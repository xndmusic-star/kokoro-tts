"""Kokoro TTS MCP Server"""
import os, sys, io, base64
sys.path.insert(0, '/app')

from fastmcp import FastMCP
import soundfile as sf

mcp = FastMCP("kokoro-tts")

# Shared GPU manager
_gpu_manager = None

def get_gpu_manager():
    global _gpu_manager
    if _gpu_manager is None:
        from server import GPUManager
        _gpu_manager = GPUManager(int(os.environ.get('GPU_IDLE_TIMEOUT', 300)))
    return _gpu_manager

@mcp.tool()
def tts_generate(text: str, voice: str = "af_heart", speed: float = 1.0, model: str = "hexgrad/Kokoro-82M") -> dict:
    """
    Generate speech from text.
    
    Args:
        text: Text to synthesize
        voice: Voice ID (e.g., af_heart, zf_xiaobei)
        speed: Speech speed (0.5-2.0)
        model: Model repo ID
    
    Returns:
        dict with base64 audio and metadata
    """
    try:
        import numpy as np
        gm = get_gpu_manager()
        lang_code = voice[0] if voice else 'a'
        pipeline = gm.get_pipeline(lang_code, model)
        
        audios = []
        for result in pipeline(text, voice=voice, speed=speed):
            if result.audio is not None:
                audios.append(result.audio.cpu().numpy())
        
        if not audios:
            return {"status": "error", "error": "No audio generated"}
        
        audio = np.concatenate(audios)
        buf = io.BytesIO()
        sf.write(buf, audio, 24000, format='WAV')
        buf.seek(0)
        
        return {
            "status": "success",
            "audio_base64": base64.b64encode(buf.read()).decode(),
            "sample_rate": 24000,
            "duration": len(audio) / 24000,
            "voice": voice,
            "model": model
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@mcp.tool()
def tts_save(text: str, output_path: str, voice: str = "af_heart", speed: float = 1.0, model: str = "hexgrad/Kokoro-82M") -> dict:
    """
    Generate speech and save to file.
    
    Args:
        text: Text to synthesize
        output_path: Output file path (.wav)
        voice: Voice ID
        speed: Speech speed (0.5-2.0)
        model: Model repo ID
    
    Returns:
        dict with file path and metadata
    """
    try:
        import numpy as np
        gm = get_gpu_manager()
        lang_code = voice[0] if voice else 'a'
        pipeline = gm.get_pipeline(lang_code, model)
        
        audios = []
        for result in pipeline(text, voice=voice, speed=speed):
            if result.audio is not None:
                audios.append(result.audio.cpu().numpy())
        
        if not audios:
            return {"status": "error", "error": "No audio generated"}
        
        audio = np.concatenate(audios)
        sf.write(output_path, audio, 24000)
        
        return {
            "status": "success",
            "file_path": output_path,
            "sample_rate": 24000,
            "duration": len(audio) / 24000
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@mcp.tool()
def gpu_status() -> dict:
    """Get GPU and model status."""
    return get_gpu_manager().get_status()

@mcp.tool()
def gpu_offload() -> dict:
    """Release GPU memory."""
    return get_gpu_manager().force_offload()

@mcp.tool()
def list_voices() -> dict:
    """List all available voices by language."""
    return {
        'a': ['af_heart','af_bella','af_nicole','am_michael','am_fenrir'],
        'b': ['bf_emma','bf_isabella','bm_george','bm_fable'],
        'z': ['zf_xiaobei','zf_xiaoyi','zm_yunjian','zm_yunyang'],
        'j': ['jf_alpha','jf_tebukuro','jm_kumo'],
        'e': ['ef_dora','em_alex'],
        'f': ['ff_siwis'],
        'h': ['hf_alpha','hm_omega'],
        'i': ['if_sara','im_nicola'],
        'p': ['pf_dora','pm_alex']
    }

@mcp.tool()
def list_models() -> dict:
    """List available models."""
    return {
        'hexgrad/Kokoro-82M': {'name': 'Kokoro 82M', 'langs': ['a','b','e','f','h','i','j','p','z']},
        'hexgrad/Kokoro-82M-v1.1-zh': {'name': 'Kokoro 82M v1.1 Chinese', 'langs': ['a','b','z']}
    }

if __name__ == "__main__":
    mcp.run()
