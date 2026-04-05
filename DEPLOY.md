# ENTRO-AI Deployment Guide

## 📋 Overview

This guide covers deployment options for **ENTRO-AI** - the entropy-resistant inference architecture for LLMs.

**Builds on ENTROPIA (E-LAB-01):** [10.5281/zenodo.19416737](https://doi.org/10.5281/zenodo.19416737)

---

## 🚀 Quick Deployment

### Development Mode

```bash
# Clone repository
git clone https://gitlab.com/gitdeeper10/entro-ai.git
cd entro-ai

# Install with development dependencies
pip install -e ".[dev]"

# Run EDT controller with vLLM
entro-ai edt --vllm-endpoint http://localhost:8000

# Launch Ψ-Dashboard
entro-ai dashboard --host 127.0.0.1 --port 8080
```

Production Mode (Simple)

```bash
# Install production version
pip install entro-ai

# Run with production settings
export ENTRO_AI_ENV=production
export ENTRO_AI_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
entro-ai dashboard --host 0.0.0.0 --port 8080 --workers 4
```

---

🐳 Docker Deployment

Basic Docker Run

```bash
# Pull image
docker pull gitdeeper10/entro-ai:latest

# Run container with vLLM integration
docker run -d \
  --name entro-ai \
  -p 8080:8080 \
  -e ENTRO_AI_ENV=production \
  -e VLLM_ENDPOINT=http://vllm:8000 \
  -e ENTRO_AI_SECRET_KEY=your-secret-key \
  --network ai-network \
  gitdeeper10/entro-ai:latest
```

Docker Compose (Full Stack)

Create docker-compose.yml:

```yaml
version: '3.8'

services:
  vllm:
    image: vllm/vllm-openai:latest
    container_name: vllm
    command: --model meta-llama/Llama-2-7b-chat-hf --api-key token-abc123
    ports:
      - "8000:8000"
    volumes:
      - ~/.cache/huggingface:/root/.cache/huggingface
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  entro-ai:
    image: gitdeeper10/entro-ai:latest
    container_name: entro-ai
    ports:
      - "8080:8080"
      - "9090:9090"
    environment:
      - ENTRO_AI_ENV=production
      - ENTRO_AI_SECRET_KEY=${ENTRO_AI_SECRET_KEY}
      - VLLM_ENDPOINT=http://vllm:8000
      - ENTRO_AI_ARCHITECTURE=transformer_llm
      - EDT_L1_THRESHOLD=1.5
      - EDT_L2_THRESHOLD=1.7
      - EDT_L3_THRESHOLD=1.85
      - EDT_L4_THRESHOLD=2.0
    depends_on:
      - vllm
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: entro-ai-redis
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

Run:

```bash
docker-compose up -d
```

---

🔧 Configuration

Environment Variables

Variable Default Description
ENTRO_AI_ENV development Environment (production/development)
ENTRO_AI_ARCHITECTURE transformer_llm Model architecture
VLLM_ENDPOINT http://localhost:8000 vLLM API endpoint
EDT_L1_THRESHOLD 1.5 Soft intervention threshold
EDT_L2_THRESHOLD 1.7 Medium intervention threshold
EDT_L3_THRESHOLD 1.85 Hard intervention threshold
EDT_L4_THRESHOLD 2.0 Critical threshold
ENTRO_AI_SECRET_KEY - Secret key for sessions

Architecture-Specific Settings

```bash
# For Transformer LLM (default)
export ENTRO_AI_ARCHITECTURE=transformer_llm
export ENTRO_AI_SCALING_EXPONENT=1.63

# For BERT-class
export ENTRO_AI_ARCHITECTURE=bert
export ENTRO_AI_SCALING_EXPONENT=1.58

# For Neuromorphic SNN
export ENTRO_AI_ARCHITECTURE=neuromorphic
export ENTRO_AI_SCALING_EXPONENT=1.42
```

---

📊 Monitoring

Ψ-Dashboard Access

· URL: http://localhost:8080/dashboard
· Real-time Ψ monitoring
· τ_collapse countdown
· κ (output coherence) prediction

Prometheus Metrics

ENTRO-AI exposes metrics at /metrics:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'entro-ai'
    static_configs:
      - targets: ['entro-ai:9090']
```

Grafana Dashboard

Import dashboard ID: entro-ai-001

---

🔒 Security Hardening

Production Checklist

· Set ENTRO_AI_ENV=production
· Generate secure ENTRO_AI_SECRET_KEY
· Enable HTTPS with valid SSL certificate
· Restrict allowed origins
· Use read-only data volumes
· Run as non-root user
· Enable rate limiting
· Configure firewall rules

SSL Configuration (Nginx)

```nginx
server {
    listen 443 ssl http2;
    server_name entropy.your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    location / {
        proxy_pass http://entro-ai:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

🧪 Testing Deployment

```bash
# Health check
curl http://localhost:8080/health

# Get current Ψ for inference
curl http://localhost:8080/api/v1/psi

# Verify EDT controller
curl http://localhost:8080/api/v1/edt/status
```

---

🔄 Updates & Rollbacks

```bash
# Pull latest image
docker pull gitdeeper10/entro-ai:latest

# Rolling restart
docker-compose up -d --no-deps entro-ai

# Rollback
docker-compose down
docker-compose up -d
```

---

📈 Scaling

· Horizontal scaling: Stateless dashboard with Redis sessions
· Vertical scaling: Increase CPU/memory for complex models
· Multi-model: Deploy multiple EDT controllers per model

---

🆘 Troubleshooting

Issue Solution
vLLM connection failed Check VLLM_ENDPOINT and network
Ψ not updating Verify telemetry adapter
EDT not intervening Check thresholds and η_EDT values
Dashboard not loading Check firewall and CORS settings

Logs

```bash
# Docker logs
docker logs entro-ai

# vLLM logs
docker logs vllm

# Combined logs
docker-compose logs -f
```

---

📚 Additional Resources

· ENTRO-AI Documentation
· ENTROPIA Framework
· GitLab Repository

---

For deployment support, contact: gitdeeper@gmail.com

"Artificial intelligence that understands its own thermodynamic limits is not weaker. It is, for the first time, physically honest."
