#!/usr/bin/env python3
"""
Audio to Text Transcription Tool
Supports: m4a, mp3, wav, and other audio formats
Uses MLX Whisper - optimized for Apple Silicon
Optional speaker diarization via pyannote.audio
"""

import argparse
import os
import sys
from pathlib import Path

import mlx_whisper

SUPPORTED_EXTENSIONS = {".m4a", ".mp3", ".wav", ".flac", ".ogg", ".webm"}

MODELS = {
    "tiny": "mlx-community/whisper-tiny-mlx",
    "base": "mlx-community/whisper-base-mlx",
    "small": "mlx-community/whisper-small-mlx",
    "medium": "mlx-community/whisper-medium-mlx",
    "large": "mlx-community/whisper-large-v3-mlx",
}

DIARIZATION_MODEL = "pyannote/speaker-diarization-3.1"


def format_timestamp(seconds: float) -> str:
    m = int(seconds // 60)
    s = seconds - m * 60
    return f"{m:02d}:{s:06.3f}"


def run_diarization(
    audio_path: Path,
    hf_token: str,
    num_speakers: int | None = None,
    min_speakers: int | None = None,
    max_speakers: int | None = None,
):
    """Run pyannote speaker diarization. Returns list of (start, end, speaker_label)."""
    try:
        from pyannote.audio import Pipeline
    except ImportError:
        print("Error: pyannote.audio is not installed.")
        print("Install with: pip install pyannote.audio")
        sys.exit(1)

    print("  Running speaker diarization (pyannote)...")
    pipeline = Pipeline.from_pretrained(DIARIZATION_MODEL, use_auth_token=hf_token)

    try:
        import torch
        if torch.backends.mps.is_available():
            pipeline.to(torch.device("mps"))
    except Exception:
        pass

    kwargs = {}
    if num_speakers is not None:
        kwargs["num_speakers"] = num_speakers
    else:
        if min_speakers is not None:
            kwargs["min_speakers"] = min_speakers
        if max_speakers is not None:
            kwargs["max_speakers"] = max_speakers
    diarization = pipeline(str(audio_path), **kwargs)

    segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segments.append((turn.start, turn.end, speaker))
    return segments


def prompt_speaker_count() -> tuple[int | None, int | None, int | None]:
    """Ask the user how many speakers are in the recording.

    Returns (num_speakers, min_speakers, max_speakers).
    """
    print("\nHow many speakers are in this recording?")
    print("  - Enter a number (e.g. 2) if you know exactly")
    print("  - Enter a range (e.g. 2-4) if you have a rough idea")
    print("  - Press Enter to let the model decide automatically")
    raw = input("Speakers: ").strip()

    if not raw:
        return None, None, None
    if "-" in raw:
        try:
            lo, hi = raw.split("-", 1)
            return None, int(lo.strip()), int(hi.strip())
        except ValueError:
            print("  Could not parse range, falling back to auto-detect.")
            return None, None, None
    try:
        return int(raw), None, None
    except ValueError:
        print("  Could not parse number, falling back to auto-detect.")
        return None, None, None


def prompt_speaker_names(grouped_segments) -> dict[str, str]:
    """Show each speaker's first utterance and let the user rename them.

    grouped_segments: list of dicts with keys speaker, start, end, text.
    Returns {SPEAKER_XX: "RealName"} mapping. Empty/skipped entries keep original label.
    """
    first_utterance: dict[str, str] = {}
    for g in grouped_segments:
        if g["speaker"] not in first_utterance:
            snippet = g["text"][:120] + ("…" if len(g["text"]) > 120 else "")
            first_utterance[g["speaker"]] = snippet

    if not first_utterance:
        return {}

    print("\nRename speakers (press Enter to keep the default label):")
    print("Tip: if the opening says 'Hi Alice' — the person saying it is NOT Alice;")
    print("     Alice is whoever is being greeted (likely the next speaker).\n")

    mapping: dict[str, str] = {}
    for label, snippet in first_utterance.items():
        print(f"  {label} first said:")
        print(f"    \"{snippet}\"")
        name = input(f"  Rename {label} to: ").strip()
        if name:
            mapping[label] = name
        print()
    return mapping


def assign_speaker(seg_start: float, seg_end: float, speaker_segments) -> str:
    """Return the speaker with the most temporal overlap with [seg_start, seg_end]."""
    best_speaker = "SPEAKER_?"
    best_overlap = 0.0
    for sp_start, sp_end, speaker in speaker_segments:
        overlap = min(seg_end, sp_end) - max(seg_start, sp_start)
        if overlap > best_overlap:
            best_overlap = overlap
            best_speaker = speaker
    return best_speaker


def group_by_speaker(whisper_segments, speaker_segments):
    """Return list of {speaker, start, end, text} merging consecutive same-speaker turns."""
    grouped = []
    for seg in whisper_segments:
        speaker = assign_speaker(seg["start"], seg["end"], speaker_segments)
        text = seg["text"].strip()
        if grouped and grouped[-1]["speaker"] == speaker:
            grouped[-1]["end"] = seg["end"]
            grouped[-1]["text"] += " " + text
        else:
            grouped.append({
                "speaker": speaker,
                "start": seg["start"],
                "end": seg["end"],
                "text": text,
            })
    return grouped


def format_diarized_output(grouped, name_map: dict[str, str] | None = None) -> str:
    name_map = name_map or {}
    lines = []
    for g in grouped:
        display = name_map.get(g["speaker"], g["speaker"])
        header = (
            f"[{display} "
            f"{format_timestamp(g['start'])} --> {format_timestamp(g['end'])}]"
        )
        lines.append(header)
        lines.append(g["text"])
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def transcribe_file(
    audio_path: Path,
    model_path: str,
    output_dir: Path | None = None,
    language: str | None = None,
    diarize: bool = False,
    hf_token: str | None = None,
    num_speakers: int | None = None,
    min_speakers: int | None = None,
    max_speakers: int | None = None,
    rename_speakers: bool = True,
) -> Path:
    """Transcribe a single audio file and save as .txt"""
    print(f"\nTranscribing: {audio_path.name}")

    result = mlx_whisper.transcribe(
        str(audio_path),
        path_or_hf_repo=model_path,
        language=language,
        verbose=True,
    )

    detected_lang = result.get("language", "unknown")
    print(f"  Detected language: {detected_lang}")

    if output_dir:
        output_path = output_dir / f"{audio_path.stem}.txt"
    else:
        output_path = audio_path.with_suffix(".txt")

    if diarize:
        if not hf_token:
            print("\nError: --diarize requires a HuggingFace access token.")
            print("  1) Create a token at https://huggingface.co/settings/tokens")
            print("  2) Accept the model terms at:")
            print(f"     https://huggingface.co/{DIARIZATION_MODEL}")
            print("     https://huggingface.co/pyannote/segmentation-3.0")
            print("  3) Pass via --hf-token ... or set HF_TOKEN in your environment.")
            sys.exit(1)

        speaker_segments = run_diarization(
            audio_path,
            hf_token,
            num_speakers=num_speakers,
            min_speakers=min_speakers,
            max_speakers=max_speakers,
        )
        unique_speakers = sorted({s for _, _, s in speaker_segments})
        print(f"  Identified {len(unique_speakers)} speaker(s): {', '.join(unique_speakers)}")

        grouped = group_by_speaker(result["segments"], speaker_segments)

        name_map: dict[str, str] = {}
        if rename_speakers and sys.stdin.isatty():
            name_map = prompt_speaker_names(grouped)

        output_text = format_diarized_output(grouped, name_map)
        output_path.write_text(output_text)
    else:
        output_path.write_text(result["text"].strip())

    print(f"  Saved: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Transcribe audio files (m4a, mp3, etc.) to text using MLX Whisper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 transcribe.py audio.m4a                      # Single file
  python3 transcribe.py *.mp3                          # Multiple files
  python3 transcribe.py audio_folder/                  # Entire folder
  python3 transcribe.py audio.m4a -m medium            # Use medium model
  python3 transcribe.py audio.m4a -o ./transcripts/    # Custom output dir
  python3 transcribe.py audio.m4a --language french    # Force language
  python3 transcribe.py audio.m4a --diarize            # Label speakers
  python3 transcribe.py audio.m4a --diarize --speakers 2
        """
    )
    parser.add_argument("input", nargs="*", help="Audio file(s) or folder to transcribe")
    parser.add_argument(
        "-m", "--model",
        default="small",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model size (default: small)",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output directory for transcripts (default: same as input)",
    )
    parser.add_argument(
        "-l", "--language",
        help="Force language (auto-detect if not specified)",
    )
    parser.add_argument(
        "--diarize",
        action="store_true",
        help="Label each segment with a speaker tag (requires pyannote.audio + HF token)",
    )
    parser.add_argument(
        "--speakers",
        type=int,
        default=None,
        help="Fix the number of speakers (helps diarization accuracy when known)",
    )
    parser.add_argument(
        "--min-speakers",
        type=int,
        default=None,
        help="Minimum number of speakers (used only if --speakers is not set)",
    )
    parser.add_argument(
        "--max-speakers",
        type=int,
        default=None,
        help="Maximum number of speakers (used only if --speakers is not set)",
    )
    parser.add_argument(
        "--no-rename",
        action="store_true",
        help="Skip the interactive 'rename SPEAKER_XX to real name' prompt after diarization",
    )
    parser.add_argument(
        "--hf-token",
        default=os.environ.get("HF_TOKEN"),
        help="HuggingFace token for pyannote models (or set HF_TOKEN env var)",
    )

    args = parser.parse_args()

    if not args.input:
        print("No audio file specified.\n")
        file_path = input("Enter path to audio file (m4a, mp3, wav, etc.): ").strip()
        file_path = file_path.strip("'\"")
        if not file_path:
            print("Error: No file path provided")
            sys.exit(1)
        args.input = [file_path]

    audio_files: list[Path] = []
    for input_path in args.input:
        path = Path(input_path)
        if path.is_dir():
            for ext in SUPPORTED_EXTENSIONS:
                audio_files.extend(path.glob(f"*{ext}"))
        elif path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            audio_files.append(path)
        elif path.is_file():
            print(f"Warning: Skipping unsupported file: {path}")
        else:
            print(f"Warning: Path not found: {path}")

    if not audio_files:
        print("Error: No audio files found")
        sys.exit(1)

    print(f"Found {len(audio_files)} audio file(s)")
    print("\nTip: Use -m to select model size:")
    print("  -m small   (default, fast)")
    print("  -m medium  (better accuracy)")
    print("  -m large   (best accuracy, slower)")
    if args.diarize:
        # If user didn't specify any speaker count info, ask interactively
        nothing_specified = (
            args.speakers is None
            and args.min_speakers is None
            and args.max_speakers is None
        )
        if nothing_specified and sys.stdin.isatty():
            num, lo, hi = prompt_speaker_count()
            args.speakers = num
            args.min_speakers = lo
            args.max_speakers = hi

        print("\nSpeaker diarization: ON")
        if args.speakers:
            print(f"  Number of speakers: {args.speakers}")
        elif args.min_speakers or args.max_speakers:
            print(f"  Speaker range: {args.min_speakers or '?'}-{args.max_speakers or '?'}")
        else:
            print("  Speaker count: auto-detect")

    if args.output:
        args.output.mkdir(parents=True, exist_ok=True)

    model_path = MODELS[args.model]
    print(f"\nUsing model: {args.model} (Apple Silicon optimized)")

    for audio_file in audio_files:
        try:
            transcribe_file(
                audio_file,
                model_path,
                args.output,
                args.language,
                diarize=args.diarize,
                hf_token=args.hf_token,
                num_speakers=args.speakers,
                min_speakers=args.min_speakers,
                max_speakers=args.max_speakers,
                rename_speakers=not args.no_rename,
            )
        except Exception as e:
            print(f"  Error transcribing {audio_file}: {e}")

    print("\nDone!")


if __name__ == "__main__":
    main()
