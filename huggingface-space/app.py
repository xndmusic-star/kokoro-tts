"""Xandão Voice Studio — Kokoro-82M em português do Brasil."""
import os
import re
import tempfile
from functools import lru_cache

import gradio as gr
import numpy as np
import soundfile as sf

VOICES = {
    "Alex — masculino (BR)": "pm_alex",
    "Santa — masculino (BR)": "pm_santa",
    "Dora — feminino (BR)": "pf_dora",
}
SAMPLE_RATE = 24000
MAX_CHARS = 1800


@lru_cache(maxsize=1)
def get_pipeline():
    from kokoro import KPipeline
    return KPipeline(lang_code="p", device="cpu")


def generate_audio(text, voice_label, speed):
    text = (text or "").strip()
    if not text:
        raise gr.Error("Digite algum texto para narrar.")
    if len(text) > MAX_CHARS:
        raise gr.Error(f"Limite de {MAX_CHARS} caracteres por geração.")
    if voice_label not in VOICES:
        raise gr.Error("Selecione uma voz válida.")
    chunks = []
    # Quebras de frases mantêm a entrada curta para fonemização em português.
    sentences = re.split(r"(?<=[.!?;:])\s+|\n+", text)
    for sentence in sentences:
        if not sentence.strip():
            continue
        for _, _, audio in get_pipeline()(sentence.strip(), voice=VOICES[voice_label], speed=float(speed)):
            if audio is not None:
                chunks.append(np.asarray(audio, dtype=np.float32))
    if not chunks:
        raise gr.Error("O modelo não gerou áudio. Tente um texto menor.")
    output = np.concatenate(chunks)
    fd, path = tempfile.mkstemp(suffix=".wav", prefix="xandao-voz-")
    os.close(fd)
    sf.write(path, output, SAMPLE_RATE)
    return path, path


with gr.Blocks(title="Xandão Voice Studio", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎙️ Xandão Voice Studio\nLocuções em português brasileiro pelo Safari do iPhone.")
    text = gr.Textbox(
        label="Seu roteiro",
        value="Você sabe o que é microfonia? Ela acontece quando o microfone capta o som da própria caixa e o amplifica novamente.",
        lines=7,
        max_lines=14,
        placeholder="Digite sua narração aqui...",
    )
    voice = gr.Dropdown(choices=list(VOICES.keys()), value="Alex — masculino (BR)", label="Voz")
    speed = gr.Slider(0.75, 1.25, value=1.0, step=0.05, label="Velocidade")
    button = gr.Button("Gerar locução", variant="primary")
    player = gr.Audio(label="Ouvir narração", type="filepath")
    download = gr.File(label="Baixar arquivo WAV")
    button.click(generate_audio, inputs=[text, voice, speed], outputs=[player, download])
    gr.Markdown("Modelo: Kokoro 82M. O processamento ocorre no servidor do Space, não no iPhone.")

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
