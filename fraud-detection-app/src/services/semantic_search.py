import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)

class SemanticSearchEngine:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model_name = model_name
        self.model = None
        self.provider_embeddings = None
        self.provider_ids = None
        self.metadata = None

    def load_model(self):
        """Loads the sentence transformer model."""
        if self.model is None:
            logger.info(f"Loading Semantic Search Model: {self.model_name}")
            # Force CPU to avoid conflict with TensorFlow/Metal on macOS
            self.model = SentenceTransformer(self.model_name, device='cpu')
            logger.info("Model loaded successfully.")

    def set_data(self, df: pd.DataFrame):
        """Stores the dataframe for later indexing."""
        self.raw_df = df
        logger.info("Semantic Search data set (lazy indexing).")

    def _ensure_indexed(self):
        """Ensures the providers are indexed."""
        if self.provider_embeddings is None:
            if not hasattr(self, 'raw_df') or self.raw_df is None:
                raise RuntimeError("No data available for indexing.")
            self.index_providers(self.raw_df)

    def index_providers(self, df: pd.DataFrame):
        """
        Creates embeddings for all providers in the dataframe.
        Expects a DataFrame with columns: 'specialty', 'risk_score', 'cost_per_service', 'services_per_bene', 'Prscrbr_First_Name', 'Prscrbr_Last_Org_Name'
        """
        self.load_model()

        logger.info(f"Indexing {len(df)} providers for semantic search...")
        
        # Create textual representation for each provider
        # "Cardiology provider with High risk (Score: 0.85). Avg Cost: $150. Services/Bene: 12.5"
        descriptions = []
        for _, row in df.iterrows():
            risk_label = "High" if row.get('risk_score', 0) > 0.75 else ("Medium" if row.get('risk_score', 0) > 0.3 else "Low")
            desc = (
                f"{row.get('specialty', 'Unknown')} provider. "
                f"Risk Level: {risk_label} (Score: {row.get('risk_score', 0):.2f}). "
                f"Average Cost per Service: ${row.get('cost_per_service', 0):.2f}. "
                f"Services per Beneficiary: {row.get('services_per_bene', 0):.2f}."
            )
            descriptions.append(desc)

        # Generate embeddings
        self.provider_embeddings = self.model.encode(descriptions, show_progress_bar=True)
        # Use provider_id column if available, otherwise fallback to index
        if 'provider_id' in df.columns:
            self.provider_ids = df['provider_id'].tolist()
        else:
            self.provider_ids = df.index.tolist()
        
        # Store minimal metadata for quick retrieval
        self.metadata = df[['Prscrbr_First_Name', 'Prscrbr_Last_Org_Name', 'specialty', 'risk_score', 'cost_per_service']].to_dict('index')
        
        logger.info("Indexing complete.")

    def search(self, query: str, k: int = 5):
        """
        Searches for providers semantically similar to the query.
        Applies hybrid filtering for "High/Medium/Low Risk" queries.
        """
        self._ensure_indexed()
        
        if self.model is None:
            self.load_model()

        # Embed query
        query_embedding = self.model.encode([query])

        # Calculate similarity
        similarities = cosine_similarity(query_embedding, self.provider_embeddings)[0]

        # Hybrid Logic: Detect Risk Intent
        query_lower = query.lower()
        risk_filter = None
        
        # Explicit "risk" mention
        if "high risk" in query_lower:
            risk_filter = "high"
        elif "medium risk" in query_lower:
            risk_filter = "medium"
        elif "low risk" in query_lower:
            risk_filter = "low"
        # Implicit risk mention (e.g. "high anesthesiology") - heuristic: if "cost" is not mentioned
        elif "cost" not in query_lower:
            if "high" in query_lower:
                risk_filter = "high"
            elif "medium" in query_lower:
                risk_filter = "medium"
            elif "low" in query_lower:
                risk_filter = "low"

        # Hybrid Logic: Detect Specialty Intent
        specialty_filter = None
        if self.metadata:
            # Extract unique specialties from metadata if not already cached
            if not hasattr(self, 'known_specialties'):
                self.known_specialties = set()
                for meta in self.metadata.values():
                    spec = meta.get('specialty', '').lower()
                    if spec:
                        self.known_specialties.add(spec)
            
            # Check if query contains a known specialty
            # We sort by length descending to match longest specialty names first (e.g. "interventional cardiology" before "cardiology")
            sorted_specs = sorted(list(self.known_specialties), key=len, reverse=True)
            for spec in sorted_specs:
                if spec in query_lower:
                    specialty_filter = spec
                    break

        # Fetch more candidates to allow for filtering
        fetch_k = k * 10 if (risk_filter or specialty_filter) else k
        top_indices = np.argsort(similarities)[::-1][:fetch_k]

        results = []
        for idx in top_indices:
            npi = self.provider_ids[idx]
            score = float(similarities[idx])
            meta = self.metadata.get(idx, {}) 
            
            risk_score = float(meta.get('risk_score', 0))
            provider_specialty = meta.get('specialty', '').lower()
            
            # Apply Specialty Filter
            if specialty_filter and specialty_filter not in provider_specialty:
                continue

            # Apply Risk Filter
            if risk_filter == "high" and risk_score < 0.7:
                continue
            if risk_filter == "medium" and not (0.3 <= risk_score <= 0.7):
                continue
            if risk_filter == "low" and risk_score > 0.3:
                continue

            risk_status = "High" if risk_score > 0.75 else ("Medium" if risk_score > 0.3 else "Low")

            name = f"{meta.get('Prscrbr_First_Name', '')} {meta.get('Prscrbr_Last_Org_Name', '')}"
            if name.strip() == "0 0" or name.strip() == "0":
                name = "Unknown Provider"

            results.append({
                "npi": str(npi),
                "similarity": score,
                "name": name,
                "specialty": meta.get('specialty', 'Unknown'),
                "risk_score": risk_score,
                "risk_status": risk_status,
                "cost_per_service": float(meta.get('cost_per_service', 0))
            })
            
            if len(results) >= k:
                break

        return results
