"""Instrument definitions with ranges, clefs, and stem-mapping heuristics."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from music21 import clef as m21clef
from music21 import instrument as m21inst


class InstrumentFamily(Enum):
    STRINGS = "strings"
    WOODWINDS = "woodwinds"
    BRASS = "brass"
    PERCUSSION = "percussion"
    VOCAL = "vocal"
    KEYBOARD = "keyboard"


@dataclass(frozen=True)
class InstrumentProfile:
    """Defines how a target instrument maps to the transcription pipeline."""

    name: str
    music21_class: type
    family: InstrumentFamily
    midi_low: int          # lowest playable MIDI note
    midi_high: int         # highest playable MIDI note
    clef_classes: list[type] = field(default_factory=lambda: [m21clef.TrebleClef])
    transposition_semitones: int = 0   # concert → written
    preferred_stems: list[str] = field(default_factory=lambda: ["other"])
    monophonic: bool = False

    @property
    def display_name(self) -> str:
        return self.name.replace("_", " ").title()


# ── Catalogue of supported instruments ──────────────────────────────────────

INSTRUMENTS: dict[str, InstrumentProfile] = {
    "violin": InstrumentProfile(
        name="violin",
        music21_class=m21inst.Violin,
        family=InstrumentFamily.STRINGS,
        midi_low=55,   # G3
        midi_high=105,  # A7
        clef_classes=[m21clef.TrebleClef],
        preferred_stems=["vocals", "other"],
        monophonic=True,
    ),
    "viola": InstrumentProfile(
        name="viola",
        music21_class=m21inst.Viola,
        family=InstrumentFamily.STRINGS,
        midi_low=48,   # C3
        midi_high=88,  # E6
        clef_classes=[m21clef.AltoClef],
        preferred_stems=["other"],
        monophonic=True,
    ),
    "cello": InstrumentProfile(
        name="cello",
        music21_class=m21inst.Violoncello,
        family=InstrumentFamily.STRINGS,
        midi_low=36,   # C2
        midi_high=81,  # A5
        clef_classes=[m21clef.BassClef, m21clef.TenorClef],
        preferred_stems=["bass", "other"],
        monophonic=True,
    ),
    "double_bass": InstrumentProfile(
        name="double_bass",
        music21_class=m21inst.DoubleBass,
        family=InstrumentFamily.STRINGS,
        midi_low=28,   # E1
        midi_high=67,  # G4
        clef_classes=[m21clef.BassClef],
        preferred_stems=["bass"],
        monophonic=True,
    ),
    "guitar": InstrumentProfile(
        name="guitar",
        music21_class=m21inst.AcousticGuitar,
        family=InstrumentFamily.STRINGS,
        midi_low=40,   # E2
        midi_high=83,  # B5
        clef_classes=[m21clef.TrebleClef],
        preferred_stems=["other"],
        monophonic=False,
    ),
    "harp": InstrumentProfile(
        name="harp",
        music21_class=m21inst.Harp,
        family=InstrumentFamily.STRINGS,
        midi_low=24,   # C1
        midi_high=103,  # G7
        clef_classes=[m21clef.TrebleClef, m21clef.BassClef],
        preferred_stems=["other"],
        monophonic=False,
    ),
    "piano": InstrumentProfile(
        name="piano",
        music21_class=m21inst.Piano,
        family=InstrumentFamily.KEYBOARD,
        midi_low=21,   # A0
        midi_high=108,  # C8
        clef_classes=[m21clef.TrebleClef, m21clef.BassClef],
        preferred_stems=["other"],
        monophonic=False,
    ),
    "voice": InstrumentProfile(
        name="voice",
        music21_class=m21inst.Vocalist,
        family=InstrumentFamily.VOCAL,
        midi_low=48,   # C3
        midi_high=84,  # C6
        clef_classes=[m21clef.TrebleClef],
        preferred_stems=["vocals"],
        monophonic=True,
    ),
    "flute": InstrumentProfile(
        name="flute",
        music21_class=m21inst.Flute,
        family=InstrumentFamily.WOODWINDS,
        midi_low=60,   # C4
        midi_high=96,  # C7
        clef_classes=[m21clef.TrebleClef],
        preferred_stems=["other"],
        monophonic=True,
    ),
}

# ── Ensemble presets ────────────────────────────────────────────────────────

ENSEMBLES: dict[str, list[str]] = {
    "string_quartet": ["violin", "violin", "viola", "cello"],
    "string_trio": ["violin", "viola", "cello"],
    "string_orchestra": ["violin", "violin", "viola", "cello", "double_bass"],
    "piano_trio": ["piano", "violin", "cello"],
}


# ── Default stem → instrument mapping (used in auto-detect mode) ────────────

DEFAULT_STEM_INSTRUMENT_MAP: dict[str, str] = {
    "vocals": "voice",
    "bass": "cello",
    "drums": None,        # percussion stem, skipped for pitched instruments
    "other": "piano",
}


def get_instrument(name: str) -> InstrumentProfile:
    key = name.lower().replace(" ", "_").replace("-", "_")
    if key not in INSTRUMENTS:
        available = ", ".join(sorted(INSTRUMENTS.keys()))
        raise ValueError(f"Unknown instrument '{name}'. Available: {available}")
    return INSTRUMENTS[key]


def list_instruments() -> list[str]:
    return sorted(INSTRUMENTS.keys())


def get_ensemble(name: str) -> list[InstrumentProfile]:
    key = name.lower().replace(" ", "_").replace("-", "_")
    if key not in ENSEMBLES:
        available = ", ".join(sorted(ENSEMBLES.keys()))
        raise ValueError(f"Unknown ensemble '{name}'. Available: {available}")
    return [INSTRUMENTS[n] for n in ENSEMBLES[key]]
