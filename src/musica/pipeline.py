"""End-to-end pipeline: YouTube URL → MusicXML partiture(s)."""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Optional

from musica.download import download_audio
from musica.separation import separate_stems
from musica.transcription import transcribe_stems
from musica.arrangement import (
    arrange_single,
    arrange_auto,
    arrange_ensemble,
    export_score,
)

logger = logging.getLogger(__name__)


def run(
    url: str,
    output_dir: Path,
    instrument: Optional[str] = None,
    ensemble: Optional[list[str]] = None,
    title: Optional[str] = None,
) -> Path:
    """Execute the full pipeline.

    Parameters
    ----------
    url:
        YouTube URL to process.
    output_dir:
        Directory where result .musicxml files are written.
    instrument:
        If set, produce a partiture for this single instrument.
    ensemble:
        If set, produce a multi-part score for these instruments.
        Ignored if *instrument* is also set.
    title:
        Title for the score metadata. Defaults to "Untitled".

    Returns
    -------
    Path to the generated .musicxml file.
    """
    title = title or "Untitled"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    work_dir = output_dir / "_workdir"
    work_dir.mkdir(parents=True, exist_ok=True)

    # 1. Download
    logger.info("Step 1/4: Downloading audio …")
    wav_path = download_audio(url, work_dir / "download")

    # 2. Separate stems
    logger.info("Step 2/4: Separating stems …")
    stems = separate_stems(wav_path, work_dir / "separated")

    # 3. Transcribe stems to MIDI
    logger.info("Step 3/4: Transcribing to MIDI …")
    stem_midis = transcribe_stems(stems, work_dir / "transcribed")

    if not stem_midis:
        raise RuntimeError("No MIDI files were produced from any stem.")

    # 4. Arrange
    logger.info("Step 4/4: Arranging score …")
    if instrument:
        score = arrange_single(stem_midis, instrument, title=title)
        out_name = f"{title} - {instrument}"
    elif ensemble:
        score = arrange_ensemble(stem_midis, ensemble, title=title)
        out_name = f"{title} - ensemble"
    else:
        score = arrange_auto(stem_midis, title=title)
        out_name = f"{title} - full"

    # 5. Export
    result_path = export_score(score, output_dir / _safe_filename(out_name))

    logger.info("Done! Open in MuseScore: %s", result_path)
    return result_path


def _safe_filename(name: str) -> str:
    """Remove characters that are problematic in file paths."""
    keepchars = " _-"
    return "".join(c if c.isalnum() or c in keepchars else "_" for c in name)
