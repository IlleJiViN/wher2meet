import sys
content = open("/home/dev/AI/test/ai_search.py").read()

# 1. Update SearchRequest
old_req = """    top_k: int = Field(
        default=3,
        ge=1,
        le=50,
        description="The number of matched locations to return."
    )"""
new_req = """    top_k: int = Field(
        default=3,
        ge=1,
        le=50,
        description="The number of matched locations to return."
    )
    engine_version: str = Field(
        default="v5",
        description="AI engine version to use (v4, v5)"
    )"""
content = content.replace(old_req, new_req)

# 2. Update lifespan
old_lifespan = """        # Step 1: Load SentenceTransformer on CPU
        model = SentenceTransformer(MODEL_NAME, device=DEVICE)

        # Apply INT8 Dynamic Quantization (v5)
        import torch
        print("[STARTUP] Applying INT8 Dynamic Quantization (v5) for CPU acceleration...")
        model[0].auto_model = torch.quantization.quantize_dynamic(
            model[0].auto_model, {torch.nn.Linear}, dtype=torch.qint8
        )
        
        # Warm up model to cache torch variables
        _ = model.encode("웜업", convert_to_numpy=True)
        
        # Step 2: Pre-cache category prototype vectors"""
new_lifespan = """        # Step 1: Load SentenceTransformer on CPU (v4 and v5)
        model_v4 = SentenceTransformer(MODEL_NAME, device=DEVICE)

        import torch
        print("[STARTUP] Applying INT8 Dynamic Quantization (v5) for CPU acceleration...")
        model_v5 = SentenceTransformer(MODEL_NAME, device=DEVICE)
        model_v5[0].auto_model = torch.quantization.quantize_dynamic(
            model_v5[0].auto_model, {torch.nn.Linear}, dtype=torch.qint8
        )
        
        # Warm up models
        _ = model_v4.encode("웜업", convert_to_numpy=True)
        _ = model_v5.encode("웜업", convert_to_numpy=True)
        
        # Step 2: Pre-cache category prototype vectors (using v4 as baseline)"""
content = content.replace(old_lifespan, new_lifespan)

# Update state assignment
old_state = "app.state.model = model"
new_state = "app.state.model_v4 = model_v4\n        app.state.model_v5 = model_v5"
content = content.replace(old_state, new_state)

# Replace category encoding with model_v4
content = content.replace("category_vectors = model.encode(", "category_vectors = model_v4.encode(")

# 3. Update search endpoint
old_search = "    model: SentenceTransformer = request.app.state.model"
new_search = "    model: SentenceTransformer = request.app.state.model_v5 if body.engine_version == 'v5' else request.app.state.model_v4"
content = content.replace(old_search, new_search)

open("/home/dev/AI/test/ai_search.py", "w").write(content)
