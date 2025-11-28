from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def test_relevance():
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    query = "high risk cardiology"
    
    # Current Format
    doc_high_old = "Cardiology provider. Risk Level: High (Score: 0.85). Average Cost per Service: $150.00. Services per Beneficiary: 12.50."
    doc_low_old = "Cardiology provider. Risk Level: Low (Score: 0.10). Average Cost per Service: $50.00. Services per Beneficiary: 2.00."
    
    # Proposed Format (More distinct)
    doc_high_new = "Cardiology provider. HIGH RISK FRAUD SUSPECT. Critical Alert. Score: 0.85. Average Cost per Service: $150.00."
    doc_low_new = "Cardiology provider. Safe Low Risk Provider. Normal behavior. Score: 0.10. Average Cost per Service: $50.00."
    
    # Embed
    q_emb = model.encode([query])
    
    # Test Old
    docs_old = [doc_high_old, doc_low_old]
    emb_old = model.encode(docs_old)
    sim_old = cosine_similarity(q_emb, emb_old)[0]
    
    print(f"Query: '{query}'")
    print("\n--- Current Format ---")
    print(f"High Risk Doc: {sim_old[0]:.4f}")
    print(f"Low Risk Doc:  {sim_old[1]:.4f}")
    print(f"Delta: {sim_old[0] - sim_old[1]:.4f}")
    
    # Test New
    docs_new = [doc_high_new, doc_low_new]
    emb_new = model.encode(docs_new)
    sim_new = cosine_similarity(q_emb, emb_new)[0]
    
    print("\n--- New Format ---")
    print(f"High Risk Doc: {sim_new[0]:.4f}")
    print(f"Low Risk Doc:  {sim_new[1]:.4f}")
    print(f"Delta: {sim_new[0] - sim_new[1]:.4f}")

if __name__ == "__main__":
    test_relevance()
