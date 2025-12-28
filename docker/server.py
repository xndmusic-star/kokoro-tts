"""Kokoro TTS Server - All-in-One: API + WebSocket + Batch + Stream + MCP"""
import os, sys, time, threading, io, base64, uuid, json, asyncio
from datetime import datetime
from typing import Optional, List, AsyncGenerator
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
import soundfile as sf
import numpy as np

sys.path.insert(0, '/app')

# ============== GPU Manager ==============
class GPUManager:
    def __init__(self, idle_timeout=300):
        self.idle_timeout = idle_timeout
        self.pipelines = {}
        self.last_used = 0
        self.lock = threading.Lock()
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    def _offload(self):
        if self.pipelines:
            self.pipelines.clear()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
    
    def force_offload(self):
        with self.lock:
            self._offload()
        return {"status": "offloaded", "device": self.device}
    
    def get_pipeline(self, lang_code='a', repo_id='hexgrad/Kokoro-82M'):
        from kokoro import KPipeline
        with self.lock:
            self.last_used = time.time()
            key = f"{lang_code}:{repo_id}"
            if key not in self.pipelines:
                self.pipelines[key] = KPipeline(lang_code=lang_code, repo_id=repo_id, device=self.device)
            return self.pipelines[key]
    
    def get_status(self):
        gpu_info = {}
        if torch.cuda.is_available():
            gpu_info = {
                "name": torch.cuda.get_device_name(0),
                "memory_used": f"{torch.cuda.memory_allocated(0)/1024**3:.2f}GB",
                "memory_total": f"{torch.cuda.get_device_properties(0).total_memory/1024**3:.2f}GB"
            }
        return {
            "device": self.device, "model_loaded": bool(self.pipelines),
            "idle_timeout": self.idle_timeout,
            "last_used": datetime.fromtimestamp(self.last_used).isoformat() if self.last_used else None,
            "gpu": gpu_info
        }
    
    def warmup(self):
        """Preload default model and voice to reduce first request latency"""
        print("🔥 Warming up model...")
        try:
            pipeline = self.get_pipeline('a', 'hexgrad/Kokoro-82M')
            # Generate a short audio to fully warm up
            for _ in pipeline("Hello", voice='af_heart', speed=1.0):
                pass
            print("✅ Model warmed up!")
        except Exception as e:
            print(f"⚠️ Warmup failed: {e}")

gpu_manager = GPUManager(int(os.environ.get('GPU_IDLE_TIMEOUT', 300)))

# Cleanup thread
def cleanup_thread():
    while True:
        time.sleep(60)
        with gpu_manager.lock:
            if gpu_manager.pipelines and time.time() - gpu_manager.last_used > gpu_manager.idle_timeout:
                gpu_manager._offload()
threading.Thread(target=cleanup_thread, daemon=True).start()

# ============== Voice Configs ==============
VOICES_DEFAULT = {
    'a': {'name': 'American English', 'voices': ['af_heart','af_bella','af_nicole','af_aoede','af_kore','af_sarah','af_nova','af_sky','af_alloy','af_jessica','af_river','am_michael','am_fenrir','am_puck','am_echo','am_eric','am_liam','am_onyx','am_santa','am_adam']},
    'b': {'name': 'British English', 'voices': ['bf_emma','bf_isabella','bf_alice','bf_lily','bm_george','bm_fable','bm_lewis','bm_daniel']},
    'z': {'name': 'Chinese', 'voices': ['zf_xiaobei','zf_xiaoyi','zf_xiaoxiao','zf_xiaoni','zm_yunjian','zm_yunyang','zm_yunxi','zm_yunxia']},
    'j': {'name': 'Japanese', 'voices': ['jf_alpha','jf_tebukuro','jf_gongitsune','jf_nezumi','jm_kumo']},
    'e': {'name': 'Spanish', 'voices': ['ef_dora','em_alex']},
    'f': {'name': 'French', 'voices': ['ff_siwis']},
    'h': {'name': 'Hindi', 'voices': ['hf_alpha','hf_beta','hm_omega','hm_psi']},
    'i': {'name': 'Italian', 'voices': ['if_sara','im_nicola']},
    'p': {'name': 'Portuguese', 'voices': ['pf_dora','pm_alex','pm_santa']}
}
VOICES_ZH = {
    'a': {'name': 'American English', 'voices': ['af_maple','af_sol']},
    'b': {'name': 'British English', 'voices': ['bf_vale']},
    'z': {'name': 'Chinese', 'voices': [f'zf_{i:03d}' for i in range(1,51)] + [f'zm_{i:03d}' for i in range(1,51)]}
}
MODELS = {
    'hexgrad/Kokoro-82M': {'name': 'Kokoro 82M', 'langs': ['a','b','e','f','h','i','j','p','z']},
    'hexgrad/Kokoro-82M-v1.1-zh': {'name': 'Kokoro 82M v1.1 Chinese', 'langs': ['a','b','z']}
}

