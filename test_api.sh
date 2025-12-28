#!/bin/bash
# Kokoro TTS API Test Script
# Usage: ./test_api.sh [host] [port]

HOST=${1:-localhost}
PORT=${2:-8300}
BASE="http://${HOST}:${PORT}"

echo "🎙️ Kokoro TTS API Test"
echo "========================"
echo "Target: $BASE"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

pass() { echo -e "${GREEN}✓ $1${NC}"; }
fail() { echo -e "${RED}✗ $1${NC}"; }

# 1. Health Check
echo "1. Health Check"
if curl -sf "$BASE/health" | jq -e '.status == "healthy"' > /dev/null; then
    pass "Health check passed"
else
    fail "Health check failed"
fi

# 2. Status
echo "2. System Status"
STATUS=$(curl -sf "$BASE/api/status")
if echo "$STATUS" | jq -e '.device' > /dev/null; then
    DEVICE=$(echo "$STATUS" | jq -r '.device')
    pass "Status OK (device: $DEVICE)"
else
    fail "Status failed"
fi

# 3. Models
echo "3. List Models"
if curl -sf "$BASE/api/models" | jq -e 'keys | length > 0' > /dev/null; then
    pass "Models listed"
else
    fail "Models failed"
fi

# 4. Voices
echo "4. List Voices"
if curl -sf "$BASE/api/voices" | jq -e 'keys | length > 0' > /dev/null; then
    pass "Voices listed"
else
    fail "Voices failed"
fi

# 5. Single TTS (WAV)
echo "5. Single TTS (WAV)"
curl -sf -X POST "$BASE/api/tts" \
    -H "Content-Type: application/json" \
    -d '{"text":"Hello world","voice":"af_heart"}' \
    -o /tmp/kokoro_test.wav
if file /tmp/kokoro_test.wav | grep -q "WAVE audio"; then
    SIZE=$(ls -la /tmp/kokoro_test.wav | awk '{print $5}')
    pass "WAV generated ($SIZE bytes)"
else
    fail "WAV generation failed"
fi

# 6. TTS Base64
echo "6. TTS Base64"
RESULT=$(curl -sf -X POST "$BASE/api/tts/base64" \
    -H "Content-Type: application/json" \
    -d '{"text":"Testing base64","voice":"am_michael"}')
if echo "$RESULT" | jq -e '.audio' > /dev/null; then
    DUR=$(echo "$RESULT" | jq -r '.duration')
    pass "Base64 OK (duration: ${DUR}s)"
else
    fail "Base64 failed"
fi

# 7. Streaming TTS
echo "7. Streaming TTS"
curl -sf -X POST "$BASE/api/tts/stream" \
    -H "Content-Type: application/json" \
    -d '{"text":"Streaming test sentence.","voice":"af_bella"}' \
    -o /tmp/kokoro_stream.bin
SIZE=$(ls -la /tmp/kokoro_stream.bin 2>/dev/null | awk '{print $5}')
if [ "$SIZE" -gt 1000 ]; then
    pass "Stream OK ($SIZE bytes)"
else
    fail "Stream failed"
fi

# 8. Batch TTS
echo "8. Batch TTS"
RESULT=$(curl -sf -X POST "$BASE/api/tts/batch" \
    -H "Content-Type: application/json" \
    -d '{"items":[{"id":"1","text":"First"},{"id":"2","text":"Second"}]}')
if echo "$RESULT" | jq -e '.success == 2' > /dev/null; then
    pass "Batch OK (2/2 success)"
else
    fail "Batch failed"
fi

# 9. Chinese Model
echo "9. Chinese Model TTS"
RESULT=$(curl -sf -X POST "$BASE/api/tts/base64" \
    -H "Content-Type: application/json" \
    -d '{"text":"你好世界","voice":"zf_001","model":"hexgrad/Kokoro-82M-v1.1-zh"}')
if echo "$RESULT" | jq -e '.audio' > /dev/null; then
    pass "Chinese model OK"
else
    fail "Chinese model failed"
fi

# 10. WebSocket (Python)
echo "10. WebSocket TTS"
python3 << 'EOF' 2>/dev/null
import asyncio, websockets, json, sys
async def test():
    try:
        async with websockets.connect(f"ws://{sys.argv[1]}:{sys.argv[2]}/ws/tts", close_timeout=5) as ws:
            await ws.send(json.dumps({"text":"WebSocket test","voice":"af_heart"}))
            while True:
                msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
                if msg["status"] == "done":
                    print(f"OK:{msg['total_chunks']}")
                    return
                elif msg["status"] == "error":
                    print(f"ERR:{msg['error']}")
                    return
    except Exception as e:
        print(f"ERR:{e}")
asyncio.run(test())
EOF
WS_RESULT=$(python3 -c "
import asyncio, websockets, json
async def test():
    try:
        async with websockets.connect('ws://${HOST}:${PORT}/ws/tts', close_timeout=5) as ws:
            await ws.send(json.dumps({'text':'WebSocket test','voice':'af_heart'}))
            while True:
                msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
                if msg['status'] == 'done':
                    print(f'OK:{msg[\"total_chunks\"]}')
                    return
                elif msg['status'] == 'error':
                    print(f'ERR:{msg[\"error\"]}')
                    return
    except Exception as e:
        print(f'ERR:{e}')
asyncio.run(test())
" 2>/dev/null)
if [[ "$WS_RESULT" == OK:* ]]; then
    CHUNKS=${WS_RESULT#OK:}
    pass "WebSocket OK ($CHUNKS chunks)"
else
    fail "WebSocket failed: $WS_RESULT"
fi

# 11. GPU Offload
echo "11. GPU Offload"
if curl -sf -X POST "$BASE/api/offload" | jq -e '.status == "offloaded"' > /dev/null; then
    pass "GPU offload OK"
else
    fail "GPU offload failed"
fi

echo ""
echo "========================"
echo "Test completed!"

# Cleanup
rm -f /tmp/kokoro_test.wav /tmp/kokoro_stream.bin
