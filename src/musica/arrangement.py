"""Arrangement engine — maps MIDI transcriptions to instrument parts and builds scores."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from music21 import converter, stream, note, chord, clef as m21clef, tempo, metadata

from musica.instruments import (
    InstrumentProfile,
    INSTRUMENTS,
    DEFAULT_STEM_INSTRUMENT_MAP,
    get_instrument,
)

logger = logging.getLogger(__name__)


# ── Helpers ─────────────────────────────────────────────────────────────────


def _clamp_to_range(
    part: stream.Part,
    profile: InstrumentProfile,
) -> stream.Part:
    """Transpose notes that fall outside the instrument's playable range
    by shifting them up or down by octaves until they fit."""
    for element in part.recurse().notes:
        pitches = (
            element.pitches if isinstance(element, chord.Chord) else [element.pitch]
        )
        for p in pitches:
            while p.midi < profile.midi_low:
                p.octave += 1
            while p.midi > profile.midi_high:
                p.octave -= 1
    return part


def _reduce_to_monophonic(part: stream.Part) -> stream.Part:
    """For monophonic instruments (violin, cello, etc.) keep only the
    highest note of each chord."""
    for element in part.recurse():
        if isinstance(element, chord.Chord):
            top_pitch = max(element.pitches, key=lambda p: p.midi)
            n = note.Note(top_pitch)
            n.duration = element.duration
            n.offset = element.offset
            element.activeSite.replace(element, n)
    return part


def _apply_instrument(
    part: stream.Part,
    profile: InstrumentProfile,
    part_label: Optional[str] = None,
) -> stream.Part:
    """Stamp a music21 instrument, clef, and name onto a Part."""
    inst = profile.music21_class()
    part.insert(0, inst)
    part.insert(0, profile.clef_classes[0]())
    part.partName = part_label or profile.display_name
    return part


# ── Single-instrument mode ──────────────────────────────────────────────────


def arrange_single(
    stem_midis: dict[str, Path],
    instrument_name: str,
    title: str = "Untitled",
) -> stream.Score:
    """Produce a single-part score for one instrument.

    Picks the most suitable stem based on the instrument's preferred_stems.
    """
    profile = get_instrument(instrument_name)

    # Pick best stem
    chosen_stem: Optional[str] = None
    chosen_midi: Optional[Path] = None
    for pref in profile.preferred_stems:
        if pref in stem_midis:
            chosen_stem = pref
            chosen_midi = stem_midis[pref]
            break

    if chosen_midi is None:
        # Fall back to any available stem
        chosen_stem, chosen_midi = next(iter(stem_midis.items()))

    logger.info(
        "Arranging for %s using '%s' stem", profile.display_name, chosen_stem
    )

    parsed = converter.parse(str(chosen_midi))
    part = parsed.parts[0] if parsed.parts else parsed

    if not isinstance(part, stream.Part):
        wrapper = stream.Part()
        for el in part:
            wrapper.append(el)
        part = wrapper

    if profile.monophonic:
        part = _reduce_to_monophonic(part)

    part = _clamp_to_range(part, profile)
    part = _apply_instrument(part, profile)

    score = stream.Score()
    score.metadata = metadata.Metadata()
    score.metadata.title = title
    score.insert(0, tempo.MetronomeMark(number=120))
    score.insert(0, part)

    return score


# ── Auto-detect mode (all detected stems) ──────────────────────────────────


def arrange_auto(
    stem_midis: dict[str, Path],
    title: str = "Untitled",
) -> stream.Score:
    """Produce a multi-part score, assigning each stem to its default instrument."""
    score = stream.Score()
    score.metadata = metadata.Metadata()
    score.metadata.title = title
    score.insert(0, tempo.MetronomeMark(number=120))

    for stem_name, midi_path in stem_midis.items():
        instrument_name = DEFAULT_STEM_INSTRUMENT_MAP.get(stem_name)
        if instrument_name is None:
            logger.info("Skipping stem '%s' (no instrument mapping)", stem_name)
            continue

        profile = get_instrument(instrument_name)
        logger.info(
            "Assigning stem '%s' → %s", stem_name, profile.display_name
        )

        parsed = converter.parse(str(midi_path))
        part = parsed.parts[0] if parsed.parts else parsed

        if not isinstance(part, stream.Part):
            wrapper = stream.Part()
            for el in part:
                wrapper.append(el)
            part = wrapper

        if profile.monophonic:
            part = _reduce_to_monophonic(part)

        part = _clamp_to_range(part, profile)
        part = _apply_instrument(part, profile, f"{profile.display_name} ({stem_name})")
        score.insert(0, part)

    return score


# ── Ensemble mode ───────────────────────────────────────────────────────────


def arrange_ensemble(
    stem_midis: dict[str, Path],
    instrument_names: list[str],
    title: str = "Untitled",
) -> stream.Score:
    """Produce a score for a given set of instruments.

    Distributes stems among the requested instruments using their preferred
    stem order. When multiple instruments want the same stem, each gets a
    copy (they can later be differentiated in MuseScore).
    """
    profiles = [get_instrument(n) for n in instrument_names]

    score = stream.Score()
    score.metadata = metadata.Metadata()
    score.metadata.title = title
    score.insert(0, tempo.MetronomeMark(number=120))

    for idx, profile in enumerate(profiles):
        # Pick best available stem
        chosen_stem: Optional[str] = None
        chosen_midi: Optional[Path] = None
        for pref in profile.preferred_stems:
            if pref in stem_midis:
                chosen_stem = pref
                chosen_midi = stem_midis[pref]
                break
        if chosen_midi is None:
            chosen_stem, chosen_midi = next(iter(stem_midis.items()))

        logger.info(
            "Ensemble part %d: %s ← stem '%s'",
            idx + 1,
            profile.display_name,
            chosen_stem,
        )

        parsed = converter.parse(str(chosen_midi))
        part = parsed.parts[0] if parsed.parts else parsed

        if not isinstance(part, stream.Part):
            wrapper = stream.Part()
            for el in part:
                wrapper.append(el)
            part = wrapper

        if profile.monophonic:
            part = _reduce_to_monophonic(part)

        part = _clamp_to_range(part, profile)
        label = profile.display_name
        if instrument_names.count(profile.name) > 1:
            label = f"{profile.display_name} {idx + 1}"
        part = _apply_instrument(part, profile, label)
        score.insert(0, part)

    return score


# ── Export ──────────────────────────────────────────────────────────────────


def export_score(score: stream.Score, output_path: Path) -> Path:
    """Write the score to MusicXML (.musicxml), directly readable by MuseScore."""
    output_path = output_path.with_suffix(".musicxml")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    score.write("musicxml", fp=str(output_path))
    logger.info("Score written to %s", output_path)
    return output_path
