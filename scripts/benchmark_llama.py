import time
import mlx.core as mx
from mlx_lm import load, generate

def benchmark_llama(model_path, prompt="Write a detailed analysis of financial compliance trends in 2024.", max_tokens=100):
    print(f"Loading model: {model_path}...")
    start_load = time.perf_counter()
    model, tokenizer = load(model_path)
    end_load = time.perf_counter()
    print(f"Model loaded in {end_load - start_load:.2f} seconds.")

    print(f"\nPrompt: {prompt}")
    print(f"Benchmarking generation of {max_tokens} tokens...\n")

    # Warmup
    _ = generate(model, tokenizer, prompt="Warmup", max_tokens=5)

    # Benchmark
    start_gen = time.perf_counter()
    response = generate(
        model, 
        tokenizer, 
        prompt=prompt, 
        max_tokens=max_tokens, 
        verbose=True # This will print tokens/sec natively in newer mlx_lm
    )
    end_gen = time.perf_counter()

    duration = end_gen - start_gen
    print(f"\nTotal generation time: {duration:.2f} seconds")

if __name__ == "__main__":
    MODEL_ID = "mlx-community/Meta-Llama-3.1-70B-Instruct-4bit"
    benchmark_llama(MODEL_ID)
