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
    """

    def __init__(self, config: Dict[str, Any], action_service: ActionService):
        self.config = config
        self.action_service = action_service
        self.mode = config.get("mode", "regex")
        
        # System prompt for LLMs to enforce tool usage
        self.system_prompt = """
        You are an AI Assistant for a Healthcare Fraud Detection System.
        You have access to the following tools:
        1. Approve Provider: Set a provider's risk score to 0 and status to verified.
        2. Flag Transaction: Place a payment hold on a suspicious transaction.

        If the user asks to perform an action, you MUST output a JSON block ONLY, like this:
        
        For Approval:
        ```json
        {"tool": "approve_provider", "npi": 1234567890, "reason": "User request"}
        ```
        
        For Flagging:
        ```json
        {"tool": "flag_transaction", "transaction_id": "TX-123", "reason": "User request"}
        ```

        If the user asks a general question, just answer normally in plain text.
        Do NOT output JSON for general questions.
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
        """Check for JSON tool calls in LLM output"""
        try:
            # Look for JSON block
            json_match = re.search(r"```json\s*({.*?})\s*```", text, re.DOTALL)
            if not json_match:
                json_match = re.search(r"({.*})", text, re.DOTALL) # Try finding raw JSON
                
            if json_match:
                tool_call = json.loads(json_match.group(1))
                tool_name = tool_call.get("tool")
                
                if tool_name == "approve_provider":
                    result = self.action_service.approve_provider(
                        tool_call.get("npi"), 
                        tool_call.get("reason", "AI Action")
                    )
                    return f"{text}\n\n**System Action:** {result['message']}"
                    
                elif tool_name == "flag_transaction":
                    result = self.action_service.flag_transaction(
                        tool_call.get("transaction_id"), 
                        tool_call.get("reason", "AI Action")
                    )
                    return f"{text}\n\n**System Action:** {result['message']}"
            
            return text # Return plain text if no tool call
            
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return text + f"\n\n(Error executing action: {str(e)})"
