import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from src.dependencies import get_ml_assets

# Configure Logging
logger = logging.getLogger(__name__)

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    k: int = 5

@router.post("/search_providers")
async def search_providers(request: SearchRequest, ml_assets: dict = Depends(get_ml_assets)):
    """
    Semantically searches for providers based on a text query.
    """
    query = request.query
    logger.info(f"Received semantic search query: '{query}'")
    
    search_engine = ml_assets.get('search_engine')
    if not search_engine:
        raise HTTPException(status_code=503, detail="Semantic search engine not initialized.")
    
    try:
        results = search_engine.search(query, k=request.k)
        return {"results": results}
    except Exception as e:
        logger.error(f"Error during semantic search: {e}")
        raise HTTPException(status_code=500, detail=str(e))
