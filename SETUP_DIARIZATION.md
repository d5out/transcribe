# Speaker Diarization — Setup Guide

This is the **optional** setup for labeling who said what in your transcripts.
Basic transcription (just text) does not need any of this — you can use
`transcribe.py` right away after `pip install -r requirements.txt`.

---

## Why this is needed

Speaker diarization uses **pyannote.audio**, which relies on pretrained models
hosted on Hugging Face. The models themselves are free, but Hugging Face
requires:

1. A free Hugging Face account + access token, and
2. You to explicitly accept the terms of use for two model pages.

Once you have that set up, the models download once to your machine and
everything runs locally afterwards. **No audio ever leaves your computer.**

---

## Step 1 — Install the optional dependencies

```bash
pip install -r requirements-diarize.txt
```

This adds `pyannote.audio`, `torch`, and `torchaudio`. The download is ~1-2 GB
total and can take a few minutes on first install.

---

## Step 2 — Create a Hugging Face account and token

1. Sign up or sign in at https://huggingface.co
2. Go to https://huggingface.co/settings/tokens
3. Click **Create new token**
4. Token type: the minimum needed is
   **"Read access to contents of all public gated repos you can access"**
   (Fine-grained token → Repositories section → third option)

   If you prefer a classic token, selecting **Read** is also fine.
5. Copy the token (it looks like `hf_xxxxxxxxxxxxxxxxxxxxxxxxx`).

**Do not paste this token into any chat window, log file, issue tracker, or
shared document.** Treat it like a password.

---

## Step 3 — Accept the two model licenses

Open each of these two pages and click **"Agree and access repository"** once
per page (you need to be signed in):

- https://huggingface.co/pyannote/speaker-diarization-3.1
- https://huggingface.co/pyannote/segmentation-3.0

Without this step, the token is valid but cannot download the models.

---

## Step 4 — Store the token securely

You have three options, ranked from most to least secure.

### Option A — macOS Keychain (recommended on Mac)

Token is stored encrypted in the system keychain. Your shell rc file only
contains a command that retrieves it — no plaintext secret ever appears in
config files.

```bash
# Store token in Keychain (the -w with no value makes it prompt securely —
# the token is not echoed and is not saved in shell history):
security add-generic-password -s HF_TOKEN -a "$USER" -w

# Tell your shell to read it from Keychain at startup:
echo 'export HF_TOKEN=$(security find-generic-password -s HF_TOKEN -a "$USER" -w 2>/dev/null)' >> ~/.zshrc
source ~/.zshrc
```

If you already have an entry with that name, remove it first:

```bash
security delete-generic-password -s HF_TOKEN -a "$USER"
```

The first time an app reads the keychain entry, macOS will show a prompt
asking whether to allow access. Click **Always Allow**.

### Option B — Environment variable in `~/.zshrc` (plain text)

Simpler but the token is stored in plain text on disk.

```bash
echo 'export HF_TOKEN=hf_your_token_here' >> ~/.zshrc
source ~/.zshrc
```

### Option C — Pass on the command line each time

Nothing is stored. Most secure but least convenient:

```bash
python3 transcribe.py audio.m4a --diarize --hf-token hf_your_token_here
```

---

## Step 5 — Verify it works

In a new terminal window run:

```bash
echo "length: ${#HF_TOKEN}, prefix: ${HF_TOKEN:0:4}"
```

Expected output:

```
length: 37, prefix: hf_x
```

If you see `length: 0`, the environment variable did not load — close and
reopen your terminal, or run `source ~/.zshrc`.

---

## Step 6 — Run diarized transcription

```bash
python3 transcribe.py your_audio.m4a -m large --diarize --speakers 2
```

Flags:

- `-m large` — highest-accuracy Whisper model (slower). You can also use
  `small` / `medium` / `tiny`.
- `--diarize` — label each segment with a speaker tag.
- `--speakers N` — fix the number of speakers when you know it (more
  accurate than auto-detect).
- `--min-speakers N --max-speakers M` — supply a range if unsure.
- Omit all three to let the model auto-detect.

On the first diarized run, pyannote will download its models (~500 MB total)
and cache them in `~/.cache/huggingface/`. Subsequent runs reuse the cache.

---

## Output format

With `--diarize`, the output `.txt` looks like this:

```
[SPEAKER_00 00:00.000 --> 00:14.440]
Hello, how are you?

[SPEAKER_01 00:14.440 --> 00:22.000]
Good, thanks. You?
```

If you run in an interactive terminal (not through an IDE / automation),
`transcribe.py` will prompt you to rename `SPEAKER_XX` to real names right
after diarization. Pass `--no-rename` to skip this prompt.

**Tip for figuring out who is who:** when people greet each other at the
start of a call — e.g. one person says *"Hi Alice"* — that person is **not**
Alice; Alice is whoever is being greeted (usually the next speaker to reply).

---

## Troubleshooting

**`Error: --diarize requires a HuggingFace access token.`**
The token is not visible to the process. Check `echo ${#HF_TOKEN}` in the
same shell you'll run the script from. If it's 0, you need to open a new
terminal or `source ~/.zshrc`.

**`401 Client Error: Unauthorized`**
The token itself is valid but you have not accepted the terms on both model
pages. Repeat Step 3.

**`403 Client Error: Forbidden`**
Token lacks permission for gated repos. Recreate the token and make sure the
"Read access to public gated repos" scope is enabled.

**`Symbol not found: _torch_library_impl`**
`torch` and `torchaudio` versions are mismatched. Reinstall both together:

```bash
pip install --upgrade torch torchaudio
```

**Diarization is slow or inaccurate**

- Use `--speakers N` if you know the exact number of speakers.
- Short (<10s) recordings are hard to diarize — more audio per speaker
  gives better clustering.
- Overlapping speech (people talking over each other) is assigned to
  whichever voice is louder.
- For many speakers (5+) or very noisy audio, consider a cloud service
  like AssemblyAI or Deepgram instead.

---

## Security reminders

- **Never commit your token** to git. The included `.gitignore` already
  excludes `.env` and shell dotfiles, but double-check before every commit.
- **Never paste your token into a chat window** with an AI assistant or
  anyone else. If you accidentally expose a token, revoke it immediately
  at https://huggingface.co/settings/tokens and issue a new one.
- The Keychain option (Step 4A) is the safest for day-to-day use because
  your shell config file contains no secret — only a command to fetch it.
