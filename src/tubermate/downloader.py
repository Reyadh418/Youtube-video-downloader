from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
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


def _seconds_to_eta(seconds: float | int | None) -> str:
    if seconds is None:
        return "--:--"
    total_seconds = max(0, int(seconds))
    minutes, secs = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def _make_progress_hook() -> Any:
    state: dict[str, Any] = {
        "last_line_len": 0,
        "finished": False,
    }

    def _render_progress_line(data: dict[str, Any]) -> None:
        status = data.get("status")

        if status == "downloading":
            downloaded = float(data.get("downloaded_bytes") or 0)
            total = data.get("total_bytes") or data.get("total_bytes_estimate")
            total_float = float(total) if total else 0.0
            percent = (downloaded / total_float * 100.0) if total_float > 0 else 0.0
            percent = min(100.0, max(0.0, percent))

            bar_width = 20
            filled = int((percent / 100.0) * bar_width)
            bar = "#" * filled + "-" * (bar_width - filled)

            progress_text = f"{_bytes_to_text(downloaded)}/{_bytes_to_text(total_float) if total_float > 0 else '?'}"
            speed_text = _bytes_to_text(data.get("speed")) + "/s" if data.get("speed") else "--/s"
            eta_text = _seconds_to_eta(data.get("eta"))

            line = f"{percent:3.0f}%[{bar}] {progress_text} {speed_text} ETA {eta_text}"
            pad_len = max(0, int(state["last_line_len"]) - len(line))
            sys.stdout.write("\r" + line + (" " * pad_len))
            sys.stdout.flush()
            state["last_line_len"] = len(line)
            return

        if status == "finished" and not state["finished"]:
            line = "100%[####################] Completed"
            pad_len = max(0, int(state["last_line_len"]) - len(line))
            sys.stdout.write("\r" + line + (" " * pad_len) + "\n")
            sys.stdout.flush()
            state["finished"] = True

    return _render_progress_line


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
    best_audio = _pick_best_audio_only(formats)

    for height in target_resolutions:
        best_progressive = _pick_best_progressive(formats, height)
        best_video_only = _pick_best_video_only(formats, height)

        if ffmpeg_available:
            merged_est = (_estimate_bytes(best_video_only, duration) if best_video_only else None)
            audio_est = (_estimate_bytes(best_audio, duration) if best_audio else None)
            if merged_est and audio_est:
                merged_est += audio_est
            elif audio_est and not merged_est:
                merged_est = audio_est

            merged_size_text = _bytes_to_text(merged_est)
            merged_suffix = f" | ~{merged_size_text}" if merged_size_text else ""
            merged_selector = (
                f"bestvideo[height<={height}][vcodec!=none]+bestaudio"
                f"/best[height<={height}][vcodec!=none][acodec!=none]"
            )
            options.append(
                FormatOption(
                    label=f"{height}p with audio (or closest lower){merged_suffix}",
                    format_selector=merged_selector,
                    requires_ffmpeg=True,
                )
            )
        else:
            progressive_est = _estimate_bytes(best_progressive, duration) if best_progressive else None
            progressive_size_text = _bytes_to_text(progressive_est)
            progressive_suffix = f" | ~{progressive_size_text}" if progressive_size_text else ""
            progressive_selector = (
                f"best[height<={height}][vcodec!=none][acodec!=none]"
                f"/best[vcodec!=none][acodec!=none]"
            )
            options.append(
                FormatOption(
                    label=f"{height}p with audio (progressive, may be lower without ffmpeg){progressive_suffix}",
                    format_selector=progressive_selector,
                )
            )

        video_only_est = _estimate_bytes(best_video_only, duration) if best_video_only else None
        video_only_size_text = _bytes_to_text(video_only_est)
        video_only_suffix = f" | ~{video_only_size_text}" if video_only_size_text else ""
        video_only_selector = f"bestvideo[height<={height}][vcodec!=none]/best[height<={height}]"
        options.append(
            FormatOption(
                label=f"{height}p video only (or closest lower){video_only_suffix}",
                format_selector=video_only_selector,
            )
        )

    return options


def fetch_video_data(url: str) -> VideoData:
    if not _is_youtube_url(url):
        raise InvalidYoutubeUrlError("Please enter a valid YouTube video URL.")

    ydl_opts: dict[str, Any] = {
        "quiet": True,
        "noplaylist": True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    formats = info.get("formats", [])
    duration = info.get("duration")
    options = _video_options(formats, duration)
    best_audio = _pick_best_audio_only(formats)

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
        raise RuntimeError("No downloadable formats found for this video.")

    title = info.get("title") or "Unknown title"
    return VideoData(title=title, options=options)


def download_video(url: str, option: FormatOption, output_dir: str | None = None) -> None:
    out_dir = Path(output_dir) if output_dir else (Path.home() / "Downloads")
    out_dir.mkdir(parents=True, exist_ok=True)

    ydl_opts: dict[str, Any] = {
        "format": option.format_selector,
        "noplaylist": True,
        "outtmpl": str(out_dir / "%(title)s.%(ext)s"),
        "quiet": True,
        "noprogress": True,
        "progress_hooks": [_make_progress_hook()],
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
