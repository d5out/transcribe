# transcribe

**Local AI audio transcription for macOS / Apple Silicon — with optional speaker diarization.**

Transcribe meetings, interviews, voice notes, and podcasts straight on your Mac.
No cloud, no uploads, no per-minute fees. Your audio never leaves your machine.

---

## Features

- 🎙️ **High-quality transcription** using [MLX Whisper](https://github.com/ml-explore/mlx) —
  the Whisper model re-implemented for Apple Silicon, so it runs fast on the GPU.
- 🗣️ **Optional speaker diarization** using [pyannote.audio](https://github.com/pyannote/pyannote-audio) —
  label each segment with who said it.
- 🧠 **Choose your accuracy / speed trade-off** — tiny, base, small, medium, or large Whisper model.
- 🖥️ Ships with **both a CLI (`transcribe.py`) and a native desktop app (`app.py`, via pywebview)**.
- 🔐 **Runs 100 % locally.** No audio ever leaves your computer.
- 🌍 **99+ languages** auto-detected, plus optional language forcing.

---

## Quick start

```bash
# Clone
git clone https://github.com/d5out/transcribe.git
cd transcribe

# Install (basic transcription only — no HuggingFace needed)
pip install -r requirements.txt

# Transcribe a file
python3 transcribe.py /path/to/audio.m4a -m large
```

### Supported formats

`m4a` &middot; `mp3` &middot; `wav` &middot; `flac` &middot; `ogg` &middot; `webm`

### Common flags

| Flag | What it does |
|---|---|
| `-m {tiny,base,small,medium,large}` | Whisper model size. Default `small`. |
| `-o DIR` | Write transcripts to `DIR` instead of the audio's folder. |
| `-l LANG` | Force a language instead of auto-detecting (e.g. `-l english`). |
| `--diarize` | Label speakers (requires optional setup — see below). |
| `--speakers N` | Tell the diarizer exactly how many speakers there are. |
| `--min-speakers N --max-speakers M` | Give the diarizer a range when unsure. |

---

## Speaker diarization (optional)

To label *who* said what, not just *what* was said:

```bash
pip install -r requirements-diarize.txt
```

Then follow the full step-by-step setup in **[SETUP_DIARIZATION.md](SETUP_DIARIZATION.md)** —
it walks you through the free Hugging Face account, access token, model-term
acceptance, and **secure token storage via macOS Keychain** (recommended)
so no plaintext secret lives in your shell config.

Once set up:

```bash
python3 transcribe.py meeting.m4a -m large --diarize --speakers 3
```

Output looks like this:

```
[SPEAKER_00 00:00.000 --> 00:14.440]
Hello, how are you?

[SPEAKER_01 00:14.440 --> 00:22.000]
Good, thanks. You?
```

Run in an interactive terminal and you'll get an optional prompt to rename
`SPEAKER_00` / `SPEAKER_01` to real names right after diarization.

> 💡 **Tip for figuring out who is who**: when people greet each other at
> the start — e.g. someone says *"Hi Alice"* — that person is **not** Alice;
> Alice is whoever is being greeted (usually the next speaker).

---

## Desktop app

A minimal native window wrapper is also included:

```bash
python3 app.py
```

Drag a file in, pick a model, click Transcribe. No browser required.

---

## How it works

| Stage | Component |
|---|---|
| Transcription | `mlx-whisper` (Apple Silicon–optimised Whisper) |
| Speaker separation | `pyannote.audio` 3.1 / 4.x (auto-compatible) |
| Acceleration | Metal Performance Shaders (MPS) when available |
| Desktop UI | `pywebview` native window |

All models are downloaded once and cached under `~/.cache/huggingface/`.
Subsequent runs are fully offline.

---

## Roadmap / continuously updated

This project tracks changes in the upstream ecosystem and will be updated as
things evolve. Active areas:

- **pyannote.audio** — new versions periodically change the API (e.g. the
  `use_auth_token` → `token` rename in 4.x). The script is kept compatible
  across recent versions.
- **Whisper models** — new MLX-converted checkpoints (larger, multilingual,
  domain-tuned) will be added to the `MODELS` map as they appear.
- **Torch / torchaudio** — version pinning strategy in
  `requirements-diarize.txt` updated when ABI breakages surface.
- **No-HuggingFace diarization backend** — exploring an alternative
  (e.g. `sherpa-onnx` / `resemblyzer`) so public users can get speaker
  labels with zero sign-up.
- **Auto-identify speakers by name** — experimental: match "Hi X" openings
  to cluster labels so the output is pre-labelled without prompting.
- **Timestamped word-level alignment** — optional word-level timestamps
  via `whisperx`-style forced alignment.

Open an issue if you hit breakage with a newer dependency version and
it's not yet handled.

---

## Troubleshooting

See **[SETUP_DIARIZATION.md § Troubleshooting](SETUP_DIARIZATION.md#troubleshooting)**
for known errors, including the `torch` / `torchaudio` ABI mismatch and
the pyannote API rename.

---

## Privacy note

Nothing you transcribe is ever uploaded. Models are fetched from Hugging Face
once at install time, but the audio itself is processed entirely on your
device. The only outbound traffic during normal runs is for anonymous
authenticity checks against the Hugging Face Hub when a model hasn't been
cached yet.

---

## ⭐ Star this repo

If this saves you a trip to a paid transcription service, please star the
repo — it helps others find it and keeps the project prioritised for
continued updates as the underlying libraries evolve.

👉 [**github.com/d5out/transcribe**](https://github.com/d5out/transcribe) — click ⭐ in the top-right.
