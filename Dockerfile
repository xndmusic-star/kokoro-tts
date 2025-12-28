# Kokoro TTS Docker Image
FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3.11-venv python3.11-dev python3-pip \
    espeak-ng libespeak-ng1 \
    git curl wget \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.11 /usr/bin/python \
    && python -m pip install --upgrade pip

WORKDIR /app

# Install Python dependencies in one layer
RUN pip install --no-cache-dir \
    torch --index-url https://download.pytorch.org/whl/cu124 && \
    pip install --no-cache-dir \
    kokoro>=0.9.4 \
    "misaki[en]>=0.9.4" \
    "misaki[zh]>=0.9.4" \
    soundfile \
    fastapi \
    uvicorn[standard] \
    python-multipart \
    fastmcp \
    numpy

# Copy application code
COPY kokoro/ ./kokoro/
COPY docker/ ./docker/

# Create directories
RUN mkdir -p /tmp/kokoro/output /tmp/kokoro/cache

ENV PORT=8300
ENV GPU_IDLE_TIMEOUT=300
ENV HF_HOME=/tmp/kokoro/cache

EXPOSE 8300

CMD ["python", "docker/server.py"]
