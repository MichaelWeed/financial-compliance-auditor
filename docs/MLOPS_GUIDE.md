# MLOps Guide: Extending & Scaling the Inference Layer

> **Audience**: Platform engineers, ML/AI teams, and developers who want to adapt the Financial Compliance Auditor to use different models, remote inference endpoints, or distributed architectures.

---

## Overview

Out of the box, this system runs entirely locally on Apple Silicon via MLX. But the architecture is designed to be **inference-agnostic**—the agent layer talks to an OpenAI-compatible API endpoint, not directly to a specific model runtime.

This guide covers:

1. How the inference layer works today
2. Swapping in different local models
3. Pointing to remote/cloud inference
4. Scaling patterns for enterprise deployment

---

## 1. Understanding the Current Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Query                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   LangGraph Agent (agent.py)                    │
│          Retrieve → Grade → Reflect → Generate                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 ChatOpenAI Client (LangChain)                   │
│        openai_api_base = "http://localhost:8080/v1"             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              MLX LM Server (mlx_lm.server)                      │
│           OpenAI-compatible /v1/chat/completions                │
└─────────────────────────────────────────────────────────────────┘
```

**Key Insight**: The agent doesn't care what's behind the `/v1/chat/completions` endpoint. It just needs an OpenAI-compatible response format.

---

## 2. Swapping Local Models

### Changing the MLX Model

The default model is `mlx-community/Qwen2.5-72B-Instruct-4bit`. To use a different model:

```bash
# Stop the current server, then:
mlx_lm.server --model mlx-community/Llama-3.3-70B-Instruct-4bit
```

Update `agent.py` to reflect the model name (optional, for logging purposes):

```python
# agent.py, line ~28
LLM_MODEL = "mlx-community/Llama-3.3-70B-Instruct-4bit"
```

### Model Selection Criteria

| Model                       | Size | Memory Required | Use Case                             |
| :-------------------------- | :--- | :-------------- | :----------------------------------- |
| Qwen2.5-7B-Instruct-4bit    | 7B   | ~8GB            | Fast iteration, light audits         |
| Qwen2.5-32B-Instruct-4bit   | 32B  | ~24GB           | Balanced performance                 |
| Qwen2.5-72B-Instruct-4bit   | 72B  | ~48GB           | Production audits, complex reasoning |
| Llama-3.3-70B-Instruct-4bit | 70B  | ~48GB           | Alternative reasoning style          |

**Tip**: For financial document analysis, larger models significantly outperform smaller ones on table comprehension and multi-hop reasoning.

---

## 3. Remote Inference Endpoints

### Option A: Self-Hosted vLLM / TGI Server

If you have a GPU server (NVIDIA A100, H100, etc.), you can run inference there and point the agent to it.

**On the GPU Server:**

```bash
# Using vLLM (recommended for throughput)
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-72B-Instruct \
    --host 0.0.0.0 \
    --port 8080 \
    --tensor-parallel-size 2  # For multi-GPU
```

**On the Client (Mac):**

```python
# agent.py
BASE_URL = "http://your-gpu-server.internal:8080/v1"
```

### Option B: Cloud Provider APIs

The system can directly use cloud-hosted models with minimal changes.

**OpenAI / Azure OpenAI:**

```python
# agent.py
from langchain_openai import ChatOpenAI

self.llm = ChatOpenAI(
    model="gpt-4-turbo",
    openai_api_key=os.environ["OPENAI_API_KEY"],
    # Remove openai_api_base to use default OpenAI endpoint
)
```

**AWS Bedrock:**

```python
from langchain_aws import ChatBedrock

self.llm = ChatBedrock(
    model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
    region_name="us-east-1"
)
```

**Anthropic Direct:**

```python
from langchain_anthropic import ChatAnthropic

