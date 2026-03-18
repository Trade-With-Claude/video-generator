"""Simple web UI for configuring and generating videos."""

from __future__ import annotations

import os
import tempfile
import threading
import webbrowser
from pathlib import Path

from flask import Flask, jsonify, request

from video_generator.generate import generate, get_audio_duration
from video_generator.presets import AVAILABLE_MOODS, parse_hex_color

app = Flask(__name__)

# Store uploaded audio path
_audio_store: dict[str, Path] = {}

HTML = """<!DOCTYPE html>
<html>
<head>
<title>Video Generator</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, system-ui, sans-serif; background: #111; color: #eee; display: flex; justify-content: center; padding: 40px 20px; }
  .container { max-width: 480px; width: 100%; }
  h1 { font-size: 22px; margin-bottom: 30px; font-weight: 500; }
  label { display: block; font-size: 13px; color: #999; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 1px; }
  select, input[type=number] { width: 100%; background: #222; border: 1px solid #333; color: #eee; padding: 10px 12px; border-radius: 6px; font-size: 15px; margin-bottom: 20px; }
  select:focus, input:focus { outline: none; border-color: #555; }
  .color-row { display: flex; gap: 10px; margin-bottom: 20px; align-items: flex-end; }
  .color-slot { flex: 1; text-align: center; }
  .color-slot input[type=color] { width: 100%; height: 50px; border: 2px solid #333; border-radius: 8px; cursor: pointer; background: none; padding: 2px; }
  .color-slot input[type=color]::-webkit-color-swatch-wrapper { padding: 0; }
  .color-slot input[type=color]::-webkit-color-swatch { border: none; border-radius: 5px; }
  .color-slot button { background: none; border: none; color: #666; cursor: pointer; font-size: 18px; margin-top: 4px; }
  .color-slot button:hover { color: #f55; }
  .add-color { background: #222; border: 2px dashed #444; color: #666; padding: 10px; border-radius: 8px; cursor: pointer; font-size: 14px; margin-bottom: 20px; width: 100%; }
  .add-color:hover { border-color: #666; color: #999; }
  .row { display: flex; gap: 12px; }
  .row > div { flex: 1; }
  button.generate { width: 100%; padding: 14px; background: #2563eb; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 500; cursor: pointer; margin-top: 10px; }
  button.generate:hover { background: #1d4ed8; }
  button.generate:disabled { background: #333; color: #666; cursor: not-allowed; }
  .status { margin-top: 16px; padding: 12px; background: #1a1a2e; border-radius: 6px; font-size: 13px; color: #aaa; display: none; }
  .status.show { display: block; }
  .status.done { border-left: 3px solid #22c55e; }
  .status.error { border-left: 3px solid #ef4444; }
  .check { display: flex; align-items: center; gap: 8px; margin-bottom: 16px; }
  .check input { width: 16px; height: 16px; }
  .check label { margin: 0; text-transform: none; font-size: 14px; color: #ccc; }
  .drop-zone { border: 2px dashed #444; border-radius: 8px; padding: 20px; text-align: center; color: #666; margin-bottom: 20px; cursor: pointer; transition: all 0.2s; }
  .drop-zone:hover, .drop-zone.dragover { border-color: #2563eb; color: #999; background: #1a1a2e; }
  .drop-zone.has-file { border-color: #22c55e; color: #aaa; border-style: solid; }
  .drop-zone .filename { color: #22c55e; font-weight: 500; }
  .drop-zone .duration { color: #999; font-size: 13px; }
  .drop-zone .remove { color: #f55; cursor: pointer; margin-left: 8px; }
</style>
</head>
<body>
<div class="container">
  <h1>Video Generator</h1>

  <label>Audio File</label>
  <div class="drop-zone" id="dropZone" onclick="document.getElementById('audioInput').click()">
    Drop audio file here or click to browse
    <input type="file" id="audioInput" accept="audio/*,.wav,.mp3,.flac,.ogg,.m4a,.aac" style="display:none">
  </div>

  <label>Mood</label>
  <select id="mood">
    <option value="ambient" selected>Ambient</option>
    <option value="focus">Focus</option>
    <option value="trippy">Trippy</option>
  </select>

  <label>Colors</label>
  <div class="color-row" id="colors">
    <div class="color-slot">
      <input type="color" value="#3cb4dc">
      <br><button onclick="removeColor(this)">&times;</button>
    </div>
    <div class="color-slot">
      <input type="color" value="#0055ff">
      <br><button onclick="removeColor(this)">&times;</button>
    </div>
    <div class="color-slot">
      <input type="color" value="#8833cc">
      <br><button onclick="removeColor(this)">&times;</button>
    </div>
  </div>
  <button class="add-color" onclick="addColor()">+ Add Color</button>

  <div class="check">
    <input type="checkbox" id="useColors">
    <label for="useColors">Use custom colors (uncheck for preset defaults)</label>
  </div>

  <div class="row">
    <div>
      <label>Duration (sec)</label>
      <input type="number" id="duration" value="300" min="5">
    </div>
    <div>
      <label>Loop length (sec)</label>
      <input type="number" id="loop" value="45" min="3">
    </div>
  </div>

  <div class="row">
    <div>
      <label>Seed (0 = random)</label>
      <input type="number" id="seed" value="0" min="0">
    </div>
  </div>

  <button class="generate" id="genBtn" onclick="doGenerate()">Generate</button>
  <div class="status" id="status"></div>
</div>

<script>
let audioId = null;

// Drag and drop
const dropZone = document.getElementById('dropZone');
const audioInput = document.getElementById('audioInput');

dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', e => { e.preventDefault(); dropZone.classList.remove('dragover'); if (e.dataTransfer.files.length) uploadAudio(e.dataTransfer.files[0]); });
audioInput.addEventListener('change', e => { if (e.target.files.length) uploadAudio(e.target.files[0]); });

async function uploadAudio(file) {
  dropZone.innerHTML = 'Uploading...';
  const form = new FormData();
  form.append('audio', file);
  try {
    const res = await fetch('/upload-audio', { method: 'POST', body: form });
    const data = await res.json();
    if (data.ok) {
      audioId = data.id;
      const mins = Math.floor(data.duration / 60);
      const secs = Math.round(data.duration % 60);
      dropZone.innerHTML = `<span class="filename">${data.name}</span> <span class="duration">${mins}m ${secs}s</span> <span class="remove" onclick="removeAudio(event)">&times;</span>`;
      dropZone.classList.add('has-file');
      document.getElementById('duration').value = Math.ceil(data.duration);
    } else {
      dropZone.innerHTML = 'Error: ' + data.error;
    }
  } catch(e) {
    dropZone.innerHTML = 'Upload failed: ' + e.message;
  }
}

function removeAudio(e) {
  e.stopPropagation();
  audioId = null;
  dropZone.innerHTML = 'Drop audio file here or click to browse';
  dropZone.classList.remove('has-file');
}

function addColor() {
  const row = document.getElementById('colors');
  const slot = document.createElement('div');
  slot.className = 'color-slot';
  const hue = Math.floor(Math.random() * 360);
  slot.innerHTML = `<input type="color" value="${hslToHex(hue, 70, 55)}"><br><button onclick="removeColor(this)">&times;</button>`;
  row.appendChild(slot);
}

function removeColor(btn) {
  const row = document.getElementById('colors');
  if (row.children.length > 1) btn.parentElement.remove();
}

function hslToHex(h, s, l) {
  s /= 100; l /= 100;
  const a = s * Math.min(l, 1-l);
  const f = n => { const k = (n + h/30) % 12; return l - a * Math.max(Math.min(k-3, 9-k, 1), -1); };
  return '#' + [f(0),f(8),f(4)].map(x => Math.round(x*255).toString(16).padStart(2,'0')).join('');
}

function getColors() {
  if (!document.getElementById('useColors').checked) return null;
  return [...document.querySelectorAll('#colors input[type=color]')].map(i => i.value.slice(1));
}

async function doGenerate() {
  const btn = document.getElementById('genBtn');
  const status = document.getElementById('status');
  btn.disabled = true;
  btn.textContent = 'Generating...';
  status.className = 'status show';
  status.textContent = audioId
    ? 'Rendering video + merging audio... this may take a few minutes.'
    : 'Rendering video... this may take a few minutes.';

  try {
    const res = await fetch('/generate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        mood: document.getElementById('mood').value,
        duration: parseFloat(document.getElementById('duration').value),
        loop_duration: parseFloat(document.getElementById('loop').value),
        seed: parseInt(document.getElementById('seed').value) || 0,
        colors: getColors(),
        audio_id: audioId,
      })
    });
    const data = await res.json();
    if (data.ok) {
      status.className = 'status show done';
      status.textContent = 'Done! ' + data.output + ' (' + data.size_mb + ' MB)';
    } else {
      status.className = 'status show error';
      status.textContent = 'Error: ' + data.error;
    }
  } catch(e) {
    status.className = 'status show error';
    status.textContent = 'Error: ' + e.message;
  }
  btn.disabled = false;
  btn.textContent = 'Generate';
}
</script>
</body>
</html>"""


