# Kokoro TTS - All-in-One Guide

## Features

- **REST API**: Single TTS, Base64 output, Streaming
- **Batch API**: Process multiple texts at once
- **WebSocket**: Real-time bidirectional TTS
- **MCP Server**: AI agent integration

## API Endpoints

### Single TTS
```bash
# Returns WAV file
curl -X POST https://kokoro.aws.xin/api/tts \
  -H 'Content-Type: application/json' \
  -d '{"text":"Hello","voice":"af_heart","speed":1.0}' \
  -o output.wav

# Returns base64
curl -X POST https://kokoro.aws.xin/api/tts/base64 \
  -H 'Content-Type: application/json' \
  -d '{"text":"Hello","voice":"af_heart"}'
```

### Streaming TTS
```bash
curl -X POST https://kokoro.aws.xin/api/tts/stream \
  -H 'Content-Type: application/json' \
  -d '{"text":"Long text here...","voice":"af_heart"}' \
  -o stream.bin
```

### Batch TTS
```bash
curl -X POST https://kokoro.aws.xin/api/tts/batch \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "hexgrad/Kokoro-82M",
    "items": [
      {"id": "1", "text": "Hello", "voice": "af_heart"},
      {"id": "2", "text": "World", "voice": "am_michael"}
    ]
  }'
```

### WebSocket
```javascript
const ws = new WebSocket('wss://kokoro.aws.xin/ws/tts');
ws.onopen = () => {
  ws.send(JSON.stringify({text: "Hello", voice: "af_heart"}));
};
ws.onmessage = (e) => {
  const data = JSON.parse(e.data);
  if (data.status === 'chunk') {
    // Play audio: data.audio (base64)
  }
};
```

## MCP Configuration

```json
{
  "mcpServers": {
    "kokoro-tts": {
      "command": "docker",
      "args": ["exec", "-i", "kokoro-tts", "python", "docker/server.py", "mcp"]
    }
  }
}
```

### MCP Tools

| Tool | Description |
|------|-------------|
| `tts_generate` | Generate speech, returns base64 |
| `tts_save` | Generate and save to file |
| `tts_batch` | Batch processing |
| `gpu_status` | Get GPU status |
| `gpu_offload` | Release GPU memory |
| `list_voices` | List available voices |
| `list_models` | List available models |

## Models

| Model | Languages |
|-------|-----------|
| `hexgrad/Kokoro-82M` | EN, ZH, JA, ES, FR, HI, IT, PT |
| `hexgrad/Kokoro-82M-v1.1-zh` | EN, ZH (100+ Chinese voices) |

## Docker

```bash
# Pull and run
docker pull neosun/kokoro-tts:latest
docker run -d --gpus all -p 8300:8300 neosun/kokoro-tts:latest

# Or use docker-compose
docker compose up -d
```
