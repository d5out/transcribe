#!/usr/bin/env python3
"""
Transcribe — Local AI Audio Transcription App
Uses pywebview for native window, MLX Whisper for transcription.
Double-click to run. No browser or server needed.
"""

from pathlib import Path

import mlx_whisper
import webview

SUPPORTED_EXTENSIONS = ("m4a", "mp3", "wav", "flac", "ogg", "webm")

MODELS = {
    "tiny": "mlx-community/whisper-tiny-mlx",
    "base": "mlx-community/whisper-base-mlx",
    "small": "mlx-community/whisper-small-mlx",
    "medium": "mlx-community/whisper-medium-mlx",
    "large": "mlx-community/whisper-large-v3-mlx",
}


class Api:
    """Python API exposed to the JS frontend via pywebview."""

    def __init__(self, window):
        self._window = window

    def pick_files(self):
        """Open native file picker and return selected paths."""
        file_types = ("Audio Files (*.m4a;*.mp3;*.wav;*.flac;*.ogg;*.webm)",)
        result = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=True,
            file_types=file_types,
        )
        if result:
            return [str(p) for p in result]
        return []

    def pick_folder(self):
        """Open native folder picker and return selected path."""
        result = self._window.create_file_dialog(webview.FOLDER_DIALOG)
        if result:
            return str(result[0])
        return ""

    def transcribe(self, file_path, model_key="large", output_name="", output_dir=""):
        """Transcribe a single file."""
        try:
            model_path = MODELS.get(model_key, MODELS["large"])
            result = mlx_whisper.transcribe(
                file_path,
                path_or_hf_repo=model_path,
                verbose=False,
            )
            text = result["text"].strip()
            language = result.get("language", "unknown")

            # Determine output path
            original = Path(file_path)
            stem = output_name.strip() if output_name.strip() else original.stem
            parent = Path(output_dir) if output_dir.strip() else original.parent
            txt_path = parent / f"{stem}.txt"
            txt_path.write_text(text)

            return {
                "status": "done",
                "text": text,
                "language": language,
                "saved_to": str(txt_path),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Transcribe</title>
<style>
  :root { --bg: #0f0f0f; --card: #1a1a1a; --border: #2a2a2a; --text: #e0e0e0; --accent: #6c8cff; --accent2: #4a6adf; --green: #4caf50; --red: #ef5350; }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', system-ui, sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; -webkit-user-select: none; user-select: none; }
  .container { max-width: 720px; margin: 0 auto; padding: 32px 20px; }
  h1 { font-size: 22px; font-weight: 600; margin-bottom: 6px; }
  .subtitle { color: #888; font-size: 13px; margin-bottom: 24px; }

  .pick-area { border: 2px dashed var(--border); border-radius: 12px; padding: 36px 24px; text-align: center; cursor: pointer; transition: all 0.2s; margin-bottom: 16px; }
  .pick-area:hover { border-color: var(--accent); background: rgba(108,140,255,0.05); }
  .pick-label { font-size: 15px; color: #888; }
  .pick-label strong { color: var(--accent); }
  .file-list { margin-top: 10px; font-size: 13px; color: var(--accent); }
  .formats { font-size: 11px; color: #555; margin-top: 6px; }

  /* Settings */
  .settings { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 14px 16px; margin-bottom: 16px; display: flex; flex-direction: column; gap: 10px; }
  .setting-row { display: flex; align-items: center; gap: 10px; }
  .setting-label { font-size: 12px; color: #888; min-width: 80px; }
  select, .text-input { background: var(--bg); color: var(--text); border: 1px solid var(--border); border-radius: 6px; padding: 7px 10px; font-size: 13px; flex: 1; }
  .text-input { font-family: inherit; }
  .text-input::placeholder { color: #555; }
  .folder-btn { background: var(--border); color: var(--text); border: none; border-radius: 6px; padding: 7px 12px; font-size: 12px; cursor: pointer; white-space: nowrap; }
  .folder-btn:hover { background: #444; }
  .folder-display { font-size: 12px; color: var(--accent); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }

  .controls { display: flex; gap: 12px; align-items: center; margin-bottom: 20px; }
  .btn { background: var(--accent); color: #fff; border: none; border-radius: 8px; padding: 10px 28px; font-size: 14px; font-weight: 600; cursor: pointer; transition: background 0.2s; }
  .btn:hover { background: var(--accent2); }
  .btn:disabled { opacity: 0.4; cursor: not-allowed; }

  .results { display: flex; flex-direction: column; gap: 14px; }
  .result-card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 14px 16px; }
  .result-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
  .result-filename { font-weight: 600; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 70%; }
  .status-badge { font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 500; white-space: nowrap; }
  .status-badge.queued { background: #333; color: #aaa; }
  .status-badge.transcribing { background: rgba(108,140,255,0.15); color: var(--accent); }
  .status-badge.done { background: rgba(76,175,80,0.15); color: var(--green); }
  .status-badge.error { background: rgba(239,83,80,0.15); color: var(--red); }
  .result-meta { font-size: 11px; color: #888; margin-bottom: 4px; }
  .result-text { font-size: 13px; line-height: 1.6; white-space: pre-wrap; margin-top: 6px; max-height: 260px; overflow-y: auto; -webkit-user-select: text; user-select: text; }
  .copy-btn { background: var(--border); color: var(--text); border: none; border-radius: 6px; padding: 4px 10px; font-size: 11px; cursor: pointer; margin-top: 6px; }
  .copy-btn:hover { background: #444; }
  .spinner { display: inline-block; width: 12px; height: 12px; border: 2px solid var(--accent); border-top-color: transparent; border-radius: 50%; animation: spin 0.8s linear infinite; vertical-align: middle; margin-right: 4px; }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
</head>
<body>
<div class="container">
  <h1>Transcribe</h1>
  <p class="subtitle">Local AI transcription on Apple Silicon</p>

  <div class="pick-area" id="pickArea">
    <p class="pick-label"><strong>Click to select audio files</strong></p>
    <p class="formats">m4a &middot; mp3 &middot; wav &middot; flac &middot; ogg &middot; webm</p>
    <div class="file-list" id="fileList"></div>
  </div>

  <div class="settings">
    <div class="setting-row">
      <span class="setting-label">Quality</span>
      <select id="modelSelect">
        <option value="large" selected>Large &mdash; best quality, slowest</option>
        <option value="medium">Medium &mdash; balanced</option>
        <option value="small">Small &mdash; fast</option>
        <option value="base">Base &mdash; faster, lower accuracy</option>
        <option value="tiny">Tiny &mdash; fastest, lowest accuracy</option>
      </select>
    </div>
    <div class="setting-row">
      <span class="setting-label">Rename</span>
      <input class="text-input" id="renameInput" type="text" placeholder="Leave blank to keep original filename">
    </div>
    <div class="setting-row">
      <span class="setting-label">Save to</span>
      <span class="folder-display" id="folderDisplay">Same folder as audio file</span>
      <button class="folder-btn" id="folderBtn">Choose folder</button>
      <button class="folder-btn" id="folderReset" style="display:none">Reset</button>
    </div>
  </div>

  <div class="controls">
    <button class="btn" id="transcribeBtn" disabled>Transcribe</button>
  </div>

  <div class="results" id="results"></div>
</div>

<script>
let selectedFiles = [];
let outputDir = '';

const pickArea = document.getElementById('pickArea');
const fileList = document.getElementById('fileList');
const transcribeBtn = document.getElementById('transcribeBtn');
const modelSelect = document.getElementById('modelSelect');
const renameInput = document.getElementById('renameInput');
const folderBtn = document.getElementById('folderBtn');
const folderReset = document.getElementById('folderReset');
const folderDisplay = document.getElementById('folderDisplay');
const results = document.getElementById('results');

pickArea.addEventListener('click', async () => {
  const paths = await pywebview.api.pick_files();
  if (paths && paths.length > 0) {
    selectedFiles = paths;
    fileList.textContent = paths.map(p => p.split('/').pop()).join(', ');
    transcribeBtn.disabled = false;
    // If single file, pre-fill rename with stem
    if (paths.length === 1) {
      const name = paths[0].split('/').pop();
      renameInput.placeholder = name.substring(0, name.lastIndexOf('.')) || name;
    } else {
      renameInput.placeholder = 'Only applies to single file';
    }
  }
});

folderBtn.addEventListener('click', async () => {
  const dir = await pywebview.api.pick_folder();
  if (dir) {
    outputDir = dir;
    folderDisplay.textContent = dir;
    folderReset.style.display = 'inline-block';
  }
});

folderReset.addEventListener('click', () => {
  outputDir = '';
  folderDisplay.textContent = 'Same folder as audio file';
  folderReset.style.display = 'none';
});

transcribeBtn.addEventListener('click', async () => {
  transcribeBtn.disabled = true;
  const model = modelSelect.value;
  const rename = selectedFiles.length === 1 ? renameInput.value.trim() : '';
  const files = [...selectedFiles];
  selectedFiles = [];
  fileList.textContent = '';

  for (const filePath of files) {
    const filename = filePath.split('/').pop();
    const card = createCard(filename);
    results.prepend(card.el);
    card.setStatus('transcribing');

    const result = await pywebview.api.transcribe(filePath, model, rename, outputDir);
    if (result.status === 'done') {
      card.setStatus('done');
      card.setText(result.text, result.language, result.saved_to);
    } else {
      card.setStatus('error');
      card.setError(result.error);
    }
  }
  transcribeBtn.disabled = false;
});

function createCard(filename) {
  const el = document.createElement('div');
  el.className = 'result-card';
  el.innerHTML = '<div class="result-header"><span class="result-filename"></span><span class="status-badge queued">Queued</span></div><div class="result-meta"></div>';
  el.querySelector('.result-filename').textContent = filename;
  const badge = el.querySelector('.status-badge');
  const meta = el.querySelector('.result-meta');

  return {
    el,
    setStatus(s) {
      badge.className = 'status-badge ' + s;
      if (s === 'transcribing') badge.innerHTML = '<span class="spinner"></span> Transcribing...';
      else if (s === 'done') badge.textContent = 'Done';
      else if (s === 'error') badge.textContent = 'Error';
    },
    setText(text, lang, savedTo) {
      meta.textContent = 'Language: ' + lang + (savedTo ? ' · Saved: ' + savedTo : '');
      const t = document.createElement('div');
      t.className = 'result-text';
      t.textContent = text;
      el.appendChild(t);
      const btn = document.createElement('button');
      btn.className = 'copy-btn';
      btn.textContent = 'Copy text';
      btn.onclick = () => { navigator.clipboard.writeText(text); btn.textContent = 'Copied!'; setTimeout(() => btn.textContent = 'Copy text', 1500); };
      el.appendChild(btn);
    },
    setError(msg) { meta.textContent = msg; }
  };
}
</script>
</body>
</html>
"""


def main():
    window = webview.create_window(
        "Transcribe",
        html=HTML,
        width=780,
        height=680,
        min_size=(500, 450),
    )
    api = Api(window)
    window.expose(api.pick_files, api.pick_folder, api.transcribe)
    webview.start()


if __name__ == "__main__":
    main()
