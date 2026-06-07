import sys
import torch
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.database.connection import engine
from app.services.ai_engine import init_ai_models
from app.routers import search

# Reconfigure stdout/stderr encoding for UTF-8 on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
if sys.stderr.encoding != 'utf-8':
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Thread tuning for hybrid core CPU
torch.set_num_threads(4)
torch.set_num_interop_threads(1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize AI models and cache
    model_v4, model_v5, cat_names, cat_vectors = init_ai_models()
    
    # Verify DB connection
    print(f"[STARTUP] Connecting to PostgreSQL/PostGIS DB...")
    with engine.connect() as conn:
        conn.execute(torch.text("SELECT 1") if hasattr(torch, 'text') else __import__('sqlalchemy').text("SELECT 1"))
    print("[STARTUP] PostgreSQL/PostGIS connection established successfully.")
    
    # Assign to app state
    app.state.model_v4 = model_v4
    app.state.model_v5 = model_v5
    app.state.engine = engine
    app.state.category_names = cat_names
    app.state.category_vectors = cat_vectors
    
    yield
    
    # Shutdown & memory release
    print("[SHUTDOWN] Releasing engine and clearing local model resources...")
    if hasattr(app.state, "model_v4"): del app.state.model_v4
    if hasattr(app.state, "model_v5"): del app.state.model_v5
    if hasattr(app.state, "engine"): del app.state.engine
    if hasattr(app.state, "category_vectors"): del app.state.category_vectors

    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    print("[SHUTDOWN] Shutdown routine complete.")

# Instantiate FastAPI Server
app = FastAPI(
    title="SpotSync AI Semantic Search & Recommendation Engine",
    description="v4 Decomposed Category Similarity: category-level prototype matching + name-level fine ranking. Refactored Modular Architecture.",
    version="4.1.0",
    lifespan=lifespan
)

app.include_router(search.router)
