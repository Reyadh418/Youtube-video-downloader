from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from shutil import which

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError


@dataclass
class FormatOption:
    label: str
    format_selector: str
    extract_audio: bool = False
    requires_ffmpeg: bool = False


@dataclass
class VideoData:
    title: str
    options: list[FormatOption]


class InvalidYoutubeUrlError(ValueError):
    pass


def _is_youtube_url(url: str) -> bool:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        return False
    host = parsed.netloc.lower()
    return "youtube.com" in host or "youtu.be" in host


def _filesize_text(fmt: dict[str, Any]) -> str:
    value = fmt.get("filesize") or fmt.get("filesize_approx")
    if not value:
        return ""
    units = ["B", "KB", "MB", "GB"]
    size = float(value)
    unit_idx = 0
    while size >= 1024 and unit_idx < len(units) - 1:
        size /= 1024
        unit_idx += 1
    return f"{size:.1f}{units[unit_idx]}"


def _has_ffmpeg() -> bool:
    return which("ffmpeg") is not None


def _video_options(formats: list[dict[str, Any]]) -> list[FormatOption]:
    keyed_options: dict[str, FormatOption] = {}
    ffmpeg_available = _has_ffmpeg()

    for fmt in formats:
        if fmt.get("vcodec") == "none":
            continue

        format_id = fmt.get("format_id")
        height = fmt.get("height")
        ext = (fmt.get("ext") or "unknown").upper()
        fps = fmt.get("fps")
        acodec = fmt.get("acodec")

        if not format_id or not height:
            continue

        key = f"{height}:{ext}:{int(fps) if fps else 0}"
        has_audio = acodec not in (None, "none")
        requires_ffmpeg = not has_audio

        if requires_ffmpeg and not ffmpeg_available:
            continue

        size_text = _filesize_text(fmt)
        suffix = f" | {size_text}" if size_text else ""
        fps_text = f" {int(fps)}fps" if fps else ""
        ffmpeg_text = " | requires ffmpeg" if requires_ffmpeg else ""
        label = f"{height}p {ext}{fps_text}{suffix}{ffmpeg_text}"

        if has_audio:
            selector = format_id
        else:
            selector = f"{format_id}+bestaudio/best"

        candidate = FormatOption(
            label=label,
            format_selector=selector,
            requires_ffmpeg=requires_ffmpeg,
        )

        existing = keyed_options.get(key)
        if existing is None:
            keyed_options[key] = candidate
            continue
        if existing.requires_ffmpeg and not candidate.requires_ffmpeg:
            keyed_options[key] = candidate

    options = list(keyed_options.values())
    options.sort(key=lambda item: int(item.label.split("p", 1)[0]), reverse=True)
    return options


def fetch_video_data(url: str) -> VideoData:
    if not _is_youtube_url(url):
        raise InvalidYoutubeUrlError("Please enter a valid YouTube video URL.")

    ydl_opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    options = _video_options(info.get("formats", []))
    options.append(FormatOption(label="Audio only (best original)", format_selector="bestaudio/best"))
    if _has_ffmpeg():
        options.append(
            FormatOption(
                label="Audio only (MP3 192kbps)",
                format_selector="bestaudio/best",
                extract_audio=True,
                requires_ffmpeg=True,
            )
        )

    if not options:
        options = [FormatOption(label="Best available", format_selector="best")]

    title = info.get("title") or "Unknown title"
    return VideoData(title=title, options=options)


def download_video(url: str, option: FormatOption, output_dir: str | None = None) -> None:
    out_dir = Path(output_dir) if output_dir else Path.cwd()
    out_dir.mkdir(parents=True, exist_ok=True)

    ydl_opts: dict[str, Any] = {
        "format": option.format_selector,
        "noplaylist": True,
        "outtmpl": str(out_dir / "%(title)s.%(ext)s"),
    }
    if option.extract_audio:
        ydl_opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ]

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def is_download_error(exc: Exception) -> bool:
    return isinstance(exc, DownloadError)
