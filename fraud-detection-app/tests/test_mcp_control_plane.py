import sys
import os
import sqlite3
import logging

# Add parent directory to path to import mcp_server
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set Environment Variables for Config Loader
os.environ['FEATURE_STORE_PATH'] = 'data/processed/provider_features.csv'
os.environ['MODEL_PATH'] = 'models/fraud_detection_model.keras'
os.environ['SCALER_PATH'] = 'models/robust_scaler.joblib'
os.environ['FEATURE_COLUMNS_PATH'] = 'models/specialty_stats.json' # Just in case

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("MCP_Test")

def test_approve_provider():
    logger.info("\n--- Testing approve_provider ---")
    
    # 1. Pick a provider
    db_path = "../shared-data/databases/providers.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Find a provider with non-zero risk score
    cursor.execute("SELECT provider_id, risk_score, status FROM providers WHERE risk_score > 0 LIMIT 1")
    row = cursor.fetchone()
    
    if not row:
        logger.warning("No high-risk providers found to test approval.")
        conn.close()
        return

    npi, old_score, old_status = row
    logger.info(f"Target Provider: {npi} (Score: {old_score}, Status: {old_status})")
    conn.close()

    # 2. Call the tool
    try:
        from mcp_server import approve_provider
        result = approve_provider(npi, "Test Approval via Script")
        logger.info(f"Tool Output: {result}")
    except ImportError:
        logger.error("Failed to import mcp_server. Make sure you are running this from fraud-detection-app directory.")
        return
    except Exception as e:
        logger.error(f"Tool Execution Error: {e}")
        return

    # 3. Verify
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT risk_score, status FROM providers WHERE provider_id = ?", (npi,))
    new_score, new_status = cursor.fetchone()
    conn.close()

    if new_score == 0.0 and new_status == 'verified':
        logger.info("✅ SUCCESS: Provider approved and verified.")
    else:
        logger.error(f"❌ FAILURE: Provider state mismatch. Score: {new_score}, Status: {new_status}")

def test_flag_transaction():
    logger.info("\n--- Testing flag_transaction ---")
    
    # 1. Pick a transaction
    db_path = "../shared-data/databases/finance.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Find a PENDING transaction to flag
    cursor.execute("SELECT transaction_id, payment_status FROM payment_transactions WHERE payment_status = 'PENDING' LIMIT 1")
    row = cursor.fetchone()
    
    if not row:
        logger.warning("No PENDING transactions found to test flagging. Creating one...")
        # Create a dummy pending transaction for testing
        import uuid
        dummy_tx = str(uuid.uuid4())
        # Need an NPI
        cursor.execute("SELECT npi FROM payment_transactions LIMIT 1")
        npi = cursor.fetchone()[0]
        cursor.execute("INSERT INTO payment_transactions (transaction_id, npi, payment_status, payment_amount, created_at) VALUES (?, ?, 'PENDING', 100.0, datetime('now'))", (dummy_tx, npi))
        conn.commit()
        tx_id = dummy_tx
        old_status = 'PENDING'
    else:
        tx_id, old_status = row
    logger.info(f"Target Transaction: {tx_id} (Status: {old_status})")
    conn.close()

    # 2. Call the tool
    try:
        from mcp_server import flag_transaction
        result = flag_transaction(tx_id, "Test Flag via Script")
        logger.info(f"Tool Output: {result}")
    except Exception as e:
        logger.error(f"Tool Execution Error: {e}")
        return

    # 3. Verify
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT payment_status FROM payment_transactions WHERE transaction_id = ?", (tx_id,))
    new_status = cursor.fetchone()[0]
    conn.close()

    if new_status == 'HOLD':
        logger.info("✅ SUCCESS: Transaction placed on HOLD.")
    else:
        logger.error(f"❌ FAILURE: Transaction status is {new_status}, expected HOLD.")

if __name__ == "__main__":
    print("Starting MCP Control Plane Tests...")
    test_approve_provider()
    test_flag_transaction()
    print("\nTests Complete.")
