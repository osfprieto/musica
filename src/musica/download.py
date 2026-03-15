"""Download audio from YouTube URLs using yt-dlp."""

from __future__ import annotations

import logging
import subprocess
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


def _require_tool(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise RuntimeError(
            f"'{name}' is not installed or not on PATH. "
            f"Install it first (e.g. pip install yt-dlp, or download ffmpeg)."
        )
    return path


def download_audio(url: str, output_dir: Path) -> Path:
    """Download audio from a YouTube URL and return the path to a WAV file.

    Uses yt-dlp to download and ffmpeg to convert to 44.1 kHz mono WAV,
    which is the ideal format for downstream transcription models.
    """
    _require_tool("yt-dlp")
    _require_tool("ffmpeg")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(output_dir / "source.%(ext)s")

    logger.info("Downloading audio from %s …", url)

    cmd = [
        "yt-dlp",
        "--no-playlist",
        "--extract-audio",
        "--audio-format", "wav",
        "--audio-quality", "0",
        "--output", output_template,
        "--postprocessor-args", "ffmpeg:-ac 1 -ar 44100",
        url,
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=600,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"yt-dlp failed (exit {result.returncode}):\n{result.stderr}"
        )

    wav_path = output_dir / "source.wav"
    if not wav_path.exists():
        # yt-dlp may use a slightly different name; find any wav
        wavs = list(output_dir.glob("*.wav"))
        if not wavs:
            raise FileNotFoundError(
                f"No WAV file found in {output_dir} after download."
            )
        wav_path = wavs[0]

    logger.info("Audio saved to %s", wav_path)
    return wav_path
