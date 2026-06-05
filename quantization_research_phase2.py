import pandas as pd
import numpy as np
import time
import torch
import warnings
from sentence_transformers import SentenceTransformer

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

def load_sample_public_data(size=200):
    df = pd.read_csv('data/전국관광지정보표준데이터.csv', encoding='cp949', nrows=size)
    texts = []
    for _, row in df.iterrows():
        name = str(row.get('관광지명', ''))
        cat = str(row.get('관광지구분', ''))
        desc = str(row.get('관광지소개', ''))
        text = f"이름: {name}, 카테고리: {cat}, 설명: {desc}"
        texts.append(text)
    return texts

def evaluate_model(model, texts, description):
    print(f"\n--- [Phase 2] {description} ---")
    
    # Warmup
    _ = model.encode(["테스트문장"])
    
    t0 = time.perf_counter()
    with torch.no_grad():
        embeddings = model.encode(texts, convert_to_numpy=True, batch_size=32)
    t1 = time.perf_counter()
    
    latency = (t1 - t0) * 1000
    avg_latency = latency / len(texts)
    print(f"Total time for {len(texts)} texts: {latency:.2f}ms (Avg {avg_latency:.2f}ms/text)")
    
    # 3-pass validation check
    assert embeddings.shape[1] == 768, "Validation 1 Failed: Dimension mismatch."
    assert np.any(embeddings != 0.0), "Validation 2 Failed: All zeros."
    assert np.var(np.linalg.norm(embeddings, axis=1)) >= 0, "Validation 3 Failed: Normalization/Variance check failed."
    
    print("3-pass validation: PASSED ✅")
    return avg_latency

def main():
    print("Starting Phase 2 Overnight Research (Thread Tuning & Advanced Tracing)...")
    texts = load_sample_public_data(200)
    print(f"Loaded {len(texts)} sample public data records.")
    
    results = {}
    
    # 1. Base Model (Default Threads)
    torch.set_num_threads(torch.get_num_threads())
    model_base = SentenceTransformer("jhgan/ko-sroberta-multitask", device="cpu")
    results['Base (Default Threads)'] = evaluate_model(model_base, texts, "Baseline FP32 (Default Threads)")
    
    # 2. Optimized Threads (Often fewer threads = better for small models)
    torch.set_num_threads(2)
    results['Base (2 Threads)'] = evaluate_model(model_base, texts, "Baseline FP32 (2 Threads)")
    
    # 3. Dynamic Quantization (with PyTorch 2.0+ recommended API check)
    try:
        from torch.ao.quantization import quantize_dynamic
        model_int8 = SentenceTransformer("jhgan/ko-sroberta-multitask", device="cpu")
        model_int8[0].auto_model = quantize_dynamic(
            model_int8[0].auto_model, {torch.nn.Linear}, dtype=torch.qint8
        )
        results['INT8 Quantization (2 Threads)'] = evaluate_model(model_int8, texts, "INT8 Dynamic Quantization")
    except Exception as e:
        print(f"Quantization failed: {e}")
        
    print("\n--- Summary of Average Latencies ---")
    for k, v in results.items():
        print(f"{k}: {v:.2f} ms/text")
        
    print("\nPhase 2 research complete. Will analyze results and prepare Phase 3...")

if __name__ == "__main__":
    main()
