
import sys
import os
import pandas as pd
import logging

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.semantic_search import SemanticSearchEngine

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reproduce_issue():
    # Initialize engine
    engine = SemanticSearchEngine()
    
    # Load data (mock or real?)
    # Let's try to load from the real DB if possible, or create a mock df that mimics the user's data
    # The user has real data in data/providers.db
    
    from src.database import get_db_connection
    try:
        with get_db_connection() as conn:
            df = pd.read_sql_query("SELECT * FROM providers LIMIT 1000", conn)
            # Ensure we have enough data to reproduce
            logger.info(f"Loaded {len(df)} providers from DB.")
    except Exception as e:
        logger.error(f"Failed to load from DB: {e}")
        return

    engine.set_data(df)
    
    # Query
    query = "high risk cardiology"
    logger.info(f"Searching for: '{query}'")
    
    results = engine.search(query, k=20)
    
    print(f"\nResults for '{query}':")
    print(f"{'NPI':<12} | {'Specialty':<30} | {'Risk':<10} | {'Score':<6} | {'Name'}")
    print("-" * 80)
    for r in results:
        print(f"{r['npi']:<12} | {r['specialty']:<30} | {r['risk_status']:<10} | {r['similarity']:.4f} | {r['name']}")

if __name__ == "__main__":
    reproduce_issue()
