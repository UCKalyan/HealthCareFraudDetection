import re
import json
import logging
import httpx
import os
from typing import Dict, Any
from src.services.action_service import ActionService

logger = logging.getLogger(__name__)

class ChatService:
    """
    Handles chat interactions for the dashboard widget.
    Supports multiple backends: Regex (Default), Gemini (Cloud), Ollama (Local).
    Now includes database query capabilities via natural language.
    """

    def __init__(self, config: Dict[str, Any], action_service: ActionService, query_service=None):
        self.config = config
        self.action_service = action_service
        self.query_service = query_service  # NEW: Database query service
        self.mode = config.get("mode", "regex")
        
        # Enhanced system prompt for LLMs with both query and action tools
        self.system_prompt = """
You are an AI Assistant for a Healthcare Fraud Detection System with access to provider, transaction, and investigation databases.

You have access to the following tools:

**QUERY TOOLS (Read-Only Database Access):**
1. get_provider_info: Get comprehensive provider details (name, specialty, risk score, status)
   - Parameters: {"tool": "get_provider_info", "npi": 1234567890}
   
2. get_provider_score: Get risk score for a specific provider
   - Parameters: {"tool": "get_provider_score", "npi": 1234567890}
   
3. get_high_risk_providers: List providers with high risk scores
   - Parameters: {"tool": "get_high_risk_providers", "threshold": 0.75, "limit": 10}
   
4. get_transactions: Get recent transactions for a provider
   - Parameters: {"tool": "get_transactions", "npi": 1234567890, "limit": 5}
   
5. get_transaction_stats: Get transaction statistics (counts, amounts by status)
   - Parameters: {"tool": "get_transaction_stats", "status": "held"}  # status can be "held", "released", "paid", or null for all
   
6. get_held_transactions: Get all transactions currently on hold
   - Parameters: {"tool": "get_held_transactions", "limit": 10}
   
7. get_investigation: Get investigation case details for a provider
   - Parameters: {"tool": "get_investigation", "npi": 1234567890}
   
8. get_system_stats: Get comprehensive system statistics
   - Parameters: {"tool": "get_system_stats"}

**ACTION TOOLS (Write Operations - Use Caution):**
9. approve_provider: Reset provider risk score to 0 and mark as verified
   - Parameters: {"tool": "approve_provider", "npi": 1234567890, "reason": "User request"}
   
10. flag_transaction: Place a payment hold on a transaction
    - Parameters: {"tool": "flag_transaction", "transaction_id": "TX-123", "reason": "User request"}

**Instructions:**
- For questions about data (scores, counts, status), use QUERY tools
- For actions (approve, flag), use ACTION tools
- Output ONLY a JSON block for tool calls
- For general conversation, respond in plain text

**Examples:**
User: "What's the risk score for NPI 1234567890?"
You: ```json
{"tool": "get_provider_score", "npi": 1234567890}
```

User: "Show last 5 transactions for that provider"
You: ```json
{"tool": "get_transactions", "npi": 1234567890, "limit": 5}
```

User: "How many transactions are on hold?"
You: ```json
{"tool": "get_transaction_stats", "status": "held"}
```

User: "Give me a system overview"
You: ```json
{"tool": "get_system_stats"}
```
"""

    async def process_message(self, message: str) -> str:
        """Process a user message and return the response."""
        logger.info(f"Processing chat message in mode: {self.mode}")
        
        if self.mode == "gemini":
            return await self._handle_gemini(message)
        elif self.mode == "ollama":
            return await self._handle_ollama(message)
        else:
            return self._handle_regex(message)

    def _handle_regex(self, message: str) -> str:
        """Default Rule-Based Logic"""
        # 1. Approve Provider
        approve_match = re.search(r"approve\s+(?:provider\s+)?(\d+)", message, re.IGNORECASE)
        if approve_match:
            npi = int(approve_match.group(1))
            result = self.action_service.approve_provider(npi, reason="User Chat Command (Regex)")
            return result["message"]
            
        # 2. Flag Transaction
        flag_match = re.search(r"flag\s+(?:transaction\s+)?([A-Za-z0-9_\-\.]+)", message, re.IGNORECASE)
        if flag_match:
            tx_id = flag_match.group(1)
            result = self.action_service.flag_transaction(tx_id, reason="User Chat Command (Regex)")
            return result["message"]
            
        return (
            "I can help you manage the system (Regex Mode).\n"
            "Try commands like:\n"
            "- 'Approve provider 1234567890'\n"
            "- 'Flag transaction TXN_12345'"
        )

    async def _handle_gemini(self, message: str) -> str:
        """Handle via Gemini API"""
        api_key = self.config.get("gemini", {}).get("api_key")
        if not api_key or api_key.startswith("$"):
            return "Error: Gemini API Key not configured."

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
        
        payload = {
            "contents": [{"parts": [{"text": self.system_prompt + "\n\nUser: " + message}]}]
        }
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, timeout=30.0)
                
            if resp.status_code != 200:
                return f"Gemini API Error: {resp.text}"
                
            data = resp.json()
            text = data['candidates'][0]['content']['parts'][0]['text']
            
            return self._parse_llm_response(text)
            
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return f"Error connecting to Gemini: {str(e)}"

    async def _handle_ollama(self, message: str) -> str:
        """Handle via Local Ollama API"""
        base_url = self.config.get("ollama", {}).get("base_url", "http://localhost:11434")
        model = self.config.get("ollama", {}).get("model", "llama3")
        
        url = f"{base_url}/api/generate"
        
        payload = {
            "model": model,
            "prompt": self.system_prompt + "\n\nUser: " + message,
            "stream": False
        }
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, timeout=60.0)
                
            if resp.status_code != 200:
                return f"Ollama API Error: {resp.text}. Is Ollama running?"
                
            data = resp.json()
            text = data.get('response', '')
            
            return self._parse_llm_response(text)
            
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return f"Error connecting to Ollama: {str(e)}"

    def _parse_llm_response(self, text: str) -> str:
        """Check for JSON tool calls in LLM output and execute them."""
        try:
            # Look for JSON block
            json_match = re.search(r"```json\s*({.*?})\s*```", text, re.DOTALL)
            if not json_match:
                json_match = re.search(r"({.*})", text, re.DOTALL) # Try finding raw JSON
                
            if json_match:
                tool_call = json.loads(json_match.group(1))
                tool_name = tool_call.get("tool")
                
                # ========================================
                # ACTION TOOLS (Write Operations)
                # ========================================
                
                if tool_name == "approve_provider":
                    result = self.action_service.approve_provider(
                        tool_call.get("npi"), 
                        tool_call.get("reason", "AI Action")
                    )
                    return f"**System Action:** {result['message']}"
                    
                elif tool_name == "flag_transaction":
                    result = self.action_service.flag_transaction(
                        tool_call.get("transaction_id"), 
                        tool_call.get("reason", "AI Action")
                    )
                    return f"**System Action:** {result['message']}"
                
                # ========================================
                # QUERY TOOLS (Read-Only Database Access)
                # ========================================
                
                elif tool_name == "get_provider_info" and self.query_service:
                    result = self.query_service.get_provider_info(tool_call.get("npi"))
                    if result["success"]:
                        return self._format_provider_info(result)
                    else:
                        return f"❌ {result['message']}"
                
                elif tool_name == "get_provider_score" and self.query_service:
                    result = self.query_service.get_provider_score(tool_call.get("npi"))
                    if result["success"]:
                        return f"**Provider NPI {result['npi']}**\n" \
                               f"- Risk Score: **{result['risk_score']:.4f}** ({result['risk_level']})\n" \
                               f"- Status: {result['status']}\n" \
                               f"- Specialty: {result['specialty']}"
                    else:
                        return f"❌ {result['message']}"
                
                elif tool_name == "get_high_risk_providers" and self.query_service:
                    threshold = tool_call.get("threshold", 0.75)
                    limit = tool_call.get("limit", 10)
                    result = self.query_service.get_high_risk_providers(threshold, limit)
                    if result["success"]:
                        return self._format_provider_list(result)
                    else:
                        return f"❌ {result['message']}"
                
                elif tool_name == "get_transactions" and self.query_service:
                    npi = tool_call.get("npi")
                    limit = tool_call.get("limit", 5)
                    result = self.query_service.get_transactions_by_npi(npi, limit)
                    if result["success"]:
                        return self._format_transactions(result)
                    else:
                        return f"❌ {result['message']}"
                
                elif tool_name == "get_transaction_stats" and self.query_service:
                    status = tool_call.get("status")
                    result = self.query_service.count_transactions_by_status(status)
                    if result["success"]:
                        return self._format_transaction_stats(result)
                    else:
                        return f"❌ {result['message']}"
                
                elif tool_name == "get_held_transactions" and self.query_service:
                    limit = tool_call.get("limit", 10)
                    result = self.query_service.get_held_transactions(limit)
                    if result["success"]:
                        return self._format_held_transactions(result)
                    else:
                        return f"❌ {result['message']}"
                
                elif tool_name == "get_investigation" and self.query_service:
                    npi = tool_call.get("npi")
                    result = self.query_service.get_case_by_npi(npi)
                    if result["success"]:
                        return self._format_investigation(result)
                    else:
                        return f"❌ {result['message']}"
                
                elif tool_name == "get_system_stats" and self.query_service:
                    result = self.query_service.get_system_summary()
                    if result["success"]:
                        return self._format_system_stats(result)
                    else:
                        return f"❌ {result['message']}"
            
            return text # Return plain text if no tool call
            
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return text + f"\n\n(Error executing action: {str(e)})"
    
    # ========================================
    # FORMATTING HELPERS
    # ========================================
    
    def _format_provider_info(self, result: Dict) -> str:
        """Format provider information for display."""
        return f"**Provider Information**\n" \
               f"- NPI: {result['npi']}\n" \
               f"- Name: {result['name']}\n" \
               f"- Specialty: {result['specialty']}\n" \
               f"- Risk Score: **{result['risk_score']:.4f}**\n" \
               f"- Status: {result['status']}\n" \
               f"- Fraud Decision: {result.get('fraud_decision', 'N/A')}"
    
    def _format_provider_list(self, result: Dict) -> str:
        """Format list of providers for display."""
        output = f"**High-Risk Providers (>{result['threshold']}):** Found {result['count']} providers\n\n"
        for i, provider in enumerate(result['providers'], 1):
            output += f"{i}. NPI {provider['npi']} - {provider['name']}\n" \
                     f"   - Risk: {provider['risk_score']:.4f} | Status: {provider['status']}\n"
        return output
    
    def _format_transactions(self, result: Dict) -> str:
        """Format transaction list for display."""
        output = f"**Transactions for NPI {result['npi']}:** (Showing {result['count']})\n\n"
        for i, tx in enumerate(result['transactions'], 1):
            output += f"{i}. {tx['transaction_id']} - ${tx['amount']:,.2f}\n" \
                     f"   - Date: {tx['date']} | Status: {tx['status']}\n"
        return output
    
    def _format_transaction_stats(self, result: Dict) -> str:
        """Format transaction statistics for display."""
        if "status" in result:
            return f"**Transactions ({result['status'].upper()}):**\n" \
                   f"- Count: {result['count']}\n" \
                   f"- Total Amount: ${result['total_amount']:,.2f}"
        else:
            output = f"**Transaction Statistics:**\n" \
                    f"- Total Transactions: {result['total_count']}\n" \
                    f"- Total Amount: ${result['total_amount']:,.2f}\n\n"
            output += "**Breakdown by Status:**\n"
            for status, data in result['by_status'].items():
                output += f"- {status}: {data['count']} (${data['total_amount']:,.2f})\n"
            return output
    
    def _format_held_transactions(self, result: Dict) -> str:
        """Format held transactions for display."""
        output = f"**Held Transactions:**\n" \
                f"- Total on Hold: {result['total_held_count']} transactions\n" \
                f"- Total Amount: ${result['total_held_amount']:,.2f}\n\n"
        output += f"**Showing Top {result['showing']}:**\n"
        for i, tx in enumerate(result['transactions'], 1):
            output += f"{i}. {tx['transaction_id']} - NPI {tx['npi']}\n" \
                     f"   - Amount: ${tx['amount']:,.2f} | Risk: {tx['fraud_risk_score']:.4f}\n"
        return output
    
    def _format_investigation(self, result: Dict) -> str:
        """Format investigation case for display."""
        return f"**Investigation Case for NPI {result['npi']}**\n" \
               f"- Case ID: {result['case_id']}\n" \
               f"- Investigation Date: {result['investigation_date']}\n" \
               f"- Status: {result['status']}\n" \
               f"- Supervisor Decision: {result['supervisor_decision']}\n\n" \
               f"*Use the Investigation Reports page for full details.*"
    
    def _format_system_stats(self, result: Dict) -> str:
        """Format system statistics for display."""
        p = result['providers']
        t = result['transactions']
        i = result['investigations']
        
        return f"**System Overview:**\n\n" \
               f"**Providers:**\n" \
               f"- Total: {p['total']:,}\n" \
               f"- High Risk (≥0.75): {p['high_risk']} ({p['high_risk_percentage']:.2f}%)\n" \
               f"- Flagged: {p['flagged']} | Verified: {p['verified']}\n" \
               f"- Avg Risk Score: {p['average_risk_score']:.4f}\n\n" \
               f"**Transactions:**\n" \
               f"- Total: {t['total_count']:,} (${t['total_amount']:,.2f})\n" \
               f"- On Hold: {t['held_count']} (${t['held_amount']:,.2f})\n\n" \
               f"**Investigations:**\n" \
               f"- Total Cases: {i['total_cases']}\n" \
               f"- Open: {i['open_cases']} | Closed: {i['closed_cases']}"

