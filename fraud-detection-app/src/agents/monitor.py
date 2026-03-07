import threading
import time
import json
import os
import sqlite3
import logging
from datetime import datetime

import httpx
import pandas as pd
from src.database import get_db_connection

logger = logging.getLogger(__name__)

STATE_FILE = "monitor_state.json"

# These defaults are overridden by config.yaml [monitor] section at runtime.
_DEFAULT_LOOP_INTERVAL   = 300    # seconds
_DEFAULT_ANALYSE_THRESH  = 0.50
_DEFAULT_CRITICAL_THRESH = 0.90
_DEFAULT_MAX_PER_CYCLE   = 20

FINANCE_API_URL = "http://localhost:8001"
FRAUD_API_URL   = "http://localhost:8000"

FEEDBACK_DB_PATH = "../shared-data/databases/feedback.db"


class MonitorAgent:
    """
    Autonomous background agent that:
      1. Continuously polls for new high-risk providers from the DB.
      2. Auto-invokes the full agentic analysis pipeline (/analyze_provider)
         for any unanalysed provider with risk_score > auto_analyse_threshold.
      3. For critical-risk providers (risk_score > critical_risk_threshold):
         - Holds PENDING payments via the Finance API.
         - Initiates RECOVERY for PROCESSED payments via the Finance API.
         - Writes each confirmed action as a 'confirm' label to feedback.db
           so incremental retraining has real labeled data.

    All thresholds and timing are read from config.yaml [monitor] section.
    """

    def __init__(self, model, scaler, feature_store, feature_cols, config: dict = None, ml_assets: dict = None):
        self.model = model
        self.scaler = scaler
        self.feature_cols = feature_cols
        # Full ml_assets dict — used by _invoke_analysis_pipeline to call
        # _run_agentic_analysis() directly (avoids the self-HTTP deadlock).
        self._ml_assets = ml_assets or {}

        # ── Read thresholds from config.yaml [monitor] ─────────────────────
        monitor_cfg = (config or {}).get("monitor", {})
        self.loop_interval   = monitor_cfg.get("loop_interval_seconds",   _DEFAULT_LOOP_INTERVAL)
        self.analyse_thresh  = monitor_cfg.get("auto_analyse_threshold",  _DEFAULT_ANALYSE_THRESH)
        self.critical_thresh = monitor_cfg.get("critical_risk_threshold", _DEFAULT_CRITICAL_THRESH)
        self.max_per_cycle   = monitor_cfg.get("max_analyse_per_cycle",   _DEFAULT_MAX_PER_CYCLE)
        # ───────────────────────────────────────────────────────────────────

        self.processed_count = 0
        self.high_risk_count = 0
        self.total_score_sum = 0.0
        self.high_risk_providers = []
        self.scanned_npis = set()
        self.actioned_npis = set()  # Track NPIs already actioned (hold/recovery)

        self.is_running = False
        self._thread = None

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM providers")
                self.total_providers = cursor.fetchone()[0]
        except Exception as e:
            logger.warning(f"MonitorAgent: failed to get total count: {e}")
            self.total_providers = 0

        self.load_state()
        logger.info("🤖 MonitorAgent initialised — continuous agentic loop ready.")

    # ── State persistence ─────────────────────────────────────────────────────

    def load_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r") as f:
                    state = json.load(f)
                self.processed_count  = state.get("processed_count", 0)
                self.high_risk_count  = state.get("high_risk_count", 0)
                self.total_score_sum  = state.get("total_score_sum", 0.0)
                self.high_risk_providers = state.get("high_risk_providers", [])
                self.scanned_npis     = set(state.get("scanned_npis", []))
                logger.info(f"MonitorAgent: state loaded — scanned {len(self.scanned_npis)}, "
                            f"high-risk {self.high_risk_count}")
            except Exception as e:
                logger.warning(f"MonitorAgent: failed to load state: {e}")

    def save_state(self):
        try:
            state = {
                "processed_count":    int(self.processed_count),
                "high_risk_count":    int(self.high_risk_count),
                "total_score_sum":    float(self.total_score_sum),
                "high_risk_providers": self.high_risk_providers,
                "scanned_npis":       [int(x) for x in self.scanned_npis],
            }
            with open(STATE_FILE, "w") as f:
                json.dump(state, f)
        except Exception as e:
            logger.warning(f"MonitorAgent: failed to save state: {e}")

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self):
        if not self.is_running:
            self.is_running = True
            self._thread = threading.Thread(
                target=self._loop, daemon=True, name="MonitorAgentLoop"
            )
            self._thread.start()
            logger.info(
                f"🤖 MonitorAgent: continuous loop started "
                f"(interval={self.loop_interval}s, "
                f"auto-analyse threshold={self.analyse_thresh}, "
                f"critical threshold={self.critical_thresh}, "
                f"max per cycle={self.max_per_cycle}) "
                f"— all values configurable via config.yaml [monitor]"
            )

    def stop(self):
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=10)

    # ── Main continuous loop ──────────────────────────────────────────────────

    def _loop(self):
        """Runs forever, waking up every loop_interval seconds."""
        while self.is_running:
            try:
                logger.info("🤖 MonitorAgent: waking up for cycle...")
                self._refresh_stats()
                self._auto_analyse_new_providers()
                self._take_autonomous_actions()
                self.save_state()
                logger.info(f"🤖 MonitorAgent: cycle complete — sleeping {self.loop_interval}s.")
            except Exception as e:
                logger.error(f"MonitorAgent: unhandled error in loop: {e}", exc_info=True)

            # Sleep in 5s chunks so stop() is responsive
            for _ in range(self.loop_interval // 5):
                if not self.is_running:
                    break
                time.sleep(5)

    # ── Cycle steps ───────────────────────────────────────────────────────────

    def _refresh_stats(self):
        """Update dashboard counters from DB."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM providers WHERE risk_score > 0.75")
                self.high_risk_count = cursor.fetchone()[0]

                cursor.execute("SELECT AVG(risk_score) FROM providers")
                avg = cursor.fetchone()[0] or 0.0
                self.total_score_sum = avg * max(self.total_providers, 1)

                cursor.execute("SELECT COUNT(*) FROM providers")
                self.total_providers = cursor.fetchone()[0]
                self.processed_count = self.total_providers

                df = pd.read_sql_query(
                    "SELECT provider_id, specialty, risk_score FROM providers "
                    "WHERE risk_score > 0.75 ORDER BY risk_score DESC LIMIT 50",
                    conn,
                )
                self.high_risk_providers = [
                    {"npi": int(r.provider_id),
                     "specialty": r.specialty,
                     "score": float(r.risk_score)}
                    for _, r in df.iterrows()
                ]
        except Exception as e:
            logger.error(f"MonitorAgent: _refresh_stats failed: {e}")

    def _auto_analyse_new_providers(self):
        """
        Find providers that:
          - Have risk_score above auto_analyse_threshold, AND
          - Have NOT yet been deep-analysed (agent_analysed_at IS NULL)
        Then invoke /analyze_provider for each in a sub-thread so the loop
        doesn't block waiting for LLM responses.
        """
        try:
            with get_db_connection() as conn:
                df = pd.read_sql_query(
                    f"""
                    SELECT provider_id, specialty, risk_score
                    FROM providers
                    WHERE risk_score > {self.analyse_thresh}
                      AND (agent_analysed_at IS NULL)
                    ORDER BY risk_score DESC
                    LIMIT {self.max_per_cycle}
                    """,
                    conn,
                )

            if df.empty:
                logger.info("MonitorAgent: no unanalysed high-risk providers found.")
                return

            logger.info(f"🤖 MonitorAgent: found {len(df)} unanalysed providers above "
                        f"threshold ({self.analyse_thresh}) — auto-analysing...")

            for _, row in df.iterrows():
                npi = str(int(row["provider_id"]))
                score = float(row["risk_score"])
                # Fire off analysis in a separate thread — don't wait for it
                t = threading.Thread(
                    target=self._invoke_analysis_pipeline,
                    args=(npi, score),
                    daemon=True,
                )
                t.start()

        except Exception as e:
            logger.error(f"MonitorAgent: _auto_analyse_new_providers failed: {e}")

    def _invoke_analysis_pipeline(self, npi: str, score: float):
        """
        Runs the agentic analysis pipeline DIRECTLY (no HTTP round-trip).

        Previously this called http://localhost:8000/analyze_provider_bg, which caused
        ConnectError when blocking ML inference in daemon threads prevented uvicorn
        from accepting new connections (self-HTTP deadlock).

        Now it calls _run_agentic_analysis() directly via a fresh asyncio event loop,
        which is safe because daemon threads each get their own loop.
        """
        try:
            logger.info(f"🤖 MonitorAgent: running direct analysis for NPI {npi} "
                        f"(risk_score={score:.4f}, reporter=skipped)...")

            # Import here to avoid circular imports at module level
            from src.routers.investigation import _run_agentic_analysis, analysis_cache
            from src.database import get_db_connection
            import pandas as pd
            import asyncio

            # Fetch provider row
            with get_db_connection() as conn:
                df = pd.read_sql_query(
                    "SELECT * FROM providers WHERE provider_id = ?", conn, params=(npi,)
                )

            if df.empty:
                logger.warning(f"MonitorAgent: NPI {npi} not found in DB — skipping.")
                self._mark_as_analysed(npi)
                return

            provider_data = df.iloc[0]

            # Run the async pipeline in a fresh event loop (safe inside a daemon thread)
            loop = asyncio.new_event_loop()
            try:
                result = loop.run_until_complete(
                    _run_agentic_analysis(
                        npi,
                        provider_data,
                        self._ml_assets,
                        skip_reporter=True,   # No LLM narrative needed for background sweep
                    )
                )
            finally:
                loop.close()

            decision = result.get("supervisorRecommendation", "N/A")
            final_score = result.get("finalScore", score)
            logger.info(
                f"✅ MonitorAgent: direct analysis complete for NPI {npi} — "
                f"score={final_score:.4f}"
            )

        except Exception as e:
            logger.error(f"MonitorAgent: _invoke_analysis_pipeline failed for {npi}: {e}")

        finally:
            # Mark as analysed regardless of outcome (avoid infinite retries)
            self._mark_as_analysed(npi)

    def _mark_as_analysed(self, npi: str):
        """Stamp agent_analysed_at so this provider isn't re-queued next cycle."""
        try:
            with get_db_connection() as conn:
                conn.execute(
                    "UPDATE providers SET agent_analysed_at = ? WHERE provider_id = ?",
                    (datetime.now().isoformat(), str(npi)),
                )
                conn.commit()
        except Exception as e:
            logger.warning(f"MonitorAgent: failed to mark {npi} as analysed: {e}")

    def _mark_autonomous_action(self, npi: int):
        """Stamp autonomous_action_at so this provider isn't re-actioned on restart."""
        try:
            with get_db_connection() as conn:
                conn.execute(
                    "UPDATE providers SET autonomous_action_at = ? WHERE provider_id = ?",
                    (datetime.now().isoformat(), str(npi)),
                )
                conn.commit()
        except Exception as e:
            logger.warning(f"MonitorAgent: failed to mark {npi} as actioned: {e}")

    def _take_autonomous_actions(self):
        """
        For providers at critical threshold:
          - Hold PENDING payments
          - Recover PROCESSED payments
          - Write each confirmed action as a 'confirm' label in feedback.db
            → enables incremental retraining on real labeled data
        """
        try:
            with get_db_connection() as conn:
                df = pd.read_sql_query(
                    f"""
                    SELECT provider_id, risk_score
                    FROM providers
                    WHERE risk_score > {self.critical_thresh}
                      AND (autonomous_action_at IS NULL)
                    ORDER BY risk_score DESC
                    LIMIT 50
                    """,
                    conn,
                )

            if df.empty:
                return

            logger.info(f"🤖 MonitorAgent: {len(df)} critical-risk providers "
                        f"(score > {self.critical_thresh}) — taking autonomous action...")

            with httpx.Client(timeout=30.0) as client:
                for _, row in df.iterrows():
                    npi   = int(row["provider_id"])
                    score = float(row["risk_score"])
                    self._act_on_provider(client, npi, score)
                    self.actioned_npis.add(npi)
                    # Persist so this NPI is skipped on future restarts
                    self._mark_autonomous_action(npi)

        except Exception as e:
            logger.error(f"MonitorAgent: _take_autonomous_actions failed: {e}")

    def _act_on_provider(self, client: httpx.Client, npi: int, score: float):
        """Hold/recover payments for one critical NPI and label it in feedback.db."""
        try:
            resp = client.get(
                f"{FINANCE_API_URL}/api/payments/search",
                params={"npi": npi, "limit": 100},
            )
            if resp.status_code != 200:
                logger.warning(f"MonitorAgent: payment search failed for {npi}: {resp.text[:200]}")
                return

            payments = resp.json().get("payments", [])
            if not payments:
                logger.info(f"MonitorAgent: no payments found for NPI {npi}.")
                return

            logger.info(f"🔎 MonitorAgent: {len(payments)} payments for NPI {npi} — processing...")
            action_taken = False

            for payment in payments:
                status = payment.get("payment_status")
                txn_id = payment.get("transaction_id")

                if status == "PENDING":
                    payload = {
                        "npi": npi,
                        "transaction_id": txn_id,
                        "fraud_score": score,
                        "confidence": 0.99,
                        "reasoning": (
                            f"AUTONOMOUS MONITOR AGENT: Critical fraud risk "
                            f"({score:.2%}) — immediate hold applied."
                        ),
                        "action": "HOLD",
                        "source": "monitor_agent",
                        "analyst": "system",
                    }
                    r = client.post(f"{FINANCE_API_URL}/api/process_payment_hold", json=payload)
                    if r.status_code == 200:
                        logger.info(f"⛔ MonitorAgent: HELD payment {txn_id} for NPI {npi}")
                        action_taken = True
                    else:
                        logger.warning(f"MonitorAgent: HOLD failed for {txn_id}: {r.text[:200]}")

                elif status == "PROCESSED":
                    payload = {
                        "transaction_id": txn_id,
                        "npi": npi,
                        "fraud_score": score,
                        "fraud_evidence": {"risk_score": score, "auto_pilot": True},
                        "initiator": "monitor_agent_autopilot",
                        "initiated_by": "system",
                    }
                    r = client.post(f"{FINANCE_API_URL}/api/initiate_recovery", json=payload)
                    if r.status_code == 200:
                        logger.info(f"↩️ MonitorAgent: RECOVERY initiated for {txn_id}, NPI {npi}")
                        action_taken = True
                    else:
                        logger.warning(f"MonitorAgent: RECOVERY failed for {txn_id}: {r.text[:200]}")

            # ── Write to feedback.db so incremental training has a label ──────
            # Always label critical-risk providers, even if payments were already
            # held (e.g. by auto-hold during ingestion).  The critical score is
            # sufficient evidence for a fraud label.
            self._write_feedback_label(npi, score)

        except httpx.ConnectError:
            logger.warning(f"MonitorAgent: cannot reach Finance API at {FINANCE_API_URL}.")
        except Exception as e:
            logger.error(f"MonitorAgent: _act_on_provider failed for {npi}: {e}")

    def _write_feedback_label(self, npi: int, score: float):
        """
        Write a 'confirm' label to feedback.db for this NPI.
        This is the bridge that makes incremental retraining possible:
        every autonomous HOLD = a high-confidence fraud label.
        """
        try:
            feedback_path = os.path.join(
                os.path.dirname(__file__), "../..", FEEDBACK_DB_PATH
            )
            feedback_path = os.path.normpath(feedback_path)

            conn = sqlite3.connect(feedback_path, timeout=15)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                """
                INSERT INTO feedback (npi, username, action, timestamp, notes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    str(npi),
                    "monitor_agent",
                    "confirm",
                    datetime.now().isoformat(),
                    f"Autonomous action — risk score {score:.4f} exceeded "
                    f"critical threshold ({self.critical_thresh})",
                ),
            )
            conn.commit()
            conn.close()
            logger.info(
                f"📝 MonitorAgent: wrote 'confirm' label for NPI {npi} "
                f"to feedback.db (score={score:.4f})"
            )
        except Exception as e:
            logger.error(f"MonitorAgent: failed to write feedback label for {npi}: {e}")

    # ── Dashboard stats ───────────────────────────────────────────────────────

    def get_stats(self):
        avg_score = (
            self.total_score_sum / self.processed_count
            if self.processed_count > 0 else 0.0
        )
        return {
            "providers_monitored": self.total_providers,
            "providers_scanned":   self.processed_count,
            "high_risk_alerts":    int(self.high_risk_count),
            "avg_fraud_score":     float(avg_score),
            "scan_progress":       (
                (self.processed_count / self.total_providers) * 100
                if self.total_providers > 0 else 0
            ),
            "recent_alerts": self.high_risk_providers[:10],
        }
