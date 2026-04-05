# ENTRO-AI Installation Guide

## 📋 System Requirements

### Minimum Requirements
- **OS:** Linux, macOS, or Windows (WSL2 recommended)
- **Python:** 3.11 or higher
- **RAM:** 8 GB (16 GB recommended for 13B+ models)
- **Storage:** 5 GB free space
- **GPU:** Optional (CPU fallback available)

### Recommended for Production
- **OS:** Ubuntu 22.04 LTS
- **Python:** 3.11
- **RAM:** 32 GB
- **Storage:** 50 GB SSD
- **GPU:** NVIDIA GPU with 16GB+ VRAM (H100, A100, RTX 4090)
- **CUDA:** 11.8 or higher

**Builds on ENTROPIA (E-LAB-01):** [10.5281/zenodo.19416737](https://doi.org/10.5281/zenodo.19416737)

---

## 🚀 Quick Install

### Using pip

```bash
# Install from PyPI
pip install entro-ai

# Verify installation
entro-ai --version
entro-ai health-check
```

Using Docker

```bash
# Pull from Docker Hub
docker pull gitdeeper10/entro-ai:latest

# Run container
docker run -p 8080:8080 gitdeeper10/entro-ai:latest dashboard
```

---

🔧 Detailed Installation

1. Install Python

Ubuntu/Debian:

```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev
```

macOS:

```bash
brew install python@3.11
```

Windows: Download from python.org

2. Create Virtual Environment

```bash
python3.11 -m venv entro-ai-env
source entro-ai-env/bin/activate  # On Windows: entro-ai-env\Scripts\activate
```

3. Install from Source

```bash
# Clone repository
git clone https://gitlab.com/gitdeeper10/entro-ai.git
cd entro-ai

# Install with all dependencies
pip install -e ".[all]"

# Or install core only
pip install -e ".[core]"
```

4. Install vLLM (Optional - for LLM integration)

```bash
# Install vLLM for model serving
pip install vllm

# Download a sample model
python -c "from transformers import AutoModelForCausalLM; AutoModelForCausalLM.from_pretrained('meta-llama/Llama-2-7b-chat-hf')"
```

5. Verify Installation

```bash
# Run tests
pytest tests/

# Run example
python examples/basic_monitoring.py

# Launch dashboard
entro-ai dashboard
```

---

🐳 Docker Installation

Build Image

```bash
git clone https://gitlab.com/gitdeeper10/entro-ai.git
cd entro-ai
docker build -f Dockerfile.ai -t entro-ai:latest .
```

Run with vLLM

```bash
# Start vLLM
docker run -d --gpus all --name vllm -p 8000:8000 vllm/vllm-openai:latest

# Start ENTRO-AI
docker run -d --name entro-ai -p 8080:8080 \
  -e VLLM_ENDPOINT=http://vllm:8000 \
  --network container:vllm \
  entro-ai:latest
```

---

📦 Platform-Specific Notes

Linux (Ubuntu/Debian)

```bash
# Install system dependencies
sudo apt install build-essential libopenblas-dev libffi-dev

# Install ENTRO-AI
pip install entro-ai
```

macOS

```bash
# Install via Homebrew
brew install openblas

# Install ENTRO-AI
pip install entro-ai
```

Windows (WSL2)

```bash
# Install WSL2, then Ubuntu
wsl --install

# Inside WSL, follow Linux instructions
```

---

🔍 Verification

Check Installation

```python
import entro_ai
print(entro_ai.__version__)
print(f"Builds on ENTROPIA: {entro_ai.ENTROPIA_DOI}")

# Test core functions
from entro_ai import EntroAIMonitor

monitor = EntroAIMonitor(
    architecture="transformer_llm",
    n_layers=32,
    d_model=4096,
    kv_cache_gb=40.0
)

monitor.update(
    kv_cache_used=0.75,
    attn_flops_util=0.70,
    token_rate=800
)

print(f"Ψ = {monitor.psi:.3f}")
print(f"κ = {monitor.kappa:.3f}")
print(f"τ_collapse = {monitor.tau_collapse:.1f}s")
```

Run Benchmark

```bash
# Run transformer calibration test
python calibration/transformer_calibrator.py --quick

# Run EDT controller test
entro-ai edt --test-mode
```

---

🐛 Troubleshooting

Issue Solution
ModuleNotFoundError: No module named 'entro_ai' Activate virtual environment: source entro-ai-env/bin/activate
ImportError: libcudart.so Install CUDA toolkit or use CPU-only mode
vLLM connection failed Check endpoint: curl http://localhost:8000/health
Dashboard port in use Change port: entro-ai dashboard --port 8081
GPU out of memory Reduce batch size or use smaller model

Logs

```bash
# ENTRO-AI logs
entro-ai dashboard --log-level DEBUG

# vLLM logs
vllm serve meta-llama/Llama-2-7b-chat-hf --log-level debug
```

---

✅ Next Steps

1. Read the ENTRO-AI Research Paper
2. Explore Examples
3. Run Tutorials
4. Review ENTROPIA Framework

---

"Artificial intelligence that understands its own thermodynamic limits is not weaker. It is, for the first time, physically honest."
