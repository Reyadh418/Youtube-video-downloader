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


def _bytes_to_text(value: float | int | None) -> str:
    if not value:
        return ""
    units = ["B", "KB", "MB", "GB"]
    size = float(value)
    unit_idx = 0
    while size >= 1024 and unit_idx < len(units) - 1:
        size /= 1024
        unit_idx += 1
    return f"{size:.1f}{units[unit_idx]}"


def _estimate_bytes(fmt: dict[str, Any], duration: float | None) -> float | None:
    direct = fmt.get("filesize") or fmt.get("filesize_approx")
    if direct:
        return float(direct)
    tbr = fmt.get("tbr")
    if tbr and duration:
        return float(tbr) * 1000.0 / 8.0 * float(duration)
    return None


def _pick_best_progressive(formats: list[dict[str, Any]], target_height: int) -> dict[str, Any] | None:
    candidates = [
        fmt
        for fmt in formats
        if fmt.get("vcodec") not in (None, "none")
        and fmt.get("acodec") not in (None, "none")
        and isinstance(fmt.get("height"), int)
        and int(fmt["height"]) <= target_height
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda fmt: (int(fmt.get("height") or 0), float(fmt.get("tbr") or 0.0)), reverse=True)[0]


def _pick_best_video_only(formats: list[dict[str, Any]], target_height: int) -> dict[str, Any] | None:
    candidates = [
        fmt
        for fmt in formats
        if fmt.get("vcodec") not in (None, "none")
        and isinstance(fmt.get("height"), int)
        and int(fmt["height"]) <= target_height
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda fmt: (int(fmt.get("height") or 0), float(fmt.get("tbr") or 0.0)), reverse=True)[0]


def _pick_best_audio_only(formats: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [
        fmt
        for fmt in formats
        if fmt.get("vcodec") in (None, "none") and fmt.get("acodec") not in (None, "none")
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda fmt: float(fmt.get("abr") or fmt.get("tbr") or 0.0), reverse=True)[0]


def _has_ffmpeg() -> bool:
    return which("ffmpeg") is not None


def _video_options(formats: list[dict[str, Any]], duration: float | None) -> list[FormatOption]:
    ffmpeg_available = _has_ffmpeg()
    options: list[FormatOption] = []
    target_resolutions = [1080, 720, 480, 360]

    for height in target_resolutions:
        if ffmpeg_available:
            best_video = _pick_best_video_only(formats, height)
            best_audio = _pick_best_audio_only(formats)
            est_size = (_estimate_bytes(best_video, duration) if best_video else None)
            audio_size = (_estimate_bytes(best_audio, duration) if best_audio else None)
            if est_size and audio_size:
                est_size += audio_size
            elif audio_size and not est_size:
                est_size = audio_size
            size_text = _bytes_to_text(est_size)
            suffix = f" | ~{size_text}" if size_text else ""
            selector = (
                f"bestvideo[height<={height}]+bestaudio"
                f"/best[height<={height}][vcodec!=none][acodec!=none]"
            )
            options.append(
                FormatOption(
                    label=f"{height}p (or closest lower){suffix}",
                    format_selector=selector,
                    requires_ffmpeg=True,
                )
            )
            continue

        best_progressive = _pick_best_progressive(formats, height)
        est_size = _estimate_bytes(best_progressive, duration) if best_progressive else None
        size_text = _bytes_to_text(est_size)
        suffix = f" | ~{size_text}" if size_text else ""
        selector = f"best[height<={height}][vcodec!=none][acodec!=none]/best[height<={height}]"
        options.append(
            FormatOption(
                label=f"{height}p (or closest lower){suffix}",
                format_selector=selector,
            )
        )

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

    formats = info.get("formats", [])
    duration = info.get("duration")
    options = _video_options(formats, duration)

    best_progressive = _pick_best_progressive(formats, 10000)
    best_video = _pick_best_video_only(formats, 10000)
    best_audio = _pick_best_audio_only(formats)
    if _has_ffmpeg():
        best_est = (_estimate_bytes(best_video, duration) if best_video else None)
        best_audio_est = (_estimate_bytes(best_audio, duration) if best_audio else None)
        if best_est and best_audio_est:
            best_est += best_audio_est
        elif best_audio_est and not best_est:
            best_est = best_audio_est
    else:
        best_est = _estimate_bytes(best_progressive, duration) if best_progressive else None
    best_size_text = _bytes_to_text(best_est)
    best_suffix = f" | ~{best_size_text}" if best_size_text else ""
    options.append(FormatOption(label=f"Best available{best_suffix}", format_selector="best"))

    audio_est = _estimate_bytes(best_audio, duration) if best_audio else None
    audio_size_text = _bytes_to_text(audio_est)
    audio_suffix = f" | ~{audio_size_text}" if audio_size_text else ""
    options.append(FormatOption(label=f"Audio only (best original){audio_suffix}", format_selector="bestaudio/best"))
    if _has_ffmpeg():
        mp3_est = float(duration) * 192000.0 / 8.0 if duration else None
        mp3_size_text = _bytes_to_text(mp3_est)
        mp3_suffix = f" | ~{mp3_size_text}" if mp3_size_text else ""
        options.append(
            FormatOption(
                label=f"Audio only (MP3 192kbps){mp3_suffix}",
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
    out_dir = Path(output_dir) if output_dir else (Path.home() / "Downloads")
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
