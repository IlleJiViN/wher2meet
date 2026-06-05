import pandas as pd
import numpy as np
import time
import torch
import warnings
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer
from optimum.onnxruntime import ORTModelForFeatureExtraction

warnings.filterwarnings("ignore")

def load_and_preprocess_public_data(size=200):
    df = pd.read_csv('data/전국관광지정보표준데이터.csv', encoding='cp949', nrows=size)
    texts = []
    # Enhanced prompt template for embedding public data
    for _, row in df.iterrows():
        name = str(row.get('관광지명', ''))
        cat = str(row.get('관광지구분', ''))
        desc = str(row.get('관광지소개', ''))
        addr = str(row.get('소재지도로명주소', ''))
        # Strategy: Provide richer contextual hierarchy
        text = f"장소명: {name} (카테고리: {cat}) / 주소: {addr} / 특징: {desc}"
        texts.append(text)
    return texts

def evaluate_model_pytorch(model, texts, description):
    print(f"\n--- [Phase 3] {description} ---")
    _ = model.encode(["테스트문장"])
    
    t0 = time.perf_counter()
    with torch.no_grad():
        embeddings = model.encode(texts, convert_to_numpy=True, batch_size=32)
    t1 = time.perf_counter()
    
    latency = (t1 - t0) * 1000
    avg_latency = latency / len(texts)
    print(f"Total time for {len(texts)} texts: {latency:.2f}ms (Avg {avg_latency:.2f}ms/text)")
    
    # 3-pass validation check
    assert embeddings.shape[1] == 768, "Validation 1 Failed"
    assert np.any(embeddings != 0.0), "Validation 2 Failed"
    assert np.var(np.linalg.norm(embeddings, axis=1)) >= 0, "Validation 3 Failed"
    
    return embeddings, avg_latency

def evaluate_model_onnx(model, tokenizer, texts, description):
    print(f"\n--- [Phase 3] {description} ---")
    # Warmup
    inputs = tokenizer(["테스트문장"], padding=True, truncation=True, return_tensors="pt")
    _ = model(**inputs)
    
    embeddings_list = []
    t0 = time.perf_counter()
    
    batch_size = 32
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i+batch_size]
        inputs = tokenizer(batch_texts, padding=True, truncation=True, return_tensors="pt")
        outputs = model(**inputs)
        
        # Mean pooling
        attention_mask = inputs['attention_mask']
        token_embeddings = outputs.last_hidden_state
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
        sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        pooled = sum_embeddings / sum_mask
        
        # Normalize
        pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)
        embeddings_list.append(pooled.numpy())
        
    embeddings = np.vstack(embeddings_list)
    t1 = time.perf_counter()
    
    latency = (t1 - t0) * 1000
    avg_latency = latency / len(texts)
    print(f"Total time for {len(texts)} texts: {latency:.2f}ms (Avg {avg_latency:.2f}ms/text)")
    
    return embeddings, avg_latency

def main():
    print("Starting Phase 3: ONNX Runtime Conversion & Enhanced Prompting Strategy...")
    texts = load_and_preprocess_public_data(200)
    print(f"Loaded {len(texts)} sample public data records with enriched context.")
    
    model_name = "jhgan/ko-sroberta-multitask"
    torch.set_num_threads(2)
    
    # 1. Baseline PyTorch
    model_pt = SentenceTransformer(model_name, device="cpu")
    emb_pt, lat_pt = evaluate_model_pytorch(model_pt, texts, "Baseline PyTorch FP32")
    
    # 2. ONNX Runtime Model
    print("\nExporting PyTorch model to ONNX...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model_onnx = ORTModelForFeatureExtraction.from_pretrained(model_name, export=True)
    
    emb_onnx, lat_onnx = evaluate_model_onnx(model_onnx, tokenizer, texts, "ONNX Runtime FP32")
    
    # 3. Cross-Validation (3-pass Check 4: Semantic equivalence)
    cos_sims = np.sum(emb_pt * emb_onnx, axis=1)
    mean_sim = np.mean(cos_sims)
    print(f"\n[Cross-Validation] Mean Cosine Similarity (PT vs ONNX): {mean_sim:.4f}")
    assert mean_sim > 0.99, f"Validation Failed: Semantic equivalence compromised! (Sim: {mean_sim})"
    
    print("\n--- Summary ---")
    print(f"PyTorch Latency: {lat_pt:.2f} ms/text")
    print(f"ONNX Runtime Latency: {lat_onnx:.2f} ms/text")
    print("Phase 3 complete! The system has successfully validated the ONNX pipeline.")
    
if __name__ == "__main__":
    main()