self.llm = ChatAnthropic(
    model="claude-3-5-sonnet-20241022",
    anthropic_api_key=os.environ["ANTHROPIC_API_KEY"]
)
```

> ⚠️ **Sovereignty Warning**: Using cloud APIs means your financial documents leave your infrastructure. This may violate data governance policies. Consider this carefully.

---

## 4. Hybrid Architecture: Local Embeddings + Remote Reasoning

A common pattern for enterprises is to keep **embeddings local** (for privacy during retrieval) while routing **generation** to a more powerful remote model.

```
┌──────────────────┐    ┌──────────────────┐
│  Local Machine   │    │   GPU Cluster    │
│                  │    │                  │
│  ┌────────────┐  │    │  ┌────────────┐  │
│  │ LanceDB    │  │    │  │ vLLM/TGI   │  │
│  │ (Vectors)  │  │    │  │ (Qwen 72B) │  │
│  └────────────┘  │    │  └────────────┘  │
│        │         │    │        ▲         │
│        ▼         │    │        │         │
│  ┌────────────┐  │    │        │         │
│  │ Sentence   │  │────┼────────┘         │
│  │ Transformer│  │    │ (HTTPS/gRPC)     │
│  └────────────┘  │    │                  │
└──────────────────┘    └──────────────────┘
```

**How to implement:**

1. Keep `ingest.py` and `database.py` unchanged (embeddings stay local)
2. Modify only `agent.py` to point `BASE_URL` to your remote cluster
3. Ensure the network path between client and server is encrypted (TLS)

---

## 5. Load Balancing for Multi-User Deployments

For teams where multiple analysts need concurrent access:

### Pattern: Reverse Proxy with Model Pool

```
                    ┌─────────────────┐
                    │   Nginx/Caddy   │
                    │  (Load Balancer)│
                    └────────┬────────┘
           ┌─────────────────┼─────────────────┐
           ▼                 ▼                 ▼
    ┌────────────┐    ┌────────────┐    ┌────────────┐
    │ GPU Node 1 │    │ GPU Node 2 │    │ GPU Node 3 │
    │ (vLLM)     │    │ (vLLM)     │    │ (vLLM)     │
    └────────────┘    └────────────┘    └────────────┘
```

**Nginx config snippet:**

```nginx
upstream inference_pool {
    least_conn;
    server gpu-node-1:8080;
    server gpu-node-2:8080;
    server gpu-node-3:8080;
}

server {
    listen 8080;
    location /v1/ {
        proxy_pass http://inference_pool;
    }
}
```

---

## 6. Environment Variables for Flexibility

To avoid hardcoding endpoints, use environment variables:

```python
# agent.py - modified initialization
import os

BASE_URL = os.environ.get("AUDITOR_LLM_ENDPOINT", "http://localhost:8080/v1")
LLM_MODEL = os.environ.get("AUDITOR_LLM_MODEL", "mlx-community/Qwen2.5-72B-Instruct-4bit")
API_KEY = os.environ.get("AUDITOR_LLM_API_KEY", "not-needed")

self.llm = ChatOpenAI(
    model=LLM_MODEL,
    openai_api_base=BASE_URL,
    openai_api_key=API_KEY,
    temperature=0.1  # Low temp for deterministic audit outputs
)
```

**Launch with custom endpoint:**

```bash
AUDITOR_LLM_ENDPOINT="https://inference.internal.corp/v1" \
AUDITOR_LLM_API_KEY="sk-xxx" \
streamlit run app.py
```

---

## 7. Model-Specific Prompt Tuning

Different models have different strengths. You may need to adjust the system prompts in `agent.py`:

| Model Family | Consideration                                                                    |
| :----------- | :------------------------------------------------------------------------------- |
| **Qwen**     | Strong at structured output, good with Chinese financial terms if needed         |
| **Llama**    | May need more explicit citation formatting instructions                          |
| **Claude**   | Excellent at nuanced reasoning, but may over-explain; reduce verbosity in prompt |
| **GPT-4**    | Very reliable at formatting, but watch token costs                               |

The key prompts to modify are in `AuditorAgent.generate()` and `AuditorAgent.grade_documents()`.

---

## 8. Monitoring & Observability

For production deployments, add instrumentation:

### LangSmith Integration

```python
# At top of agent.py
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "your-langsmith-key"
os.environ["LANGCHAIN_PROJECT"] = "financial-compliance-auditor"
```

### Custom Logging

The system already logs to `logs/agent_log.txt`. For structured logging:

```python
import json
import logging

logging.basicConfig(
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}',
    level=logging.INFO
)
```

---

## 9. Quick Reference: Configuration Files

| File          | Purpose               | Key Variables                |
| :------------ | :-------------------- | :--------------------------- |
| `agent.py`    | LLM endpoint config   | `BASE_URL`, `LLM_MODEL`      |
| `database.py` | Embedding model       | `SentenceTransformer(...)`   |
| `ingest.py`   | PDF parsing strategy  | `strategy="hi_res"`          |
| `launch.sh`   | Startup orchestration | Port numbers, conda env name |

---

## 10. Future Considerations

### Streaming Responses

The current implementation waits for full generation. For a better UX with large responses, implement streaming:

```python
# Requires refactoring app.py to use st.write_stream()
for chunk in self.llm.stream(messages):
    yield chunk.content
```

### Multi-Modal (Vision) Models

SEC filings increasingly include charts and infographics. Future versions could use vision-capable models (GPT-4V, Claude 3.5, Qwen-VL) to analyze embedded images.

### Fine-Tuning

For domain-specific accuracy, consider fine-tuning on a corpus of annotated audit reports. Tools like Axolotl + QLoRA make this accessible even on consumer hardware.

---

## Contributing

If you extend this system in interesting ways—particularly for enterprise patterns—consider contributing back. Open an issue or PR on the [GitHub repo](https://github.com/MichaelWeed/financial-compliance-auditor).
