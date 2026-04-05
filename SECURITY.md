# ENTRO-AI Security Policy

## 📋 Supported Versions

| Version | Supported | Security Updates |
|---------|-----------|------------------|
| 1.0.x   | ✅ Yes    | Critical fixes only |
| < 1.0   | ❌ No     | End of life |

**Builds on ENTROPIA (E-LAB-01):** [10.5281/zenodo.19416737](https://doi.org/10.5281/zenodo.19416737)

---

## 🔒 Security Model

ENTRO-AI is an entropy monitoring framework for AI inference systems. The security model is based on:

1. **Read-only Telemetry**: ENTRO-AI only reads inference metrics, never modifies model weights
2. **Local Binding**: Ψ-Dashboard binds to localhost by default
3. **Isolated Interventions**: EDT controller actions are reversible and logged

---

## 🚨 Reporting a Vulnerability

If you discover a security vulnerability in ENTRO-AI, please:

### Do NOT:
- Open a public GitHub/GitLab issue
- Discuss the vulnerability in public channels
- Disclose details before a fix is available

### DO:
1. Email the maintainer: **gitdeeper@gmail.com**
2. Include detailed steps to reproduce
3. If possible, include a proof of concept
4. Allow up to **72 hours** for an initial response

---

## 🔐 Security Best Practices

### For Production Deployment

```bash
# Always use environment variables for secrets
export ENTRO_AI_SECRET_KEY="your-secure-key"
export ENTRO_AI_ALLOWED_ORIGINS="https://your-domain.com"

# Run with non-root user
docker run -u 1000:1000 entro-ai:latest

# Use read-only data mounts
docker run -v /data:/home/entro-ai/data:ro entro-ai:latest

# Enable HTTPS in production
entro-ai dashboard --https --cert /path/to/cert.pem --key /path/to/key.pem
```

Configuration Security

```bash
# .env.production - Never commit to repository!
ENTRO_AI_SECRET_KEY=change-this-to-a-secure-random-string
ENTRO_AI_ALLOWED_ORIGINS=https://entropy.your-domain.com
ENTRO_AI_LOG_LEVEL=WARNING
VLLM_API_KEY=your-vllm-api-key
```

Network Security

```bash
# Bind dashboard to localhost when not behind reverse proxy
entro-ai dashboard --host 127.0.0.1 --port 8080

# Use firewall rules
sudo ufw allow from 127.0.0.1 to any port 8080
```

---

📊 Data Sensitivity

ENTRO-AI processes inference telemetry including:

· KV-cache occupancy
· Token generation rates
· Attention bandwidth utilization
· GPU memory pressure

This data may reveal model usage patterns. Always:

· Encrypt data at rest
· Use secure channels (HTTPS/WSS)
· Implement access controls
· Anonymize telemetry where possible

---

🔄 Security Updates

Security updates are published through:

· PyPI: pip install --upgrade entro-ai
· Docker Hub: docker pull gitdeeper10/entro-ai:latest
· GitLab Releases: gitlab.com/gitdeeper10/entro-ai/-/releases

---

📝 Vulnerability Disclosure Timeline

Phase Duration
Report Received Day 0
Initial Response Within 72 hours
Fix Development 7-14 days
Patch Release Day 14
Public Disclosure Day 21

---

🔗 Related Security Policies

· ENTROPIA Framework: 10.5281/zenodo.19416737

---

⚠️ Disclaimer

ENTRO-AI is a predictive framework for AI inference quality. It should not be used as the sole safety mechanism for critical AI systems. Always maintain human oversight and redundant safety systems.

---

For non-security issues, please open a GitLab Issue.

"Artificial intelligence that understands its own thermodynamic limits is not weaker. It is, for the first time, physically honest."
