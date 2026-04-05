# ENTRO-AI Dockerfile
# Entropy-Resistant Inference Architecture for LLMs
# Builds on ENTROPIA (E-LAB-01) — DOI: 10.5281/zenodo.19416737

FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libopenblas0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application
COPY entro_ai/ /app/entro_ai/
COPY pyproject.toml .
COPY README.md .
COPY LICENSE .
COPY NOTICE .

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Create non-root user
RUN useradd -m -u 1000 entro-ai && chown -R entro-ai:entro-ai /app
USER entro-ai

# Install package
RUN pip install --no-deps -e .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose ports
EXPOSE 8080 9090

# Run command
ENTRYPOINT ["entro-ai"]
CMD ["dashboard", "--host", "0.0.0.0", "--port", "8080"]
