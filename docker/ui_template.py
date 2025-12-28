"""UI Template for Kokoro TTS"""
import json

def get_html(voices_default, voices_zh, models):
    return HTML.replace("{{VOICES_DEFAULT}}", json.dumps(voices_default))\
        .replace("{{VOICES_ZH}}", json.dumps(voices_zh))\
        .replace("{{MODELS}}", json.dumps(models))

HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Kokoro TTS</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{--bg:#0a0a0f;--card:#12121a;--border:#1e1e2e;--primary:#8b5cf6;--text:#e2e8f0;--text-muted:#94a3b8;--success:#10b981;--error:#ef4444}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;line-height:1.6}
.container{max-width:1400px;margin:0 auto;padding:20px}
header{display:flex;justify-content:space-between;align-items:center;padding:20px 0;border-bottom:1px solid var(--border);margin-bottom:30px;flex-wrap:wrap;gap:15px}
.logo{display:flex;align-items:center;gap:12px}
.logo h1{font-size:1.8rem;font-weight:700;background:linear-gradient(135deg,var(--primary),#ec4899);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.version{background:var(--primary);color:#fff;padding:4px 12px;border-radius:20px;font-size:0.75rem;font-weight:600}
.nav{display:flex;gap:15px;align-items:center;flex-wrap:wrap}
.nav a{color:var(--text-muted);text-decoration:none;font-size:0.85rem;padding:6px 12px;border:1px solid var(--border);border-radius:6px;transition:all 0.2s}
.nav a:hover{color:var(--primary);border-color:var(--primary)}
.gpu-status{display:flex;align-items:center;gap:8px;padding:8px 16px;background:var(--card);border-radius:8px;border:1px solid var(--border)}
.gpu-dot{width:8px;height:8px;border-radius:50%;background:var(--success);animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.5}}
.main{display:grid;grid-template-columns:1fr 350px;gap:30px}
@media(max-width:1024px){.main{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:24px;margin-bottom:20px}
.card-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;flex-wrap:wrap;gap:10px}
.card-title{font-size:1rem;font-weight:600}
textarea{width:100%;min-height:150px;background:var(--bg);border:1px solid var(--border);border-radius:12px;padding:16px;color:var(--text);font-family:inherit;font-size:0.9rem;resize:vertical}
textarea:focus{outline:none;border-color:var(--primary)}
.controls{display:grid;gap:14px;margin-top:16px}
.control-row{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:640px){.control-row{grid-template-columns:1fr}}
.form-group label{display:block;font-size:0.8rem;color:var(--text-muted);margin-bottom:6px;font-weight:500}
select,input[type="range"]{width:100%;background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:10px;color:var(--text);font-size:0.85rem}
select:focus{outline:none;border-color:var(--primary)}
.btn{padding:12px 24px;border:none;border-radius:10px;font-size:0.9rem;font-weight:600;cursor:pointer;transition:all 0.2s;display:inline-flex;align-items:center;justify-content:center;gap:8px}
.btn-primary{background:linear-gradient(135deg,var(--primary),#7c3aed);color:#fff}
.btn-primary:hover{transform:translateY(-2px);box-shadow:0 10px 30px rgba(139,92,246,0.3)}
.btn-primary:disabled{opacity:0.5;cursor:not-allowed;transform:none}
.btn-secondary{background:var(--bg);border:1px solid var(--border);color:var(--text)}
.btn-secondary:hover{border-color:var(--primary)}
.btn-danger{background:var(--error);color:#fff}
.btn-group{display:flex;gap:10px;margin-top:16px;flex-wrap:wrap}
.audio-player{margin-top:16px;padding:16px;background:var(--bg);border-radius:12px}
audio{width:100%}
.stat{display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid var(--border);font-size:0.85rem}
.stat:last-child{border:none}
.stat-label{color:var(--text-muted)}
.stat-value{font-weight:600}
.voice-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(90px,1fr));gap:6px;max-height:200px;overflow-y:auto}
.voice-chip{padding:5px 8px;background:var(--bg);border:1px solid var(--border);border-radius:6px;font-size:0.7rem;cursor:pointer;text-align:center;transition:all 0.2s}
.voice-chip:hover,.voice-chip.active{border-color:var(--primary);background:rgba(139,92,246,0.1)}
.progress{height:4px;background:var(--border);border-radius:2px;overflow:hidden;margin-top:10px}
.progress-bar{height:100%;background:linear-gradient(90deg,var(--primary),#ec4899);width:0%;transition:width 0.3s}
.lang-tabs{display:flex;gap:5px;margin-bottom:10px;flex-wrap:wrap}
.lang-tab{padding:4px 10px;background:var(--bg);border:1px solid var(--border);border-radius:5px;font-size:0.7rem;cursor:pointer}
.lang-tab:hover,.lang-tab.active{border-color:var(--primary);color:var(--primary)}
.toast{position:fixed;bottom:20px;right:20px;padding:14px 20px;background:var(--card);border:1px solid var(--border);border-radius:10px;display:none;z-index:1000;font-size:0.85rem}
.stream-status{font-size:0.75rem;color:var(--text-muted);margin-top:8px;min-height:18px}
.stream-status.active{color:var(--success)}
.metrics-panel{margin-top:16px;padding:16px;background:var(--bg);border-radius:12px;border:1px solid var(--border)}
.metrics-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
@media(min-width:640px){.metrics-grid{grid-template-columns:repeat(4,1fr)}}
.metric-card{background:var(--card);border-radius:10px;padding:14px;text-align:center;border:1px solid var(--border)}
.metric-label{font-size:0.75rem;color:var(--text-muted);margin-bottom:6px}
.metric-value{font-size:1.4rem;font-weight:700;color:var(--success)}
.metric-status{margin-top:12px;padding:12px;background:rgba(16,185,129,0.1);border-radius:8px;text-align:center;font-size:0.85rem;color:var(--success)}
.metric-status.streaming{background:rgba(139,92,246,0.1);color:var(--primary)}
.tabs{display:flex;gap:0;margin-bottom:20px;border-bottom:1px solid var(--border)}
.tab{padding:10px 20px;cursor:pointer;border-bottom:2px solid transparent;font-size:0.85rem;color:var(--text-muted)}
.tab:hover{color:var(--text)}
.tab.active{color:var(--primary);border-bottom-color:var(--primary)}
.tab-content{display:none}
.tab-content.active{display:block}
footer{text-align:center;padding:30px 0;color:var(--text-muted);font-size:0.8rem;border-top:1px solid var(--border);margin-top:30px}
.ws-indicator{width:10px;height:10px;border-radius:50%;background:var(--error);display:inline-block;margin-right:8px}
.ws-indicator.connected{background:var(--success)}
</style>
</head>
<body>
<div class="container">
<header>
<div class="logo"><h1>🎙️ Kokoro TTS</h1><span class="version">v1.1.0</span></div>
<nav class="nav">
<a href="/docs">📄 Swagger</a>
<a href="/redoc">📚 ReDoc</a>
<div class="gpu-status"><span class="gpu-dot"></span><span id="gpu-label">GPU</span></div>
</nav>
</header>
<div class="main">
<div class="content">
<div class="tabs">
<div class="tab active" onclick="switchTab('single')">Single</div>
<div class="tab" onclick="switchTab('stream')">Stream</div>
<div class="tab" onclick="switchTab('websocket')">WebSocket</div>
<div class="tab" onclick="switchTab('batch')">Batch</div>
</div>

<div id="tab-single" class="tab-content active">
<div class="card">
<div class="card-header"><span class="card-title">📝 Text to Speech</span>
<select id="lang-select" onchange="updateLang()"></select></div>
<textarea id="text-input" placeholder="Enter text...">Kokoro is an open-weight TTS model with 82 million parameters.</textarea>
<div class="controls">
<div class="control-row">
<div class="form-group"><label>Model</label><select id="model-select" onchange="updateModel()"></select></div>
<div class="form-group"><label>Voice</label><select id="voice-select"></select></div>
</div>
<div class="form-group"><label>Speed: <span id="speed-val">1.0</span>x</label>
<input type="range" id="speed" min="0.5" max="2" step="0.1" value="1" oninput="document.getElementById('speed-val').textContent=this.value"></div>
</div>
<div class="btn-group">
<button class="btn btn-primary" id="gen-btn" onclick="generate()">🎵 Generate</button>
</div>
<div class="progress" id="progress" style="display:none"><div class="progress-bar" id="progress-bar"></div></div>
<div class="audio-player" id="audio-container" style="display:none"><audio id="audio-player" controls></audio></div>
</div>
</div>

<div id="tab-stream" class="tab-content">
<div class="card">
<div class="card-header"><span class="card-title">📡 Streaming TTS</span></div>
<textarea id="stream-text" placeholder="Enter text for streaming (multiple sentences recommended)...">This is the first sentence for streaming. This is the second sentence. And this is the third sentence. The audio will play as each sentence generates.</textarea>
<div class="controls">
<div class="control-row">
<div class="form-group"><label>Model</label><select id="stream-model" onchange="updateStreamVoices()"></select></div>
<div class="form-group"><label>Voice</label><select id="stream-voice"></select></div>
</div>
<div class="form-group"><label>Speed: <span id="stream-speed-val">1.0</span>x</label>
<input type="range" id="stream-speed" min="0.5" max="2" step="0.1" value="1" oninput="document.getElementById('stream-speed-val').textContent=this.value"></div>
</div>
<div class="btn-group">
<button class="btn btn-primary" id="stream-btn" onclick="streamAudio()">📡 Start Stream</button>
<button class="btn btn-danger" id="stop-btn" onclick="stopStream()" style="display:none">⏹ Stop</button>
</div>
<div class="metrics-panel" id="stream-metrics" style="display:none">
<div class="metrics-grid">
<div class="metric-card"><div class="metric-label">首字节延迟</div><div class="metric-value" id="m-ttfb">-</div></div>
<div class="metric-card"><div class="metric-label">开始播放</div><div class="metric-value" id="m-ttfp">-</div></div>
<div class="metric-card"><div class="metric-label">总时间</div><div class="metric-value" id="m-total">-</div></div>
<div class="metric-card"><div class="metric-label">数据大小</div><div class="metric-value" id="m-size">-</div></div>
</div>
<div class="metric-status" id="m-status"></div>
</div>
<div class="stream-status" id="stream-status"></div>
</div>
</div>

<div id="tab-websocket" class="tab-content">
<div class="card">
<div class="card-header"><span class="card-title">🔌 WebSocket TTS</span>
<span><span class="ws-indicator" id="ws-indicator"></span><span id="ws-status">Disconnected</span></span></div>
<textarea id="ws-text" placeholder="Enter text...">Hello via WebSocket! Real-time bidirectional communication.</textarea>
<div class="controls">
<div class="control-row">
<div class="form-group"><label>Model</label><select id="ws-model" onchange="updateWsVoices()"></select></div>
<div class="form-group"><label>Voice</label><select id="ws-voice"></select></div>
</div>
<div class="form-group"><label>Speed: <span id="ws-speed-val">1.0</span>x</label>
<input type="range" id="ws-speed" min="0.5" max="2" step="0.1" value="1" oninput="document.getElementById('ws-speed-val').textContent=this.value"></div>
</div>
<div class="btn-group">
<button class="btn btn-secondary" onclick="connectWS()">🔗 Connect</button>
<button class="btn btn-primary" onclick="sendWS()">📤 Send</button>
<button class="btn btn-danger" onclick="disconnectWS()">❌ Disconnect</button>
</div>
<div class="stream-status" id="ws-log"></div>
</div>
</div>

<div id="tab-batch" class="tab-content">
<div class="card">
<div class="card-header"><span class="card-title">📦 Batch Processing</span></div>
<textarea id="batch-text" placeholder='Enter JSON array:
[
  {"id": "1", "text": "Hello", "voice": "af_heart"},
  {"id": "2", "text": "World", "voice": "am_michael"}
]'>[{"id":"1","text":"Hello world","voice":"af_heart"},{"id":"2","text":"Goodbye","voice":"am_michael"}]</textarea>
<div class="controls">
<div class="control-row">
<div class="form-group"><label>Model</label><select id="batch-model" onchange="updateBatchVoices()"></select></div>
<div class="form-group"><label>Default Voice</label><select id="batch-voice"></select></div>
</div>
<div class="form-group"><label>Default Speed: <span id="batch-speed-val">1.0</span>x</label>
<input type="range" id="batch-speed" min="0.5" max="2" step="0.1" value="1" oninput="document.getElementById('batch-speed-val').textContent=this.value"></div>
</div>
<div class="btn-group">
<button class="btn btn-primary" id="batch-btn" onclick="batchGenerate()">🚀 Process Batch</button>
<button class="btn btn-secondary" onclick="playAllBatch()">▶️ Play All</button>
<button class="btn btn-secondary" onclick="downloadAllBatch()">💾 Download All</button>
</div>
<div id="batch-results" style="margin-top:16px"></div>
</div>
</div>
</div>

<div class="sidebar">
<div class="card">
<div class="card-header"><span class="card-title">⚡ Status</span>
<button class="btn btn-danger" onclick="offloadGPU()" style="padding:5px 10px;font-size:0.7rem">Release</button></div>
<div class="stat"><span class="stat-label">Device</span><span class="stat-value" id="stat-device">-</span></div>
<div class="stat"><span class="stat-label">Memory</span><span class="stat-value" id="stat-memory">-</span></div>
<div class="stat"><span class="stat-label">Model</span><span class="stat-value" id="stat-model">-</span></div>
</div>
<div class="card">
<div class="card-header"><span class="card-title">🎤 Voices</span></div>
<div class="lang-tabs" id="lang-tabs"></div>
<div class="voice-grid" id="voice-grid"></div>
</div>
</div>
</div>
<footer>Kokoro TTS v1.1.0 • All-in-One: REST + WebSocket + Batch + Stream</footer>
</div>
<div class="toast" id="toast"></div>
<script>
const voicesDefault={{VOICES_DEFAULT}},voicesZh={{VOICES_ZH}},models={{MODELS}};
let currentLang='a',currentVoices=voicesDefault,audioCtx=null,streamCtrl=null,ws=null;

let batchResults=[];
function init(){
const modelOpts=Object.entries(models).map(([k,v])=>`<option value="${k}">${v.name}</option>`).join('');
['model-select','stream-model','ws-model','batch-model'].forEach(id=>document.getElementById(id).innerHTML=modelOpts);
updateModel();updateStreamVoices();updateWsVoices();updateBatchVoices();updateStatus();setInterval(updateStatus,30000);
}
function switchTab(t){document.querySelectorAll('.tab').forEach(e=>e.classList.remove('active'));document.querySelectorAll('.tab-content').forEach(e=>e.classList.remove('active'));document.querySelector(`.tab-content#tab-${t}`).classList.add('active');document.querySelector(`.tab:nth-child(${['single','stream','websocket','batch'].indexOf(t)+1})`).classList.add('active');}
function updateModel(){const m=document.getElementById('model-select').value;currentVoices=m.includes('v1.1-zh')?voicesZh:voicesDefault;const s=document.getElementById('lang-select'),p=s.value;s.innerHTML=Object.entries(currentVoices).map(([k,v])=>`<option value="${k}">${v.name}</option>`).join('');currentLang=currentVoices[p]?p:Object.keys(currentVoices)[0];s.value=currentLang;updateVoiceSelect();updateVoiceGrid();}
function updateLang(){currentLang=document.getElementById('lang-select').value;updateVoiceSelect();updateVoiceGrid();}
function updateVoiceSelect(){const voices=currentVoices[currentLang]?.voices||[];document.getElementById('voice-select').innerHTML=voices.map(v=>`<option value="${v}">${v}</option>`).join('');}
function updateStreamVoices(){const m=document.getElementById('stream-model').value;const v=m.includes('v1.1-zh')?voicesZh:voicesDefault;const voices=Object.values(v).flatMap(x=>x.voices).slice(0,50);document.getElementById('stream-voice').innerHTML=voices.map(x=>`<option value="${x}">${x}</option>`).join('');}
function updateWsVoices(){const m=document.getElementById('ws-model').value;const v=m.includes('v1.1-zh')?voicesZh:voicesDefault;const voices=Object.values(v).flatMap(x=>x.voices).slice(0,50);document.getElementById('ws-voice').innerHTML=voices.map(x=>`<option value="${x}">${x}</option>`).join('');}
function updateBatchVoices(){const m=document.getElementById('batch-model').value;const v=m.includes('v1.1-zh')?voicesZh:voicesDefault;const voices=Object.values(v).flatMap(x=>x.voices).slice(0,50);document.getElementById('batch-voice').innerHTML=voices.map(x=>`<option value="${x}">${x}</option>`).join('');}
function updateVoiceGrid(){document.getElementById('lang-tabs').innerHTML=Object.entries(currentVoices).map(([k,v])=>`<div class="lang-tab ${k===currentLang?'active':''}" onclick="selectLang('${k}')">${v.name.split(' ')[0]}</div>`).join('');document.getElementById('voice-grid').innerHTML=(currentVoices[currentLang]?.voices||[]).slice(0,20).map(v=>`<div class="voice-chip" onclick="selectVoice('${v}')">${v}</div>`).join('');}
function selectLang(l){currentLang=l;document.getElementById('lang-select').value=l;updateVoiceSelect();updateVoiceGrid();}
function selectVoice(v){document.getElementById('voice-select').value=v;}
function getParams(){return{text:document.getElementById('text-input').value,voice:document.getElementById('voice-select').value,speed:parseFloat(document.getElementById('speed').value),model:document.getElementById('model-select').value};}

async function generate(){
const btn=document.getElementById('gen-btn'),prog=document.getElementById('progress'),bar=document.getElementById('progress-bar');
btn.disabled=true;prog.style.display='block';bar.style.width='30%';
try{const r=await fetch('/api/tts',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(getParams())});bar.style.width='80%';if(!r.ok)throw new Error((await r.json()).detail);const b=await r.blob(),a=document.getElementById('audio-player');a.src=URL.createObjectURL(b);document.getElementById('audio-container').style.display='block';a.play();bar.style.width='100%';showToast('Done!','success');}catch(e){showToast('Error: '+e.message,'error');}finally{btn.disabled=false;setTimeout(()=>{prog.style.display='none';bar.style.width='0%';},500);}updateStatus();
}

async function streamAudio(){
if(!audioCtx)audioCtx=new(window.AudioContext||window.webkitAudioContext)({sampleRate:24000});
const sb=document.getElementById('stream-btn'),xb=document.getElementById('stop-btn'),st=document.getElementById('stream-status'),mp=document.getElementById('stream-metrics'),ms=document.getElementById('m-status');
sb.style.display='none';xb.style.display='inline-flex';st.textContent='Connecting...';st.className='stream-status active';
mp.style.display='block';ms.textContent='⏳ 正在连接...';ms.className='metric-status streaming';
['m-ttfb','m-ttfp','m-total','m-size'].forEach(id=>document.getElementById(id).textContent='-');
streamCtrl=new AbortController();let n=0,q=[],playing=false,totalBytes=0,startTime=Date.now(),ttfb=0,ttfp=0,totalTimer=null;
function updateTotal(){document.getElementById('m-total').textContent=((Date.now()-startTime)/1000).toFixed(2)+'s';}
totalTimer=setInterval(updateTotal,100);
function playNext(){if(!q.length){playing=false;return;}playing=true;if(!ttfp){ttfp=(Date.now()-startTime)/1000;document.getElementById('m-ttfp').textContent=ttfp.toFixed(3)+'s';}const s=audioCtx.createBufferSource();s.buffer=q.shift();s.connect(audioCtx.destination);s.onended=playNext;s.start();}
try{const p={text:document.getElementById('stream-text').value,voice:document.getElementById('stream-voice').value,speed:parseFloat(document.getElementById('stream-speed').value),model:document.getElementById('stream-model').value};const r=await fetch('/api/tts/stream',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(p),signal:streamCtrl.signal});if(!r.ok)throw new Error('Error');const rd=r.body.getReader();let buf=new Uint8Array(0);
while(true){const{done,value}=await rd.read();if(done)break;if(!ttfb){ttfb=(Date.now()-startTime)/1000;document.getElementById('m-ttfb').textContent=ttfb.toFixed(3)+'s';}totalBytes+=value.length;document.getElementById('m-size').textContent=(totalBytes/1024).toFixed(0)+' KB';const nb=new Uint8Array(buf.length+value.length);nb.set(buf);nb.set(value,buf.length);buf=nb;
while(buf.length>=4){const sz=new DataView(buf.buffer,buf.byteOffset,4).getUint32(0,true);if(buf.length<4+sz)break;const wav=buf.slice(4,4+sz);buf=buf.slice(4+sz);n++;st.textContent=`Chunk ${n}...`;ms.textContent=`🔊 接收中... Chunk ${n}`;audioCtx.decodeAudioData(wav.buffer.slice(wav.byteOffset,wav.byteOffset+wav.byteLength)).then(ab=>{q.push(ab);if(!playing)playNext();});}}
clearInterval(totalTimer);updateTotal();st.textContent=`Done: ${n} chunks`;ms.textContent=`✅ 完成！首字节 ${ttfb.toFixed(3)}s | 首播 ${ttfp.toFixed(3)}s`;ms.className='metric-status';showToast('Stream done!','success');}catch(e){clearInterval(totalTimer);if(e.name!=='AbortError'){showToast('Error','error');st.textContent='Error';ms.textContent='❌ 错误';ms.className='metric-status';}else{st.textContent='Stopped';ms.textContent='⏹ 已停止';ms.className='metric-status';}}finally{sb.style.display='inline-flex';xb.style.display='none';setTimeout(()=>st.className='stream-status',3000);}updateStatus();
}
function stopStream(){if(streamCtrl){streamCtrl.abort();streamCtrl=null;}if(audioCtx){audioCtx.close();audioCtx=null;}}

function connectWS(){if(ws)return;const proto=location.protocol==='https:'?'wss':'ws';const url=`${proto}://${location.host}/ws/tts`;console.log('Connecting to:',url);ws=new WebSocket(url);ws.onopen=()=>{document.getElementById('ws-indicator').classList.add('connected');document.getElementById('ws-status').textContent='Connected';console.log('WS Connected');};ws.onclose=(e)=>{document.getElementById('ws-indicator').classList.remove('connected');document.getElementById('ws-status').textContent='Disconnected';console.log('WS Closed:',e.code,e.reason);ws=null;};ws.onerror=(e)=>{console.error('WS Error:',e);document.getElementById('ws-log').textContent='Connection error';};ws.onmessage=e=>{const d=JSON.parse(e.data),log=document.getElementById('ws-log');if(d.status==='chunk'){log.textContent=`Received chunk ${d.index}`;const audio=new Audio('data:audio/wav;base64,'+d.audio);audio.play();}else if(d.status==='done')log.textContent=`Done: ${d.total_chunks} chunks`;else if(d.status==='error')log.textContent='Error: '+d.error;};}
function disconnectWS(){if(ws){ws.close();ws=null;}}
function sendWS(){if(!ws||ws.readyState!==1){showToast('Not connected','error');return;}const msg={text:document.getElementById('ws-text').value,voice:document.getElementById('ws-voice').value,speed:parseFloat(document.getElementById('ws-speed').value),model:document.getElementById('ws-model').value};ws.send(JSON.stringify(msg));document.getElementById('ws-log').textContent='Sending...';}

async function batchGenerate(){
const txt=document.getElementById('batch-text').value,res=document.getElementById('batch-results'),btn=document.getElementById('batch-btn');
btn.disabled=true;res.innerHTML='<div style="color:var(--text-muted)">Processing...</div>';
try{
let items=JSON.parse(txt);
const defVoice=document.getElementById('batch-voice').value;
const defSpeed=parseFloat(document.getElementById('batch-speed').value);
items=items.map(x=>({...x,voice:x.voice||defVoice,speed:x.speed||defSpeed}));
const r=await fetch('/api/tts/batch',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({items,model:document.getElementById('batch-model').value})});
const d=await r.json();batchResults=d.results;
res.innerHTML=`<div style="margin-bottom:12px;font-weight:600">✅ ${d.success}/${d.total} success</div>`+
d.results.map((x,i)=>`<div style="display:flex;align-items:center;gap:10px;padding:8px;background:var(--bg);border-radius:8px;margin-bottom:6px">
<span style="min-width:60px;font-size:0.8rem">${x.id}</span>
<span style="flex:1;font-size:0.75rem;color:${x.status==='success'?'var(--success)':'var(--error)'}">${x.status}${x.duration?' ('+x.duration.toFixed(2)+'s)':''}</span>
${x.status==='success'?`<button class="btn btn-secondary" style="padding:4px 10px;font-size:0.7rem" onclick="playBatchItem(${i})">▶️</button>
<button class="btn btn-secondary" style="padding:4px 10px;font-size:0.7rem" onclick="downloadBatchItem(${i},'${x.id}')">💾</button>`:''}</div>`).join('');
showToast(`Batch: ${d.success}/${d.total}`,'success');
}catch(e){res.innerHTML=`<div style="color:var(--error)">Error: ${e.message}</div>`;showToast('Error','error');}
finally{btn.disabled=false;}updateStatus();
}
function playBatchItem(i){if(batchResults[i]?.audio){const a=new Audio('data:audio/wav;base64,'+batchResults[i].audio);a.play();}}
function downloadBatchItem(i,id){if(batchResults[i]?.audio){const a=document.createElement('a');a.href='data:audio/wav;base64,'+batchResults[i].audio;a.download=`tts_${id}.wav`;a.click();}}
function playAllBatch(){let i=0;function next(){if(i<batchResults.length&&batchResults[i]?.audio){const a=new Audio('data:audio/wav;base64,'+batchResults[i].audio);a.onended=()=>{i++;next();};a.play();}};next();}
function downloadAllBatch(){batchResults.forEach((x,i)=>{if(x.audio)downloadBatchItem(i,x.id);});}

async function offloadGPU(){await fetch('/api/offload',{method:'POST'});showToast('Released','success');updateStatus();}
async function updateStatus(){try{const d=await(await fetch('/api/status')).json();document.getElementById('stat-device').textContent=d.device.toUpperCase();document.getElementById('stat-memory').textContent=d.gpu?.memory_used||'N/A';document.getElementById('stat-model').textContent=d.model_loaded?'Loaded':'Idle';document.getElementById('gpu-label').textContent=d.device==='cuda'?'GPU':'CPU';}catch(e){}}
function showToast(m,t='info'){const toast=document.getElementById('toast');toast.textContent=m;toast.style.display='block';toast.style.borderColor=t==='error'?'var(--error)':t==='success'?'var(--success)':'var(--primary)';setTimeout(()=>toast.style.display='none',3000);}
init();
</script>
</body>
</html>'''
