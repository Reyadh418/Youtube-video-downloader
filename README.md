# Tubermate

Tubermate is a terminal-first YouTube video downloader built with Python.
It is designed for a simple interactive flow:

1. Run the Tubermate command.
2. Paste a YouTube video link.
3. See numbered download options (video qualities and audio-only choices).
4. Enter a number to start downloading.
5. If a link or download fails, choose retry or cancel.

Current scope is intentionally focused on single-video downloads for a fast and reliable v1.

## Why Tubermate

- Clean terminal experience, no GUI required
- Interactive numbered menu for quality and format selection
- Single command launch after installation
- Clear retry/cancel behavior on failures
- Built on yt-dlp for robust extraction and downloads

## Planned V1 Feature Set

- Single video download from a YouTube URL
- Interactive prompt to enter URL
- Fetch and display available formats in numbered order
- Include audio-only download options in the same menu
- Download selected format with progress output
- Retry or cancel prompt when URL fetch or download fails

## Tech Stack

- Python 3.10+
- yt-dlp
- Optional but recommended: ffmpeg (for best audio handling and some merged formats)

## Installation

Two common install methods are supported.

### Option A: Install as a global CLI with pipx (recommended)

This is the easiest way to get the Tubermate command available in your terminal PATH.

1. Install pipx (one-time):

	py -m pip install --user pipx
	py -m pipx ensurepath

2. Restart your terminal.

3. Install Tubermate from the project folder:

	pipx install .

4. Run:

	Tubermate

### Option B: Install with pip (also works)

1. From the project folder:

	py -m pip install .

2. Ensure your Python Scripts directory is in PATH.
3. Run:

	Tubermate

## Usage Flow

After installation, run:

	Tubermate

Expected interaction:

1. App asks for YouTube video URL.
2. App fetches available formats.
3. App displays numbered options, for example:
   - 1) 1080p MP4
   - 2) 720p MP4
   - 3) Audio only (best)
4. You enter the option number.
5. Download starts.
6. If failure occurs, app asks:
   - Retry
   - Cancel

## ffmpeg Note

Some download combinations may require ffmpeg.

Windows quick setup example:

1. Install ffmpeg via package manager (for example winget or chocolatey), or download from the official ffmpeg site.
2. Add ffmpeg to PATH.
3. Verify:

	ffmpeg -version

If ffmpeg is not available, basic downloads can still work depending on the selected format.

## Project Status

This repository currently documents and prepares the v1 CLI behavior.
Implementation will focus first on reliable single-video downloading with interactive quality selection.

## Error Handling Expectations

- Invalid URL: prompt user to retry or cancel
- Network issues: prompt user to retry or cancel
- Unavailable format: return to menu or ask for a new selection
- Permission/path issues: show clear message and stop gracefully

## Roadmap

After v1 is stable, possible next steps:

- Custom output directory selection
- Default quality preferences
- Download history log
- Playlist support (future, not in v1)

## Development Setup

From the repository root:

1. Create virtual environment:

	py -m venv .venv

2. Activate on Windows PowerShell:

	.\.venv\Scripts\Activate.ps1

3. Install dependencies:

	py -m pip install -U pip
	py -m pip install yt-dlp

## Contributing

Contributions are welcome.

Suggested contribution style:

- Keep the CLI flow simple and predictable
- Preserve interactive numbered selection behavior
- Keep single-video reliability as top priority

## Disclaimer

Use this project responsibly and respect YouTube Terms of Service and copyright laws in your region.
