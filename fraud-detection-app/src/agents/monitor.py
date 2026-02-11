import threading
import time
import numpy as np
import pandas as pd
import json
import os
from src.database import get_db_connection

import httpx

STATE_FILE = "monitor_state.json"
CRITICAL_RISK_THRESHOLD = 0.9
FINANCE_API_URL = "http://localhost:8001"

class MonitorAgent:
    def __init__(self, model, scaler, feature_store, feature_cols):
        # feature_store is now None, we use DB
        self.model = model
        self.scaler = scaler
        self.feature_cols = feature_cols
        
        self.processed_count = 0
        self.high_risk_count = 0
        self.total_score_sum = 0.0
        self.high_risk_providers = [] # Store details of high risk providers
        self.scanned_npis = set()
        
        self.is_running = False
        self._thread = None
        
        # Get total providers from DB
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM providers")
                self.total_providers = cursor.fetchone()[0]
        except Exception as e:
            print(f"Agent: Monitor failed to get total count: {e}")
            self.total_providers = 0
        
        self.load_state()

    def load_state(self):
        """Loads the scan state from a JSON file."""
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r') as f:
                    state = json.load(f)
                    self.processed_count = state.get('processed_count', 0)
                    self.high_risk_count = state.get('high_risk_count', 0)
                    self.total_score_sum = state.get('total_score_sum', 0.0)
                    self.high_risk_providers = state.get('high_risk_providers', [])
                    self.scanned_npis = set(state.get('scanned_npis', []))
                
                print(f"Agent: Monitor loaded state. Scanned: {len(self.scanned_npis)}, High Risk: {self.high_risk_count}")
            except Exception as e:
                print(f"Agent: Monitor failed to load state: {e}")

    def save_state(self):
        """Saves the current scan state to a JSON file."""
        try:
            state = {
                'processed_count': int(self.processed_count),
                'high_risk_count': int(self.high_risk_count),
                'total_score_sum': float(self.total_score_sum),
                'high_risk_providers': self.high_risk_providers,
                'scanned_npis': [int(x) for x in self.scanned_npis]
            }
            with open(STATE_FILE, 'w') as f:
                json.dump(state, f)
        except Exception as e:
            print(f"Agent: Monitor failed to save state: {e}")

    def start(self):
        """Starts the background monitoring process."""
        if not self.is_running:
            self.is_running = True
            self._thread = threading.Thread(target=self._process_data, daemon=True)
            self._thread.start()
            print("Agent: Monitor started background scanning...")

    def stop(self):
        """Stops the background process."""
        self.is_running = False
        if self._thread:
            self._thread.join()

    def take_autonomous_action(self, npi, score):
        """
        Autonomously holds payments or initiates recovery for critical risk providers.
        """
        if score < CRITICAL_RISK_THRESHOLD:
            return

        print(f"🤖 Agent: Monitor taking AUTONOMOUS ACTION for NPI {npi} (Score: {score:.4f})")
        
        try:
            # 1. Search for payments
            with httpx.Client(timeout=30.0) as client:
                try:
                    response = client.get(f"{FINANCE_API_URL}/api/payments/search", params={"npi": npi, "limit": 100})
                    if response.status_code != 200:
                        print(f"⚠️ Agent: Monitor failed to fetch payments for {npi}: {response.text}")
                        return
                    
                    data = response.json()
                    payments = data.get("payments", [])
                    
                    if not payments:
                        print(f"ℹ️ Agent: Monitor found no payments for {npi} to act on.")
                        return

                    print(f"🔎 Agent: Monitor found {len(payments)} payments for {npi}. Analyzing...")

                    for payment in payments:
                        status = payment.get("payment_status")
                        txn_id = payment.get("transaction_id")
                        
                        # ACTION 1: HOLD PENDING PAYMENTS
                        if status == "PENDING":
                            print(f"⛔ Agent: Monitor HOLDING payment {txn_id}...")
                            hold_payload = {
                                "npi": npi,
                                "transaction_id": txn_id,
                                "fraud_score": score,
                                "confidence": 0.99,
                                "reasoning": f"AUTONOMOUS AGENT: Critical Fraud Risk ({score:.2%}) detected. Immediate hold applied.",
                                "action": "HOLD"
                            }
                            resp = client.post(f"{FINANCE_API_URL}/api/process_payment_hold", json=hold_payload)
                            if resp.status_code == 200:
                                print(f"✅ Agent: Monitor successfully HELD payment {txn_id}")
                            else:
                                print(f"❌ Agent: Monitor failed to HOLD payment {txn_id}: {resp.text}")

                        # ACTION 2: RECOVER PROCESSED PAYMENTS
                        elif status == "PROCESSED":
                            print(f"↩️ Agent: Monitor INITIATING RECOVERY for {txn_id}...")
                            recovery_payload = {
                                "transaction_id": txn_id,
                                "npi": npi,
                                "fraud_score": score,
                                "fraud_evidence": {"risk_score": score, "auto_pilot": True},
                                "initiator": "monitor_agent_autopilot",
                                "initiated_by": "system"
                            }
                            resp = client.post(f"{FINANCE_API_URL}/api/initiate_recovery", json=recovery_payload)
                            if resp.status_code == 200:
                                print(f"✅ Agent: Monitor successfully INITIATED RECOVERY for {txn_id}")
                            else:
                                # It might fail if already recovered, which is fine
                                print(f"⚠️ Agent: Monitor recovery response for {txn_id}: {resp.text}")
                except httpx.ConnectError:
                     print(f"⚠️ Agent: Monitor cannot connect to Finance App at {FINANCE_API_URL}. Is it running?")

        except Exception as e:
            print(f"❌ Agent: Monitor autonomous action failed: {e}")

    def _process_data(self):
        """Iterates through the database to update stats."""
        # Since we pre-calculated risk scores, we can just query the DB for high risk items
        # and simulate "scanning" or just load them.
        
        try:
            with get_db_connection() as conn:
                # 1. Update High Risk Count
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM providers WHERE risk_score > 0.75")
                self.high_risk_count = cursor.fetchone()[0]
                
                # 2. Update Avg Score
                cursor.execute("SELECT AVG(risk_score) FROM providers")
                result = cursor.fetchone()[0]
                avg_score = result if result else 0.0
                self.total_score_sum = avg_score * self.total_providers # Approx
                
                # 3. Get Recent High Risk Providers
                df = pd.read_sql_query("SELECT * FROM providers WHERE risk_score > 0.75 ORDER BY risk_score DESC LIMIT 50", conn)
                
                self.high_risk_providers = []
                for _, row in df.iterrows():
                    npi = int(row['provider_id'])
                    score = float(row['risk_score'])
                    
                    self.high_risk_providers.append({
                        "npi": npi,
                        "specialty": row['specialty'],
                        "score": score
                    })
                    
                    # --- AUTO-PILOT ACTION ---
                    # Check if we should take autonomous action
                    self.take_autonomous_action(npi, score)
                    # -------------------------
                    
                # 4. Mark all as scanned (since we did it in migration)
                self.processed_count = self.total_providers
                
            print(f"Agent: Monitor refreshed stats from DB. High Risk: {self.high_risk_count}")
            self.save_state()
            
        except Exception as e:
            print(f"Agent: Monitor error in background process: {e}")
            
        self.is_running = False

    def get_stats(self):
        """Returns the current live statistics."""
        avg_score = (self.total_score_sum / self.processed_count) if self.processed_count > 0 else 0.0
        
        return {
            "providers_monitored": self.total_providers,
            "providers_scanned": self.processed_count,
            "high_risk_alerts": int(self.high_risk_count),
            "avg_fraud_score": float(avg_score),
            "scan_progress": (self.processed_count / self.total_providers) * 100 if self.total_providers > 0 else 0,
            "recent_alerts": self.high_risk_providers[:10] # Return top 10 for dashboard
        }
