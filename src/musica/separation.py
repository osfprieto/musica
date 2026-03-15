"""Source separation using Demucs — splits audio into stems."""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Demucs htdemucs model outputs these four stems
STEM_NAMES = ("vocals", "bass", "drums", "other")


def separate_stems(wav_path: Path, output_dir: Path) -> dict[str, Path]:
    """Run Demucs on *wav_path* and return a dict mapping stem name → WAV path.

    Returns paths for: vocals, bass, drums, other.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Separating stems with Demucs …")

    cmd = [
        sys.executable, "-m", "demucs",
        "-n", "htdemucs",
        "-o", str(output_dir),
        str(wav_path),
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=1800,  # separation can be slow
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Demucs failed (exit {result.returncode}):\n{result.stderr}"
        )

    # Demucs outputs to: output_dir/htdemucs/<input_stem_name>/<stem>.wav
    source_name = wav_path.stem
    stems_dir = output_dir / "htdemucs" / source_name

    if not stems_dir.exists():
        # Try to find the output directory
        candidates = list((output_dir / "htdemucs").glob("*"))
        if candidates:
            stems_dir = candidates[0]
        else:
            raise FileNotFoundError(
                f"Demucs output not found. Expected at {stems_dir}"
            )

    stems: dict[str, Path] = {}
    for stem_name in STEM_NAMES:
        stem_path = stems_dir / f"{stem_name}.wav"
        if stem_path.exists():
            stems[stem_name] = stem_path
            logger.info("  Found stem: %s → %s", stem_name, stem_path)
        else:
            logger.warning("  Missing stem: %s", stem_name)

    if not stems:
        raise FileNotFoundError(f"No stems found in {stems_dir}")

    return stems
