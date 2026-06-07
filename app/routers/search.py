from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from sentence_transformers import SentenceTransformer

from app.models.schemas import SearchRequest, SearchResponse
from app.services.search_service import execute_search

router = APIRouter()

@router.post(
    "/search",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic Location Search",
    description="Hybrid Search pipeline combining vector similarity, synonyms, and postgis distance."
)
async def semantic_search(request: Request, body: SearchRequest):
    model: SentenceTransformer = request.app.state.model_v5 if body.engine_version == 'v5' else request.app.state.model_v4
    engine = getattr(request.app.state, "engine", None)
    category_names = getattr(request.app.state, "category_names", [])
    category_vectors = getattr(request.app.state, "category_vectors", None)
    
    if not model or not engine or category_vectors is None:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "PostGIS connection or AI Model is not initialized."}
        )
        
    try:
        response = execute_search(body, model, engine, category_names, category_vectors)
        return response
    except ValueError as ve:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(ve)}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Search execution failure: {str(e)}"}
        )
