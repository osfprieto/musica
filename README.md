# Musica

Turn any YouTube video into instrument partitures (sheet music) that open directly in **MuseScore**.

## Features

- **Single instrument mode** — produce a partiture for cello, guitar, violin, or any supported instrument
- **Auto-detect mode** — transcribe all detected stems and assign default instruments
- **Ensemble mode** — generate a full orchestral/chamber score with parts for each instrument
- **Built-in presets** — string quartet, string trio, string orchestra, piano trio

## Prerequisites

Install these system tools before running:

- **Python 3.9 – 3.12** — Python 3.13+ is not yet supported by TensorFlow (required by `basic-pitch`). Download from [python.org](https://www.python.org/downloads/) and install Python 3.11 or 3.12.
- **ffmpeg** — [download](https://ffmpeg.org/download.html) and add to PATH
- **MuseScore 4** — for viewing/editing the output files

## Installation

### 1. Create and activate a virtual environment

> **Note:** Python 3.9 – 3.12 is required. `basic-pitch` depends on TensorFlow, which has no Windows builds for Python 3.13+. Download Python 3.12 from [python.org](https://www.python.org/downloads/) if needed.

**Windows (Command Prompt)**

Use the `py` launcher to target a specific Python version when creating the venv:
```cmd
cd musica
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
```

To confirm you're using the right version after activating:
```cmd
python --version
```

**macOS / Linux**
```bash
cd musica
python3.12 -m venv .venv
source .venv/bin/activate
```

### 2. Install the package

```bash
pip install -e .
```

This installs all Python dependencies: `yt-dlp`, `demucs`, `basic-pitch`, `music21`, `click`.

### 3. Deactivate when done

```bash
deactivate
```

## Usage

### Generate partitures for all detected instruments
```bash
musica "https://youtube.com/watch?v=VIDEO_ID"
```

### Single instrument
```bash
musica "https://youtube.com/watch?v=VIDEO_ID" -i cello
musica "https://youtube.com/watch?v=VIDEO_ID" -i guitar
musica "https://youtube.com/watch?v=VIDEO_ID" -i violin
```

### Custom ensemble
```bash
musica "https://youtube.com/watch?v=VIDEO_ID" -e violin -e violin -e viola -e cello
```

### Named preset
```bash
musica "https://youtube.com/watch?v=VIDEO_ID" --preset string_quartet
```

### Other options
```bash
musica "URL" -o ./my_output -t "Song Title" -v
musica --list-instruments
musica --list-ensembles
```

## Supported Instruments

| Instrument   | Range     | Type              |
|-------------|-----------|-------------------|
| violin      | G3 – A7   | Strings (mono)    |
| viola       | C3 – E6   | Strings (mono)    |
| cello       | C2 – A5   | Strings (mono)    |
| double_bass | E1 – G4   | Strings (mono)    |
| guitar      | E2 – B5   | Strings (poly)    |
| harp        | C1 – G7   | Strings (poly)    |
| piano       | A0 – C8   | Keyboard (poly)   |
| voice       | C3 – C6   | Vocal (mono)      |
| flute       | C4 – C7   | Woodwinds (mono)  |

## Ensemble Presets

| Preset           | Parts                                      |
|-----------------|---------------------------------------------|
| string_quartet  | violin, violin, viola, cello                |
| string_trio     | violin, viola, cello                        |
| string_orchestra| violin, violin, viola, cello, double_bass   |
| piano_trio      | piano, violin, cello                        |

## How It Works

```
YouTube URL
    ↓  yt-dlp + ffmpeg
WAV audio (44.1 kHz mono)
    ↓  Demucs (htdemucs)
Separated stems: vocals, bass, drums, other
    ↓  Basic Pitch (Spotify)
MIDI files per stem
    ↓  music21 (arrangement engine)
    ├→ Single: fit to instrument range, assign clef
    ├→ Auto: map each stem to a default instrument
    └→ Ensemble: distribute stems across requested parts
    ↓
MusicXML file → open in MuseScore
```

## Output

The tool generates `.musicxml` files in the output directory. Open them in MuseScore where you can:

- Edit notes, dynamics, and articulations
- Use **File → Parts** to extract individual instrument parts
- Print or export to PDF
- Play back with built-in synthesizer

## Notes

- Source separation and transcription are imperfect — expect to do some manual cleanup in MuseScore
- Simpler recordings (solo instruments, clear mixes) produce better results
- The `drums` stem is skipped for pitched instrument partitures
- First run downloads the Demucs AI model (~300MB)
