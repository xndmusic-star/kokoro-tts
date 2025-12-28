# Kokoro TTS Docker

All-in-One Docker image for [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) TTS with:
- 🎨 **Web UI** - Beautiful interface with all features
- 🔌 **REST API** - Full-featured HTTP endpoints
- 📡 **WebSocket** - Real-time bidirectional TTS
- 📦 **Batch Processing** - Process multiple texts at once
- 🌊 **Streaming** - Audio chunks as they generate
- 🤖 **MCP Server** - AI agent integration

## Quick Start

```bash
# Pull and run
docker pull neosun/kokoro-tts:latest
docker run -d --name kokoro-tts --gpus all -p 8300:8300 neosun/kokoro-tts:latest

# Access
# UI: http://localhost:8300
# Swagger: http://localhost:8300/docs
```

## Models

| Model | Languages | Best For |
|-------|-----------|----------|
| `hexgrad/Kokoro-82M` | EN, CN, JP, ES, FR, HI, IT, PT | General use |
| `hexgrad/Kokoro-82M-v1.1-zh` | EN, CN | Chinese optimized |

## API Reference

### Health & Status

```bash
# Health check
curl http://localhost:8300/health

# System status (GPU, memory, model)
curl http://localhost:8300/api/status

# Release GPU memory
curl -X POST http://localhost:8300/api/offload
```

### Configuration

```bash
# List models
curl http://localhost:8300/api/models

# List voices (default model)
curl http://localhost:8300/api/voices

# List voices (Chinese model)
curl "http://localhost:8300/api/voices?model=hexgrad/Kokoro-82M-v1.1-zh"
```

### Text-to-Speech

#### Single TTS (WAV file)
```bash
curl -X POST http://localhost:8300/api/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world","voice":"af_heart","speed":1.0}' \
  -o output.wav
```

#### TTS Base64
```bash
curl -X POST http://localhost:8300/api/tts/base64 \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world","voice":"af_heart","speed":1.0}'
# Returns: {"audio":"base64...","sample_rate":24000,"duration":1.5}
```

#### Streaming TTS
```bash
curl -X POST http://localhost:8300/api/tts/stream \
  -H "Content-Type: application/json" \
  -d '{"text":"Long text here...","voice":"af_heart"}' \
  -o stream.bin
# Returns: [4-byte length][wav chunk][4-byte length][wav chunk]...
```

#### Batch TTS
```bash
curl -X POST http://localhost:8300/api/tts/batch \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"id":"1","text":"First sentence","voice":"af_heart"},
      {"id":"2","text":"Second sentence","voice":"am_michael","speed":1.2}
    ],
    "model": "hexgrad/Kokoro-82M"
  }'
# Returns: {"results":[...],"total":2,"success":2}
```

### WebSocket

Connect to `ws://localhost:8300/ws/tts`

```javascript
const ws = new WebSocket('ws://localhost:8300/ws/tts');
ws.onopen = () => {
  ws.send(JSON.stringify({
    text: "Hello world",
    voice: "af_heart",
    speed: 1.0,
    model: "hexgrad/Kokoro-82M"
  }));
};
ws.onmessage = (e) => {
  const data = JSON.parse(e.data);
  if (data.status === 'chunk') {
    // data.audio = base64 WAV, data.index = chunk number
    playAudio(data.audio);
  } else if (data.status === 'done') {
    console.log(`Completed: ${data.total_chunks} chunks`);
  }
};
```

## Request Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | string | required | Text to synthesize |
| `voice` | string | `af_heart` | Voice ID |
| `speed` | float | `1.0` | Speed (0.5-2.0) |
| `model` | string | `hexgrad/Kokoro-82M` | Model repo ID |

## Voices

### Default Model (Kokoro-82M)

| Language | Voices |
|----------|--------|
| 🇺🇸 American English | af_heart, af_bella, af_nicole, am_michael, am_fenrir... |
| 🇬🇧 British English | bf_emma, bf_isabella, bm_george, bm_fable... |
| 🇨🇳 Chinese | zf_xiaobei, zf_xiaoyi, zm_yunjian, zm_yunyang... |
| 🇯🇵 Japanese | jf_alpha, jf_tebukuro, jm_kumo... |
| 🇪🇸 Spanish | ef_dora, em_alex |
| 🇫🇷 French | ff_siwis |
| 🇮🇳 Hindi | hf_alpha, hm_omega... |
| 🇮🇹 Italian | if_sara, im_nicola |
| 🇧🇷 Portuguese | pf_dora, pm_alex |

### Chinese Model (v1.1-zh)

| Language | Voices |
|----------|--------|
| 🇨🇳 Chinese | zf_001-zf_050, zm_001-zm_050 |
| 🇺🇸 American English | af_maple, af_sol |
| 🇬🇧 British English | bf_vale |

## MCP Integration

For AI agents (Claude, etc.), run MCP server:

```bash
docker exec -it kokoro-tts python /app/docker/server.py mcp
```

Or configure in your MCP client:
```json
{
  "mcpServers": {
    "kokoro-tts": {
      "command": "docker",
      "args": ["exec", "-i", "kokoro-tts", "python", "/app/docker/server.py", "mcp"]
    }
  }
}
```

### MCP Tools

| Tool | Description |
|------|-------------|
| `tts_generate` | Generate speech, returns base64 audio |
| `tts_save` | Generate and save to file |
| `tts_batch` | Batch generate multiple texts |
| `list_voices` | List available voices |
| `list_models` | List available models |
| `gpu_status` | Get GPU status |
| `gpu_offload` | Release GPU memory |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8300` | Server port |
| `GPU_IDLE_TIMEOUT` | `300` | Seconds before GPU offload |

## Docker Compose

```yaml
services:
  kokoro-tts:
    image: neosun/kokoro-tts:latest
    ports:
      - "8300:8300"
    environment:
      - GPU_IDLE_TIMEOUT=600
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
```

## Testing

```bash
# Run all API tests
./test_api.sh localhost 8300
```

## License

Apache 2.0 - Same as Kokoro-82M
