#!/bin/bash
# Kokoro TTS - One-click Start Script

set -e
cd "$(dirname "$0")"

echo "🎙️ Kokoro TTS Docker Launcher"
echo "=============================="

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

# Check nvidia-docker
if command -v nvidia-smi &> /dev/null; then
    echo "✅ NVIDIA GPU detected"
    
    # Auto-select GPU with least memory usage
    GPU_ID=$(nvidia-smi --query-gpu=index,memory.used --format=csv,noheader,nounits | \
             sort -t',' -k2 -n | head -1 | cut -d',' -f1 | tr -d ' ')
    
    if [ -n "$GPU_ID" ]; then
        echo "🎯 Selected GPU $GPU_ID (lowest memory usage)"
        export NVIDIA_VISIBLE_DEVICES=$GPU_ID
    fi
else
    echo "⚠️ No NVIDIA GPU detected, running on CPU"
    export NVIDIA_VISIBLE_DEVICES=""
fi

# Load .env if exists
if [ -f .env ]; then
    echo "📄 Loading .env configuration"
    export $(grep -v '^#' .env | xargs)
fi

# Set defaults
export PORT=${PORT:-8300}
export GPU_IDLE_TIMEOUT=${GPU_IDLE_TIMEOUT:-300}
export DEFAULT_MODEL=${DEFAULT_MODEL:-hexgrad/Kokoro-82M}

# Check port availability
if ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
    echo "⚠️ Port $PORT is in use, finding available port..."
    for p in $(seq 8300 8399); do
        if ! ss -tlnp 2>/dev/null | grep -q ":$p "; then
            export PORT=$p
            echo "✅ Using port $PORT"
            break
        fi
    done
fi

echo ""
echo "📋 Configuration:"
echo "   Port: $PORT"
echo "   GPU: ${NVIDIA_VISIBLE_DEVICES:-CPU}"
echo "   Idle Timeout: ${GPU_IDLE_TIMEOUT}s"
echo "   Default Model: $DEFAULT_MODEL"
echo ""

# Build and start
echo "🔨 Building Docker image..."
docker compose build --quiet

echo "🚀 Starting Kokoro TTS..."
docker compose up -d

# Wait for health check
echo "⏳ Waiting for service to be ready..."
for i in {1..30}; do
    if curl -s "http://localhost:$PORT/health" > /dev/null 2>&1; then
        echo ""
        echo "✅ Kokoro TTS is ready!"
        echo ""
        echo "🌐 Access URLs:"
        echo "   UI:      http://localhost:$PORT"
        echo "   API:     http://localhost:$PORT/api/tts"
        echo "   Swagger: http://localhost:$PORT/apidocs"
        echo ""
        echo "📖 Quick API test:"
        echo "   curl -X POST http://localhost:$PORT/api/tts \\"
        echo "     -H 'Content-Type: application/json' \\"
        echo "     -d '{\"text\":\"Hello world\",\"voice\":\"af_heart\"}' \\"
        echo "     --output test.wav"
        echo ""
        exit 0
    fi
    sleep 2
    echo -n "."
done

echo ""
echo "⚠️ Service may still be starting. Check logs with:"
echo "   docker compose logs -f"
