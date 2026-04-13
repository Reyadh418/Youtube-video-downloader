# Tubermate

Tubermate is a terminal app that downloads a single YouTube video from a link.
You run one command, paste a URL, choose a numbered quality option, and download.

## What It Does

- Interactive command-line flow, no GUI
- Numbered quality options: 1080p, 720p, 480p, 360p
- Audio download options
- Estimated size shown in the selection menu
- Retry/cancel prompts when link fetch or download fails
- Default download folder: `C:\Users\hp\Downloads` (on your machine)

## Beginner Guide

### 1. Requirements

- Python 3.10+
- pipx (recommended)
- Optional: ffmpeg for more/high-quality merged formats and MP3 conversion

### 2. Install (Recommended)

From the project root:

```powershell
python -m pip install --user pipx
python -m pipx ensurepath
```

Close and reopen the terminal, then run:

```powershell
pipx install .
```

Start the app:

```powershell
Tubermate
```

### 3. Use It

1. Run `Tubermate`
2. Paste a YouTube URL
3. Pick a number from the quality/audio list
4. Wait for download completion

Downloads are saved to your Downloads folder by default.

### 4. Update After Code Changes

If you edit source code and want your installed command to use latest changes:

```powershell
pipx install --force .
```

### 5. Common Fixes

If `Tubermate` command is not recognized:

```powershell
python -m pipx ensurepath
```

Then restart the terminal.

If ffmpeg is missing and you want best quality merges or MP3 conversion:

```powershell
ffmpeg -version
```

If command not found, install ffmpeg and add it to PATH.

## Option List Behavior

Tubermate always shows a stable menu layout:

1. 1080p (or closest lower)
2. 720p (or closest lower)
3. 480p (or closest lower)
4. 360p (or closest lower)
5. Best available
6. Audio only (best original)
7. Audio only (MP3 192kbps) (only when ffmpeg is available)

Notes:

- `or closest lower` means Tubermate falls back automatically if exact quality is unavailable.
- Size values are estimates (prefixed with `~`).

## Tech Deep Dive (For Enthusiasts)

### Stack

- Python packaging via `pyproject.toml`
- `yt-dlp` for extraction and download execution
- Console entry point: `Tubermate = tubermate.cli:main`

### Current Architecture

```text
.
|- pyproject.toml
|- requirements.txt
|- src/
|  |- tubermate/
|     |- __init__.py
|     |- cli.py
|     |- downloader.py
|- tests/
   |- test_import.py
```

### Format Selection Strategy

- A fixed, user-friendly option set is rendered for consistency.
- Internally, each quality option maps to yt-dlp selector expressions.
- Without ffmpeg: selectors prefer progressive streams with both video+audio.
- With ffmpeg: selectors can combine separate best video + best audio streams.
- Audio options:
  - `bestaudio/best`
  - MP3 192 kbps post-processing with FFmpeg (if available)

### Size Estimation Strategy

Estimated sizes are computed from metadata in this order:

1. `filesize`
2. `filesize_approx`
3. Fallback estimate via bitrate and duration

Displayed values are approximate and intended for decision support before download.

### Error Handling Model

- URL validation checks for YouTube domains (`youtube.com`, `youtu.be`)
- Failures in metadata fetch prompt `Retry or cancel? (r/c)`
- Download failures also prompt retry/cancel
- Invalid menu input is handled with repeated prompt until valid

### Download Output

- Default output directory is `Path.home() / "Downloads"`
- Output template: `%(title)s.%(ext)s`

### Dev Workflow

Install in editable mode (local development path):

```powershell
python -m pip install -e .
```

Run tests:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

Reinstall pipx command after changes:

```powershell
pipx install --force .
```

## Known Limitations

- Single-video focus only (no playlist support yet)
- Size values are estimates, not exact final bytes
- Some YouTube formats depend on external tools/runtime changes over time

## Legal and Responsible Use

Use Tubermate responsibly and in compliance with:

- YouTube Terms of Service
- Local copyright laws and content licensing rules
