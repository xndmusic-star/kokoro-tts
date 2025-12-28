# 🚀 Kokoro TTS 流式延迟优化指南

本文档详细记录了将 Kokoro TTS 流式播放延迟从 **2秒+** 优化到 **~100ms** 的完整过程和经验。

## 📊 优化成果

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 首字节时间 (TTFB) | ~500ms | ~50ms | **10x** |
| 首播时间 | 2s+ | ~100ms | **20x** |
| 首 Chunk 大小 | 436KB | 71.5KB | **6x** |
| Chunk 数量 | 1 | 4-6 | 更细粒度 |

## 🔍 问题分析

### 现象
- 首字节显示 0.5s 到达
- 但实际播放要等 2s+
- 用户体验差，感觉卡顿

### 排查过程

**1. 最初怀疑 Cloudflare 缓冲**

```bash
# 对比测试
本地 TTFB: 0.1s
Cloudflare TTFB: 0.3s
```

结论：Cloudflare 只增加 ~200ms 网络延迟（物理传输时间），不是主因。

**2. 发现真正原因：Chunk 太大**

```bash
# 修复前 - 整段文本生成一个巨大 chunk
Chunk 1: 436KB, 需要 ~2s 才能完整接收

# 修复后 - 按句子分割成多个小 chunk
Chunk 1: 71.5KB, ~100ms 完整接收
Chunk 2: 80.9KB
Chunk 3: 87.9KB
...
```

### 根本原因

Kokoro pipeline 默认使用 `split_pattern=r'\n+'`（按换行符分割），导致整段文本被当作一个单元处理，生成一个巨大的音频 chunk。

## 🛠️ 优化措施

### 1. 按句子/子句分割（最关键）

**原理**：将长文本按标点符号分割成小段，每段独立生成音频并立即发送。

```python
# ❌ 修复前 - 默认按换行分割
for result in pipeline(text, voice=voice, speed=speed):
    # split_pattern 默认是 r'\n+'
    yield audio_chunk

# ✅ 修复后 - 按句子和子句分割
for result in pipeline(
    text, 
    voice=voice, 
    speed=speed, 
    split_pattern=r'[.!?。！？,，;；:：]+'
):
    yield audio_chunk
```

**支持的分割符**：
- 英文：`. ! ? , ; :`
- 中文：`。！？，；：`

**效果**：首 chunk 从 436KB 降到 71.5KB，接收时间从 2s 降到 100ms。

### 2. 模型预热（消除冷启动）

**原理**：服务启动时预先加载模型和 voice 文件，避免首次请求的额外延迟。

```python
def warmup(self):
    """Preload default model and voice to reduce first request latency"""
    print("🔥 Warming up model...")
    pipeline = self.get_pipeline('a', 'hexgrad/Kokoro-82M')
    # 生成一段短音频，完全预热模型
    for _ in pipeline("Hello", voice='af_heart', speed=1.0):
        pass
    print("✅ Model warmed up!")
```

**效果**：冷启动 93ms → 热启动 56ms

### 3. 前端非阻塞音频解码

**原理**：使用 `.then()` 替代 `await`，让音频解码和数据接收并行进行。

```javascript
// ❌ 修复前 - 阻塞式解码
const ab = await audioCtx.decodeAudioData(wav.buffer);
q.push(ab);
if (!playing) playNext();

// ✅ 修复后 - 非阻塞式解码
audioCtx.decodeAudioData(wav.buffer).then(ab => {
    q.push(ab);
    if (!playing) playNext();
});
```

**效果**：解码不再阻塞下一个 chunk 的接收，首播时间更接近首字节时间。

### 4. AudioContext 自动恢复

**原理**：浏览器安全策略会在无用户交互时暂停 AudioContext，需要显式恢复。

```javascript
async function streamAudio() {
    if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)({
            sampleRate: 24000
        });
    }
    // 关键：恢复被暂停的 AudioContext
    if (audioCtx.state === 'suspended') {
        await audioCtx.resume();
    }
    // ... 开始流式播放
}
```

### 5. 响应头禁用缓冲

**原理**：防止 Nginx/代理服务器缓冲响应数据。

```python
return StreamingResponse(
    generate(), 
    media_type="application/octet-stream",
    headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no"  # 禁用 nginx 缓冲
    }
)
```

## ⚡ 性能极限

### 无法再优化的部分

| 限制 | 原因 | 数值 |
|------|------|------|
| TTS 生成时间 | 模型推理的最小时间 | ~50ms |
| 网络延迟 | 物理传输距离 | ~100-200ms |

### 理论最优值

- **本地环境**：~50ms TTFB（模型生成时间）
- **通过 CDN**：~250-300ms TTFB（模型 + 网络）

## 🧪 调试命令

### 测试 TTFB

```bash
curl -w "TTFB: %{time_starttransfer}s, Total: %{time_total}s\n" \
  -o /dev/null -s -X POST \
  http://localhost:8300/api/tts/stream \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world.","voice":"af_heart"}'
```

### 分析 Chunk 大小和时间

```python
import time, requests, struct

text = "Hello world, how are you. I hope you are doing well."
start = time.time()

with requests.post("http://localhost:8300/api/tts/stream", 
                   json={"text": text, "voice": "af_heart"}, stream=True) as r:
    buf = b''
    chunk_num = 0
    for data in r.iter_content(chunk_size=4096):
        buf += data
        while len(buf) >= 4:
            sz = struct.unpack('<I', buf[:4])[0]
            if len(buf) < 4 + sz:
                break
            chunk_num += 1
            elapsed = time.time() - start
            print(f"Chunk {chunk_num}: {elapsed*1000:.0f}ms, {sz/1024:.1f}KB")
            buf = buf[4+sz:]
```

### 对比本地 vs CDN

```bash
echo "=== 本地 ==="
for i in {1..3}; do
  curl -w "%{time_starttransfer}s\n" -o /dev/null -s -X POST \
    http://localhost:8300/api/tts/stream \
    -H "Content-Type: application/json" \
    -d '{"text":"Test.","voice":"af_heart"}'
done

echo "=== CDN ==="
for i in {1..3}; do
  curl -w "%{time_starttransfer}s\n" -o /dev/null -s -X POST \
    https://your-domain.com/api/tts/stream \
    -H "Content-Type: application/json" \
    -d '{"text":"Test.","voice":"af_heart"}'
done
```

## 📝 关键经验总结

1. **分割粒度决定延迟** - chunk 越小，首播越快
2. **模型预热很重要** - 首次加载 voice 文件有额外开销
3. **前端不能阻塞** - 解码和接收必须并行
4. **~50ms 是模型硬限制** - TTS 生成的最短时间
5. **网络延迟是物理限制** - CDN 增加的延迟是正常的传输时间
6. **不要怀疑 CDN** - 先检查 chunk 大小和服务端逻辑

## 🔧 配置建议

### 生产环境

```yaml
# docker-compose.yml
services:
  kokoro-tts:
    image: neosun/kokoro-tts:v1.1.0
    environment:
      - GPU_IDLE_TIMEOUT=600  # GPU 空闲释放时间
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

### Nginx 配置（如果使用）

```nginx
location /api/tts/stream {
    proxy_pass http://kokoro-tts:8300;
    proxy_buffering off;           # 禁用缓冲
    proxy_cache off;               # 禁用缓存
    proxy_http_version 1.1;
    proxy_set_header Connection "";
}
```

### Cloudflare 配置

- 确保 WebSocket 支持已开启
- 流式响应会自动处理，无需特殊配置
- 预期增加 100-200ms 网络延迟（正常）

---

*最后更新: 2025-01*