@app.route("/")
def index():
    return HTML


@app.route("/upload-audio", methods=["POST"])
def upload_audio():
    try:
        file = request.files.get("audio")
        if not file or not file.filename:
            return jsonify(ok=False, error="No file provided")

        # Save to temp file
        suffix = Path(file.filename).suffix
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir="output")
        file.save(tmp.name)
        tmp.close()

        duration = get_audio_duration(tmp.name)
        audio_id = os.path.basename(tmp.name)
        _audio_store[audio_id] = Path(tmp.name)

        return jsonify(ok=True, id=audio_id, name=file.filename, duration=duration)
    except Exception as e:
        return jsonify(ok=False, error=str(e))


@app.route("/generate", methods=["POST"])
def api_generate():
    try:
        data = request.json
        colors = None
        if data.get("colors"):
            colors = [parse_hex_color(c) for c in data["colors"]]

        seed = data.get("seed", 0)
        if seed == 0:
            seed = None

        audio_path = None
        audio_id = data.get("audio_id")
        if audio_id and audio_id in _audio_store:
            audio_path = _audio_store[audio_id]

        output = generate(
            mood=data.get("mood", "ambient"),
            target_duration=data.get("duration", 300),
            loop_duration=data.get("loop_duration", 45),
            seed=seed,
            colors=colors,
            audio=audio_path,
        )

        # Clean up uploaded audio
        if audio_id and audio_id in _audio_store:
            _audio_store[audio_id].unlink(missing_ok=True)
            del _audio_store[audio_id]

        size_mb = f"{output.stat().st_size / 1024 / 1024:.1f}"
        return jsonify(ok=True, output=str(output), size_mb=size_mb)
    except Exception as e:
        return jsonify(ok=False, error=str(e))


def run_ui(port: int = 5555) -> None:
    """Launch the web UI."""
    Path("output").mkdir(exist_ok=True)
    print(f"\n  Video Generator UI -> http://localhost:{port}\n")
    threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{port}")).start()
    app.run(host="127.0.0.1", port=port, debug=False)


if __name__ == "__main__":
    run_ui()
