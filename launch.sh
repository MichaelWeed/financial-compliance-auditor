#!/bin/bash

# Forensic Compliance Auditor - Sovereign Launcher
# --------------------------------------------------
# This script ignites the MLX Inference Node and the Forensic UI.

# 1. Environment Setup
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$PROJECT_DIR"

# Try to find conda executable
CONDA_EXE=$(which conda)
if [ -z "$CONDA_EXE" ]; then
    # Fallback to common homebrew path
    CONDA_EXE="/opt/homebrew/bin/conda"
fi

CONDA_ENV="compliance-auditor"
MODEL="mlx-community/Qwen2.5-72B-Instruct-4bit"
PORT=8080

echo "--- 🚀 IGNITING SOVEREIGN AUDITOR [$PROJECT_DIR] ---"

# 2. Check/Start Inference Node
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "💡 REASONING NODE is already online on port $PORT."
else
    echo "🧠 STARTING INFERENCE NODE ($MODEL)..."
    $CONDA_EXE run -n $CONDA_ENV python -m mlx_lm.server --model $MODEL --port $PORT > logs/server.log 2>&1 &
    
    # Wait for server to respond
    echo -n "   Waiting for node to initialize..."
    for i in {1..30}; do
        if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
            echo " DONE."
            break
        fi
        echo -n "."
        sleep 2
    done
fi

# 3. Launch UI
echo "⚖️  AWAKENING FORENSIC WORKBENCH..."
$CONDA_EXE run -n $CONDA_ENV streamlit run app.py --server.port 8503
