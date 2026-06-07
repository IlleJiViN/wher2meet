import time
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from typing import Tuple, List

from categories import CATEGORY_DESCRIPTIONS

MODEL_NAME = "jhgan/ko-sroberta-multitask"
DEVICE = "cpu"

def init_ai_models() -> Tuple[SentenceTransformer, SentenceTransformer, List[str], np.ndarray]:
    """
    Initializes SentenceTransformer models and pre-caches category prototype vectors.
    Returns (model_v4, model_v5, category_names, category_vectors).
    """
    print(f"[STARTUP] Initializing SpotSync AI (Decomposed Category Similarity)...")
    start_time = time.perf_counter()

    # Load SentenceTransformer on CPU (v4 and v5)
    model_v4 = SentenceTransformer(MODEL_NAME, device=DEVICE)

    print("[STARTUP] Applying INT8 Dynamic Quantization (v5) for CPU acceleration...")
    model_v5 = SentenceTransformer(MODEL_NAME, device=DEVICE)
    model_v5[0].auto_model = torch.quantization.quantize_dynamic(
        model_v5[0].auto_model, {torch.nn.Linear}, dtype=torch.qint8
    )
    
    # Warm up models
    _ = model_v4.encode("웜업", convert_to_numpy=True)
    _ = model_v5.encode("웜업", convert_to_numpy=True)
    
    # Pre-cache category prototype vectors
    print(f"[STARTUP] Encoding {len(CATEGORY_DESCRIPTIONS)} category prototypes...")
    category_names = list(CATEGORY_DESCRIPTIONS.keys())
    category_texts = list(CATEGORY_DESCRIPTIONS.values())
    
    with torch.no_grad():
        category_vectors = model_v4.encode(
            category_texts,
            convert_to_numpy=True,
            normalize_embeddings=True
        ).astype('float32')  # Shape: (num_categories, 768)
    
    print(f"[STARTUP] Category prototype matrix cached: {category_vectors.shape}")
    
    duration = (time.perf_counter() - start_time) * 1000
    print(f"[STARTUP] AI models initialized in {duration:.2f}ms.")
    
    return model_v4, model_v5, category_names, category_vectors
