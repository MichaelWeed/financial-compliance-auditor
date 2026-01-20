"""
Benchmark script for Qwen 2.5 72B via LM Studio's OpenAI-compatible API.
Ensure LM Studio is running with the model loaded before executing.
"""
import time
import requests

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"

def benchmark_inference(prompt: str, max_tokens: int = 100) -> dict:
    """Send a request to LM Studio and measure throughput."""
    
    payload = {
        "model": "qwen2.5-72b-ablit-v2-q8",  # LM Studio uses the folder name
        "messages": [
            {"role": "system", "content": "You are a financial compliance auditor."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "stream": False
    }
    
    print(f"Prompt: {prompt}")
    print(f"Requesting {max_tokens} tokens...\n")
    
    start = time.perf_counter()
    response = requests.post(LM_STUDIO_URL, json=payload, timeout=300)
    end = time.perf_counter()
    
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        return {}
    
    data = response.json()
    duration = end - start
    
    # Extract usage info
    usage = data.get("usage", {})
    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)
    total_tokens = usage.get("total_tokens", 0)
    
    # Calculate throughput
    tokens_per_second = completion_tokens / duration if duration > 0 else 0
    
    print("=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)
    print(f"Model: Qwen 2.5 72B (Q8)")
    print(f"Prompt tokens: {prompt_tokens}")
    print(f"Completion tokens: {completion_tokens}")
    print(f"Total time: {duration:.2f} seconds")
    print(f"Throughput: {tokens_per_second:.2f} tokens/sec")
    print("=" * 60)
    print(f"\nResponse:\n{data['choices'][0]['message']['content']}")
    
    return {
        "tokens_per_second": tokens_per_second,
        "completion_tokens": completion_tokens,
        "duration": duration
    }

def check_lm_studio_status():
    """Check if LM Studio server is running."""
    try:
        response = requests.get("http://localhost:1234/v1/models", timeout=5)
        if response.status_code == 200:
            models = response.json().get("data", [])
            print("LM Studio is running!")
            print(f"Available models: {[m['id'] for m in models]}\n")
            return True
    except requests.exceptions.ConnectionError:
        print("ERROR: LM Studio server is not running.")
        print("Please start LM Studio and load your Qwen 2.5 72B model.")
        print("Then enable the local server (Developer > Local Server).")
        return False

if __name__ == "__main__":
    if check_lm_studio_status():
        benchmark_inference(
            prompt="List three key challenges in financial audit automation and explain each briefly.",
            max_tokens=200
        )
