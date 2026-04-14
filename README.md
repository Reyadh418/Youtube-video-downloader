# Tubermate

Tubermate is a terminal app that downloads a single YouTube video from a link.
You run one command, paste a URL, choose a numbered quality option, and download.

## What It Does

- Interactive command-line flow, no GUI
- Numbered quality options: 1080p, 720p, 480p, 360p
- Each quality includes with-audio and video-only choices
- Audio download options
- Estimated size shown in the selection menu
- Retry/cancel prompts when link fetch or download fails
- Default download folder: `C:\Users\(username)\Downloads` (on your machine)

## Quick Start

If you already have Git and Python installed, use this fast setup:

```powershell
git clone https://github.com/Reyadh418/Youtube-video-downloader.git
cd Youtube-video-downloader
python -m pip install --user pipx
python -m pipx ensurepath
pipx install .
Tubermate
```

If you are new to this, do not worry. The complete beginner-friendly step-by-step guide is right below.

## Beginner Guide

This section is for complete beginners on Windows PowerShell.
You can copy and paste each command exactly as written.

### 1. Install Python (one-time)

Check if Python is already installed:

```powershell
python --version
```

If you see a version number (example `Python 3.13.x`), continue.
If not, install Python from the Microsoft Store or use this command:

```powershell
winget install -e --id Python.Python.3.13
```

Then restart PowerShell.

Install Git so you can clone the repository:

```powershell
winget install -e --id Git.Git
```

Then restart PowerShell and verify Git:

```powershell
git --version
```

### 2. Install pipx and set PATH (one-time)

```powershell
python -m pip install --user pipx
python -m pipx ensurepath
```

Close PowerShell and open it again.

Check pipx:

```powershell
pipx --version
```

### 3. Install ffmpeg and set PATH (recommended)

Install ffmpeg using winget:

```powershell
winget install --id Gyan.FFmpeg -e
```

Close PowerShell and open it again.

Verify ffmpeg:

```powershell
ffmpeg -version
```

Why this matters:

- ffmpeg enables high-quality video + audio merging
- ffmpeg enables MP3 conversion

### 4. Install Tubermate

Clone the repository and enter the project folder:

```powershell
git clone https://github.com/Reyadh418/Youtube-video-downloader.git
cd Youtube-video-downloader
```

Install Tubermate with pipx:

```powershell
pipx install .
```

Run Tubermate:

```powershell
Tubermate
```

### 5. Use Tubermate

1. Run `Tubermate`
2. Paste a YouTube video URL
3. Choose a number from the menu
4. Wait for download to finish

By default, files are saved to your Downloads folder.

### 6. Update Tubermate after code changes

If you changed the source code and want the command to use the new version:

```powershell
cd Youtube-video-downloader
pipx install --force .
```

### 7. Quick troubleshooting

If `Tubermate` command is not recognized:

```powershell
python -m pipx ensurepath
```

Then restart PowerShell.

If ffmpeg is not recognized:

```powershell
ffmpeg -version
```

If not found, reinstall ffmpeg and restart PowerShell.

## Option List Behavior

Tubermate always shows a stable menu layout:

1. 1080p with audio (progressive, may be lower without ffmpeg)
2. 1080p video only (or closest lower)
3. 720p with audio (progressive, may be lower without ffmpeg)
4. 720p video only (or closest lower)
5. 480p with audio (progressive, may be lower without ffmpeg)
6. 480p video only (or closest lower)
7. 360p with audio (progressive, may be lower without ffmpeg)
8. 360p video only (or closest lower)
9. Best available
10. Audio only (best original)
11. Audio only (MP3 192kbps) (only when ffmpeg is available)

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
- Without ffmpeg: high-quality options can still download as video-only.
- Without ffmpeg: with-audio options may fall back to lower progressive resolutions.
- With ffmpeg: Tubermate can merge high-resolution video + audio streams.
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
