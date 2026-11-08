---
title: Xandao Voice Studio
emoji: 🎙️
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 5.49.1
app_file: app.py
python_version: "3.11"
short_description: Locucoes em portugues brasileiro com Kokoro 82M
---

# Xandão Voice Studio

Aplicativo de síntese de voz em português brasileiro, adaptado para Safari no iPhone.

O processamento é feito no Hugging Face Space. A primeira execução baixa os pesos de `hexgrad/Kokoro-82M`.

## Implantação

Crie um Space com SDK **Gradio**, depois configure no GitHub os segredos:
- `HF_TOKEN`: token Hugging Face com permissão de escrita para o Space.
- `HF_SPACE_ID`: identificador `usuario/nome-do-space`.

O workflow `.github/workflows/deploy-kokoro-space.yml` envia esta pasta ao Space quando alterada.

Os planos gratuitos do Spaces podem dormir ou não oferecer memória suficiente para executar este modelo. Não coloque dados sensíveis no texto de um Space público.
