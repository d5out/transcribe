# transcribe

**Local AI audio transcription for macOS / Apple Silicon — with optional speaker diarization.**

Transcribe meetings, interviews, voice notes, and podcasts straight on your Mac.
No cloud, no uploads, no per-minute fees. Your audio never leaves your machine.

> 🤖 **Also works as a Claude Skill** — if you use Claude Code, you can ask
> Claude to transcribe files conversationally (*"transcribe this recording
> and summarise it"*) and it will invoke this tool under the hood. See
> **[§ Use as a Claude Skill](#use-as-a-claude-skill)** below.

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

## Use as a Claude Skill

If you have [Claude Code](https://www.anthropic.com/claude-code), this repo
doubles as a **Claude Skill**. Install it once and Claude will invoke the
transcription tool for you whenever you ask in natural language.

### Install the skill

**Option A — link this repo's bundled skill (stays in sync with `git pull`):**

```bash
# From inside this cloned repo:
mkdir -p ~/.claude/skills
ln -s "$(pwd)/.claude/skills/transcribe" ~/.claude/skills/transcribe
```

**Option B — copy it:**

```bash
mkdir -p ~/.claude/skills
cp -r .claude/skills/transcribe ~/.claude/skills/transcribe
```

### Then just ask Claude

Once the skill is installed (and your Python deps from `requirements.txt` are
in place), open Claude Code and say things like:

- *"Transcribe `/path/to/meeting.m4a` with the large model."*
- *"Transcribe this recording, there are 3 speakers, then summarise it."*
- *"Who said what in `interview.mp3`? Save a labelled transcript."*

Claude reads **[`.claude/skills/transcribe/SKILL.md`](.claude/skills/transcribe/SKILL.md)**
to decide when to use the skill and how to call `transcribe.py`. It handles
pre-flight dependency checks, picks the right flags, and after the run it
can chain into summaries, translation, note-taking, etc.

The skill respects the same privacy guarantee as the CLI: audio stays local.

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

## Privacy & data flow

Exactly what leaves your machine depends on **how** you invoke the tool.
Read this section before transcribing sensitive content.

### Using the CLI or desktop app directly (standalone)

| Data | Where it goes | Leaves your machine? |
|---|---|---|
| Audio / video file | Processed in memory on your Mac | **No — never uploaded** |
| Transcript (`.txt`) | Written to local disk | **No — never uploaded** |
| Video frames | Not read at all; only the audio track is extracted | **No — not processed** |
| Whisper / pyannote model weights | Downloaded once from Hugging Face, then cached under `~/.cache/huggingface/` and used offline | Download metadata yes; content no |
| What Hugging Face sees | Your IP + token + which model files you requested | **Never your audio or transcript** |

In standalone mode the Hub only knows *"this token downloaded these model
files"*. It has no idea what you transcribed.

### Using it through the Claude Skill

Still runs locally — but there is an extra path to be aware of:

- The transcription script writes a `.txt` on disk, same as before.
- It also prints each segment to **stdout** (Whisper's `verbose=True` default).
- When Claude Code invokes the skill, its Bash tool captures that stdout.
- Captured stdout becomes part of the conversation → it is sent to
  Anthropic's servers as normal conversation context.

In other words: the *file* on disk stays local, but anything Claude reads
back from the tool while helping you (for summarisation, translation,
follow-up, etc.) flows through Anthropic like any other Claude conversation.

If you want the strongest privacy — e.g. legal depositions, medical
recordings, anything you wouldn't paste into a chat with any AI — **run the
CLI in a plain terminal rather than through the skill.**

### Recording other people

The tool is agnostic about what you feed it, but please note:

- In the UK, EU (GDPR), California, and many other jurisdictions, recording
  a conversation without the other party's knowledge and/or consent can be
  **illegal** — even if you're a participant.
- Even where recording is legal, running the recording through AI analysis
  often requires a **separate disclosure** to the other party under
  applicable data-protection rules.
- This is a property of the **recording**, not the tool — but it applies
  equally whether you use this project, a cloud service, or a human
  typist.

---

## ⭐ Star this repo

If this saves you a trip to a paid transcription service, please star the
repo — it helps others find it and keeps the project prioritised for
continued updates as the underlying libraries evolve.

👉 [**github.com/d5out/transcribe**](https://github.com/d5out/transcribe) — click ⭐ in the top-right.