# ============== Pydantic Models ==============
class TTSRequest(BaseModel):
    text: str
    voice: str = "af_heart"
    speed: float = 1.0
    model: str = "hexgrad/Kokoro-82M"

class TTSBatchItem(BaseModel):
    id: str
    text: str
    voice: str = "af_heart"
    speed: float = 1.0

class TTSBatchRequest(BaseModel):
    items: List[TTSBatchItem]
    model: str = "hexgrad/Kokoro-82M"

# ============== Core TTS Function ==============
def synthesize(text: str, voice: str, speed: float, model: str) -> np.ndarray:
    lang_code = voice[0] if voice else 'a'
    pipeline = gpu_manager.get_pipeline(lang_code, model)
    audios = []
    for result in pipeline(text, voice=voice, speed=speed):
        if result.audio is not None:
            audios.append(result.audio.cpu().numpy())
    if not audios:
        raise ValueError("No audio generated")
    return np.concatenate(audios)

def audio_to_wav_bytes(audio: np.ndarray) -> bytes:
    buf = io.BytesIO()
    sf.write(buf, audio, 24000, format='WAV')
    return buf.getvalue()

def audio_to_base64(audio: np.ndarray) -> str:
    return base64.b64encode(audio_to_wav_bytes(audio)).decode()

# ============== FastAPI App ==============
app = FastAPI(
    title="Kokoro TTS API",
    version="1.1.0",
    description="All-in-One TTS: REST API + WebSocket + Batch + Streaming"
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ---------- Health & Status ----------
@app.get("/health", tags=["System"])
async def health():
    return {"status": "healthy", "version": "1.1.0", "timestamp": datetime.now().isoformat()}

@app.get("/api/status", tags=["System"])
async def api_status():
    """Get GPU and system status"""
    return gpu_manager.get_status()

@app.post("/api/offload", tags=["System"])
async def api_offload():
    """Release GPU memory"""
    return gpu_manager.force_offload()

# ---------- Voices & Models ----------
@app.get("/api/voices", tags=["Config"])
async def api_voices(model: str = "hexgrad/Kokoro-82M"):
    """List available voices for a model"""
    return VOICES_ZH if 'v1.1-zh' in model else VOICES_DEFAULT

@app.get("/api/models", tags=["Config"])
async def api_models():
    """List available models"""
    return MODELS

# ---------- Single TTS ----------
@app.post("/api/tts", tags=["TTS"])
async def api_tts(req: TTSRequest):
    """Generate speech from text, returns WAV file"""
    try:
        audio = synthesize(req.text, req.voice, req.speed, req.model)
        return StreamingResponse(
            io.BytesIO(audio_to_wav_bytes(audio)),
            media_type="audio/wav",
            headers={"Content-Disposition": f"attachment; filename=tts_{uuid.uuid4().hex[:8]}.wav"}
        )
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/tts/base64", tags=["TTS"])
async def api_tts_base64(req: TTSRequest):
    """Generate speech, returns base64 encoded audio"""
    try:
        audio = synthesize(req.text, req.voice, req.speed, req.model)
        return {"audio": audio_to_base64(audio), "sample_rate": 24000, "duration": len(audio)/24000}
    except Exception as e:
        raise HTTPException(500, str(e))

# ---------- Streaming TTS ----------
@app.post("/api/tts/stream", tags=["TTS"])
async def api_tts_stream(req: TTSRequest):
    """Stream audio chunks as they are generated"""
    async def generate() -> AsyncGenerator[bytes, None]:
        lang_code = req.voice[0] if req.voice else 'a'
        pipeline = gpu_manager.get_pipeline(lang_code, req.model)
        for result in pipeline(req.text, voice=req.voice, speed=req.speed):
            if result.audio is not None:
                chunk = audio_to_wav_bytes(result.audio.cpu().numpy())
                yield len(chunk).to_bytes(4, 'little') + chunk
    return StreamingResponse(
        generate(), 
        media_type="application/octet-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )

# ---------- Batch TTS ----------
@app.post("/api/tts/batch", tags=["TTS"])
async def api_tts_batch(req: TTSBatchRequest):
    """Process multiple TTS requests, returns list of base64 audio"""
    results = []
    for item in req.items:
        try:
            audio = synthesize(item.text, item.voice, item.speed, req.model)
            results.append({
                "id": item.id, "status": "success",
                "audio": audio_to_base64(audio), "sample_rate": 24000, "duration": len(audio)/24000
            })
        except Exception as e:
            results.append({"id": item.id, "status": "error", "error": str(e)})
    return {"results": results, "total": len(req.items), "success": sum(1 for r in results if r["status"]=="success")}

# ---------- WebSocket TTS ----------
@app.websocket("/ws/tts")
async def websocket_tts(websocket: WebSocket):
    """WebSocket endpoint for real-time TTS
    
    Send JSON: {"text": "...", "voice": "af_heart", "speed": 1.0, "model": "..."}
    Receive: {"status": "chunk", "audio": "base64...", "index": 0} for each chunk
             {"status": "done", "total_chunks": N} when complete
             {"status": "error", "error": "..."} on error
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            text = data.get("text", "")
            voice = data.get("voice", "af_heart")
            speed = float(data.get("speed", 1.0))
            model = data.get("model", "hexgrad/Kokoro-82M")
            
            if not text:
                await websocket.send_json({"status": "error", "error": "text is required"})
                continue
            
            try:
                lang_code = voice[0] if voice else 'a'
                pipeline = gpu_manager.get_pipeline(lang_code, model)
                chunk_idx = 0
                for result in pipeline(text, voice=voice, speed=speed):
                    if result.audio is not None:
                        audio_b64 = audio_to_base64(result.audio.cpu().numpy())
                        await websocket.send_json({
                            "status": "chunk", "audio": audio_b64,
                            "index": chunk_idx, "sample_rate": 24000
                        })
                        chunk_idx += 1
                await websocket.send_json({"status": "done", "total_chunks": chunk_idx})
            except Exception as e:
                await websocket.send_json({"status": "error", "error": str(e)})
    except WebSocketDisconnect:
        pass

# ---------- UI ----------
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def index():
    from ui_template import get_html
    return get_html(VOICES_DEFAULT, VOICES_ZH, MODELS)

# ============== MCP Server (stdio mode) ==============
def run_mcp_server():
    """Run MCP server for AI agent integration"""
    from fastmcp import FastMCP
    mcp = FastMCP("kokoro-tts")
    
    @mcp.tool()
    def tts_generate(text: str, voice: str = "af_heart", speed: float = 1.0, model: str = "hexgrad/Kokoro-82M") -> dict:
        """Generate speech from text, returns base64 audio"""
        try:
            audio = synthesize(text, voice, speed, model)
            return {"status": "success", "audio_base64": audio_to_base64(audio), "sample_rate": 24000, "duration": len(audio)/24000}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    @mcp.tool()
    def tts_save(text: str, output_path: str, voice: str = "af_heart", speed: float = 1.0, model: str = "hexgrad/Kokoro-82M") -> dict:
        """Generate speech and save to file"""
        try:
            audio = synthesize(text, voice, speed, model)
            sf.write(output_path, audio, 24000)
            return {"status": "success", "file_path": output_path, "duration": len(audio)/24000}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    @mcp.tool()
    def tts_batch(items: list, model: str = "hexgrad/Kokoro-82M") -> dict:
        """Batch generate speech. items: [{"id": "1", "text": "...", "voice": "af_heart"}]"""
        results = []
        for item in items:
            try:
                audio = synthesize(item["text"], item.get("voice", "af_heart"), item.get("speed", 1.0), model)
                results.append({"id": item["id"], "status": "success", "audio_base64": audio_to_base64(audio)})
            except Exception as e:
                results.append({"id": item["id"], "status": "error", "error": str(e)})
        return {"results": results}
    
    @mcp.tool()
    def gpu_status() -> dict:
        """Get GPU status"""
        return gpu_manager.get_status()
    
    @mcp.tool()
    def gpu_offload() -> dict:
        """Release GPU memory"""
        return gpu_manager.force_offload()
    
    @mcp.tool()
    def list_voices(model: str = "hexgrad/Kokoro-82M") -> dict:
        """List available voices"""
        return VOICES_ZH if 'v1.1-zh' in model else VOICES_DEFAULT
    
    @mcp.tool()
    def list_models() -> dict:
        """List available models"""
        return MODELS
    
    mcp.run()

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'mcp':
        run_mcp_server()
    else:
        import uvicorn
        port = int(os.environ.get('PORT', 8300))
        print(f"🎙️ Kokoro TTS Server starting on http://0.0.0.0:{port}")
        # Warmup model in background
        threading.Thread(target=gpu_manager.warmup, daemon=True).start()
        uvicorn.run(app, host='0.0.0.0', port=port)
