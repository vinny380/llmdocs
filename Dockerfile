# syntax=docker/dockerfile:1
FROM python:3.12-slim

LABEL org.opencontainers.image.title="llmdocs" \
      org.opencontainers.image.description="Agent-first documentation platform" \
      org.opencontainers.image.source="https://github.com/yourorg/llmdocs"

# System deps needed by chromadb / sentence-transformers
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install locked deps first (cached layer — only invalidated when requirements.txt changes).
# PyPI's Linux torch wheel pulls CUDA (~2GB+ of nvidia-* wheels). We only need CPU inference
# for sentence-transformers in the container, so install torch from PyTorch's CPU index first
# and exclude the torch line from the full freeze so pip does not replace it.
COPY requirements.txt .
RUN pip install --no-cache-dir torch==2.11.0 --index-url https://download.pytorch.org/whl/cpu && \
    grep -v '^torch==' requirements.txt > /tmp/requirements-without-torch.txt && \
    pip install --no-cache-dir -r /tmp/requirements-without-torch.txt

# Install the package itself
COPY pyproject.toml README.md ./
COPY llmdocs/ llmdocs/
RUN pip install --no-cache-dir --no-deps .

# Runtime directories
RUN mkdir -p /data/chroma /docs

# llmdocs.yaml is expected to be mounted or provided via environment;
# this default config points at the /docs volume and stores index in /data/chroma.
ENV LLMDOCS_CONFIG=/app/llmdocs.yaml
COPY docker/llmdocs.yaml /app/llmdocs.yaml

EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

ENTRYPOINT ["llmdocs"]
CMD ["serve", "--config", "/app/llmdocs.yaml", "--data-dir", "/data/chroma"]
