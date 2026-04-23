---
name: transcribe
description: Transcribe audio files to text locally on macOS / Apple Silicon using MLX Whisper. Optionally label who said what with pyannote.audio speaker diarization. Invoke when the user asks to transcribe a recording, write up an audio file (m4a / mp3 / wav / flac / ogg / webm), or identify who said what in a conversation. Everything runs on the user's own machine — audio never leaves the device.
---

# transcribe — skill instructions

This skill wraps the `transcribe.py` CLI bundled in the repository root.
It produces a plain-text transcript, optionally with speaker labels and
timestamps.

---

## 1. Locate the script

The script lives in the root of the same repo this skill ships with. Resolve
its absolute path by walking up from this `SKILL.md` until you find
`transcribe.py`. Quote the path in all commands because the user's home path
may contain spaces.

---

## 2. Pre-flight checks

Before running, confirm (one combined bash call is fine):

```bash
python3 -c "import mlx_whisper" 2>&1 | head -1
```

If that errors, tell the user to run
`pip install -r requirements.txt` in the repo directory and stop.

If the user asks for **speaker labels / diarization**, also verify:

```bash
python3 -c "import pyannote.audio" 2>&1 | head -1
echo "HF_TOKEN length: ${#HF_TOKEN}"
```

If pyannote is missing, tell the user to run
`pip install -r requirements-diarize.txt`.
If `HF_TOKEN length: 0`, point them at `SETUP_DIARIZATION.md` in the repo —
do **not** ask them to paste the token.

---

## 3. Invoke the script

### Text-only transcription

```bash
python3 "/absolute/path/to/transcribe.py" "/absolute/path/to/audio.m4a" -m large
```

Default model is `small`; use `-m large` unless the user says otherwise or
asks for speed. Available: `tiny`, `base`, `small`, `medium`, `large`.

### With speaker diarization

```bash
python3 "/absolute/path/to/transcribe.py" "/absolute/path/to/audio.m4a" \
  -m large --diarize --speakers N --no-rename
```

Rules:

- **Always pass `--no-rename`** when invoking from inside Claude — the
  interactive rename prompt needs a TTY and hangs otherwise.
- If the user gave you a speaker count, pass `--speakers N`.
- If they gave a range, pass `--min-speakers N --max-speakers M` instead.
- If they said nothing, pass neither — pyannote will auto-detect.
- Diarization is slow; warn the user the command may take several minutes
  on long recordings and consider running it in the background.

### Other useful flags

| Flag | Use |
|---|---|
| `-o DIR` | Write transcript(s) to `DIR` instead of next to the audio. |
| `-l LANG` | Force a language (`english`, `chinese`, …) instead of auto-detect. |

---

## 4. After the run

The script writes a `.txt` next to the audio file (or into `-o DIR`). Read
that file directly — do **not** copy the full transcript back into the chat
unless the user asks; it can be very long.

If diarized output contains `SPEAKER_00` / `SPEAKER_01` labels and the user
has indicated who the speakers are (e.g. "it was me and Alice"), offer to
replace the labels in-place by editing the `.txt`. A simple rule of thumb for
cold identification: in a greeting like *"Hi Alice"*, the person saying it
is **not** Alice — Alice is whoever is greeted (usually the next speaker).

Then ask the user what they want next: the raw transcript, a summary,
a translation, action items, etc.

---

## 5. Troubleshooting quick reference

| Symptom | Fix |
|---|---|
| `Symbol not found: _torch_library_impl` | `pip install --upgrade torch torchaudio` |
| `Cannot access gated repo ...` | User hasn't accepted pyannote model terms — point them to `SETUP_DIARIZATION.md § Step 3`. |
| `use_auth_token` / `token` keyword error | pyannote version mismatch; the script auto-falls-back, so this only happens if they've modified the code or use pyannote directly. Suggest `pip install --upgrade pyannote.audio`. |
| `HF_TOKEN length: 0` | Token not loaded in this shell. Tell them to open a new terminal or `source ~/.zshrc`. |

Full details: `SETUP_DIARIZATION.md` in the repo root.

---

## 6. Privacy

Emphasise to the user, once, that **the audio and transcript never leave
their machine**. This is a differentiator vs cloud transcription services
and is the main reason to use the skill.
