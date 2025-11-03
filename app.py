from flask import Flask, request, send_file, render_template_string, jsonify
from gtts import gTTS
import io
from functools import lru_cache
import os

app = Flask(__name__)
LANGUAGES = {"cantonese": "yue", "english": "en"}

HTML = '''
<!DOCTYPE html>
<html>
<head>
  <title>SoundCraft – 理想 AI 語音 v0.7</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>body { background: linear-gradient(to right, #667eea, #764ba2); color: white; padding: 50px; text-align: center; }</style>
</head>
<body>
  <h1 class="display-4">🎙️ SoundCraft 理想版</h1>
  <p class="lead">輸入文字，即生成粵語/英語音頻 - 優化語速 + 無卡死！</p>
  <div class="container mt-4">
    <input type="text" id="text" class="form-control mb-3" placeholder="輸入內容... (e.g. 理想平台測試！)" style="max-width: 500px; margin: auto;">
    <select id="lang" class="form-select mb-3" style="max-width: 300px; margin: auto;">
      <option value="cantonese">粵語</option>
      <option value="english">English</option>
    </select>
    <input type="range" id="speed" min="0.5" max="1.5" value="1" class="form-range mb-3" style="max-width: 300px; margin: auto;"><label>語速 (0.5=慢, 1.5=快)</label>
    <button onclick="generate()" class="btn btn-primary btn-lg mb-3">生成音頻</button>
    <button onclick="shareToX()" class="btn btn-info btn-lg" id="shareBtn" style="display:none;">分享到 x.com</button>
    <div id="result" class="mt-4"></div>
  </div>
  <script>
    let audioUrl = '';
    function generate() {
      const text = document.getElementById('text').value;
      const lang = document.getElementById('lang').value;
      const speed = document.getElementById('speed').value;
      if (!text) return alert("請輸入文字！");
      document.getElementById('result').innerHTML = '<div class="spinner-border text-light"></div> 生成中... (timeout 10s)';
      const controller = new AbortController();
      setTimeout(() => controller.abort(), 10000);
      fetch('/generate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({text, lang, speed: parseFloat(speed)}),
        signal: controller.signal
      }).then(res => {
        if (!res.ok) throw new Error('生成失敗');
        return res.blob();
      }).then(blob => {
        audioUrl = URL.createObjectURL(blob);
        document.getElementById('result').innerHTML = 
          `<audio controls class="mt-3" src="${audioUrl}"></audio><br>
           <a href="${audioUrl}" download="soundcraft.mp3" class="btn btn-success mt-2">下載 MP3</a>
           <p class="text-success">成功！語速: ${speed}x</p>`;
        document.getElementById('shareBtn').style.display = 'inline-block';
      }).catch(err => {
        document.getElementById('result').innerHTML = `<p class="text-danger">錯誤: ${err.message}。重試？</p><button onclick="generate()" class="btn btn-warning">重試</button>`;
      });
    }
    function shareToX() {
      if (navigator.share) {
        navigator.share({title: 'SoundCraft AI', text: '試下呢個理想音頻！', url: window.location.href});
      } else {
        alert('分享連結: ' + window.location.href);
      }
    }
  </script>
</body>
</html>
'''

@lru_cache(maxsize=10)
def _tts_generate(text, lang_code, slow):
    tts = gTTS(text=text, lang=lang_code, slow=slow)
    audio_buffer = io.BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)
    return audio_buffer.getvalue()

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        lang_code = LANGUAGES.get(data['lang'], 'en')
        text = data.get('text', '')
        speed_value = float(data.get('speed', 1.0))
        slow = (speed_value < 1.0)
        audio_bytes = _tts_generate(text, lang_code, slow)
        return send_file(
            io.BytesIO(audio_bytes),
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name="soundcraft.mp3"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)# SoundCraft-Ideal
