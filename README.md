# 🏛️ Financial Compliance Auditor: Sovereign Visual RAG

> **Precision Document Intelligence for Institutional Financial Audit.**

## 📊 Executive Summary (The Problem & The Solution)

**The Problem**: Traditional Large Language Models (LLMs) are "probabilistic"—they often hallucinate or provide information without verifiable provenance. In financial auditing, where a single inaccuracy carries multi-million dollar liability, "vibes-based" AI is unacceptable.

**The Solution**: This project is a **Sovereign Visual RAG** system built for high-stakes corporate auditing. It doesn't just answer questions; it provides **Financial Substantiation**. Using a custom-built Agentic Reasoning chain, every single claim made by the AI is mapped back to **exact pixel-perfect coordinates** on the original SEC 10-K filing.

**Value Proposition**:

- **0% Pure Speculation**: An agentic reflecting loop (LangGraph) grades retrieved evidence before synthesizing an answer.
- **Sovereign & Air-Gapped**: Runs entirely locally on Apple Silicon (MLX), ensuring sensitive financial data never leaves your infrastructure.
- **Visual Grounding**: Citations link directly to a PDF viewer with bounding-box highlights, creating an unshakeable audit trail.
- **White-Glove Onboarding**: Guided first-run experience for portfolio reviewers and analysts.
- **Graceful Control**: Dedicated system shutdown to avoid macOS crash reports and ensure clean exits.

[![Financial Compliance Auditor Demo](https://img.youtube.com/vi/OssO9q74d7c/maxresdefault.jpg)](https://youtu.be/OssO9q74d7c)

_Watch the full demo: Click above to see the Financial Compliance Auditor in action._

---

## 🗺️ Navigation: Choose Your Persona

| I am a...                     | My Goal                                             | Destination                                       |
| :---------------------------- | :-------------------------------------------------- | :------------------------------------------------ |
| **Hiring Manager / HR**       | Understand the value and project scope.             | Continue reading this README.                     |
| **Technical Architect / CTO** | Review the system design, schemas, and logic.       | ⮕ **[System Architecture](docs/ARCHITECTURE.md)** |
| **Financial Analyst / User**  | Use the tool to audit filings and generate reports. | ⮕ **[Operations Manual](docs/USER_GUIDE.md)**     |
| **Academic / Researcher**     | Understand methodology and reproducibility.         | ⮕ **[Operations Manual](docs/USER_GUIDE.md)**     |

---

## ⚡ One-Click Quickstart

For a live demonstration, use our unified launchers:

- ** macOS**: Double-click the **Financial Compliance Auditor.app** in the project root. (Or run `./launch.sh` from terminal).
- **🪟 Windows**: Double-click `launch.bat`.

> [!TIP]
> On the first run, the app will guide you through the **White-Glove Onboarding** loop to help you understand the core audit workflow.

---

## 🛠️ The Technology Stack

- **Reasoning**: Qwen 2.5 72B (via MLX Metal Acceleration)
- **Orchestration**: LangGraph (Reflecting DAG Workflow)
- **Data Tier**: LanceDB (High-performance Vector Store)
- **Analysis**: Unstructured.io (Layout-aware Document Parsing)
- **Interface**: Streamlit (High-Precision Forensic Workbench)
