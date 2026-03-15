"""Audio-to-MIDI transcription using Basic Pitch (Spotify)."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def transcribe_to_midi(wav_path: Path, output_dir: Path) -> Path:
    """Transcribe a WAV file to MIDI using Basic Pitch.

    Returns the path to the generated .mid file.
    """
    try:
        from basic_pitch.inference import predict_and_save
    except ImportError as exc:
        raise RuntimeError(
            "basic-pitch is not installed. Run: pip install basic-pitch"
        ) from exc

    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Transcribing %s to MIDI …", wav_path.name)

    predict_and_save(
        audio_path_list=[wav_path],
        output_directory=output_dir,
        save_midi=True,
        save_model_outputs=False,
        save_notes=False,
        sonify_midi=False,
    )

    # Basic Pitch writes <stem>_basic_pitch.mid
    midi_files = list(output_dir.glob("*.mid"))
    if not midi_files:
        midi_files = list(output_dir.glob("*.midi"))
    if not midi_files:
        raise FileNotFoundError(
            f"No MIDI file produced in {output_dir} for {wav_path.name}"
        )

    midi_path = midi_files[0]
    logger.info("MIDI saved to %s", midi_path)
    return midi_path


def transcribe_stems(
    stems: dict[str, Path], output_dir: Path
) -> dict[str, Path]:
    """Transcribe each separated stem to MIDI.

    Returns dict mapping stem name → MIDI path.
    Skips the 'drums' stem (not useful for pitched instruments).
    """
    midi_dir = output_dir / "midi"
    midi_dir.mkdir(parents=True, exist_ok=True)

    result: dict[str, Path] = {}

    for stem_name, wav_path in stems.items():
        if stem_name == "drums":
            logger.info("Skipping drums stem (unpitched)")
            continue

        stem_midi_dir = midi_dir / stem_name
        midi_path = transcribe_to_midi(wav_path, stem_midi_dir)
        result[stem_name] = midi_path

    return result
