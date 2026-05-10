from __future__ import annotations

from tubermate.downloader import FormatOption, PlaylistDownloadResult, PlaylistDownloadSummary, PlaylistEntry
from tubermate.downloader import download_video, fetch_first_playable_video_data, fetch_video_data, fetch_playlist_entries


def _ask_retry_or_cancel() -> bool:
    while True:
        choice = input("Retry or cancel? (r/c): ").strip().lower()
        if choice in {"r", "retry"}:
            return True
        if choice in {"c", "cancel"}:
            return False
        print("Please enter r for retry or c for cancel.")


def _read_choice(max_choice: int) -> int:
    while True:
        raw = input(f"Select an option number (1-{max_choice}): ").strip()
        if not raw.isdigit():
            print("Enter a valid number.")
            continue
        number = int(raw)
        if 1 <= number <= max_choice:
            return number
        print(f"Please choose a number between 1 and {max_choice}.")


def _is_only_audio(option: FormatOption) -> bool:
    label = option.label.lower()
    return option.extract_audio or label.startswith("audio only")


def _is_without_audio(option: FormatOption) -> bool:
    return "video only" in option.label.lower()


def _is_with_audio(option: FormatOption) -> bool:
    return not _is_only_audio(option) and not _is_without_audio(option)


def _split_options(options: list[FormatOption]) -> tuple[list[FormatOption], list[FormatOption], list[FormatOption]]:
    with_audio = [option for option in options if _is_with_audio(option)]
    without_audio = [option for option in options if _is_without_audio(option)]
    only_audio = [option for option in options if _is_only_audio(option)]
    return with_audio, without_audio, only_audio


def _download_playlist(entries: list[PlaylistEntry], selected: FormatOption) -> PlaylistDownloadSummary:
    total = len(entries)
    results: list[PlaylistDownloadResult] = []
    succeeded = 0
    failed = 0
    skipped = 0

    for idx, entry in enumerate(entries, start=1):
        print()
        print(f"Downloading {idx}/{total}: {entry.title}")
        if "video only" in selected.label.lower():
            print("Note: this selection is video-only and may not include audio.")
        if selected.requires_ffmpeg:
            print("This selection requires ffmpeg to be installed and available in PATH.")

        while True:
            try:
                print("Preparing download...")
                download_video(url=entry.url, option=selected)
                print()
                print(f"Completed {idx}/{total}: {entry.title}")
                succeeded += 1
                results.append(PlaylistDownloadResult(title=entry.title, url=entry.url, status="succeeded"))
                break
            except Exception as exc:
                print(f"Download failed for {entry.title}: {exc}")
                if _ask_retry_or_cancel():
                    print("Retrying...")
                    continue
                skipped += 1
                results.append(PlaylistDownloadResult(title=entry.title, url=entry.url, status="skipped", error=str(exc)))
                print("Skipping current item.")
                break

    return PlaylistDownloadSummary(total=total, succeeded=succeeded, failed=failed, skipped=skipped, results=results)


def main() -> None:
    print("Tubermate")
    print()

    # Ask whether user wants single video or playlist
    while True:
        mode_input = input("Download single video or playlist? (s/p): ").strip()
        mode = mode_input.lower()
        # Backwards-compatible: if user entered a URL (or any non s/p), treat as single-video URL
        if mode in {"s", "single"}:
            is_playlist = False
            break
        if mode in {"p", "playlist"}:
            is_playlist = True
            break
        # treat any other input as the video URL (legacy behavior / test compatibility)
        url = mode_input
        is_playlist = False
        break
    print()

    if not is_playlist:
        # single video flow (unchanged) — if `url` was provided at the mode prompt, reuse it
        if "url" in locals() and url:
            try:
                video_data = fetch_video_data(url)
            except Exception as exc:
                print(f"Could not fetch formats: {exc}")
                if not _ask_retry_or_cancel():
                    print("Cancelled.")
                    return
        else:
            while True:
                url = input("Enter YouTube video URL: ").strip()
                if not url:
                    print("URL cannot be empty.")
                    continue

                try:
                    video_data = fetch_video_data(url)
                    break
                except Exception as exc:
                    print(f"Could not fetch formats: {exc}")
                    if not _ask_retry_or_cancel():
                        print("Cancelled.")
                        return
    else:
        # playlist flow
        while True:
            playlist_url = input("Enter YouTube playlist URL: ").strip()
            if not playlist_url:
                print("URL cannot be empty.")
                continue
            try:
                entries = fetch_playlist_entries(playlist_url)
                break
            except Exception as exc:
                print(f"Could not fetch playlist: {exc}")
                if not _ask_retry_or_cancel():
                    print("Cancelled.")
                    return

        print(f"Found {len(entries)} entries. Fetching options from the first playable video...")
        try:
            video_data, playable_entry = fetch_first_playable_video_data(entries)
        except Exception as exc:
            print(str(exc))
            return
        print(f"Using options from: {playable_entry.title}")

    options = video_data.options
    print(f"Title: {video_data.title}")
    with_audio, without_audio, only_audio = _split_options(options)
    flat_options = with_audio + without_audio + only_audio

    print()
    print("Available download options")
    print("-" * 28)
    current_number = 1

    if with_audio:
        print("A. With Audio Options")
        for option in with_audio:
            print(f"{current_number:>2}. {option.label}")
            current_number += 1
        print()

    if without_audio:
        print("B. Without Audio Options")
        for option in without_audio:
            print(f"{current_number:>2}. {option.label}")
            current_number += 1
        print()

    if only_audio:
        print("C. Only Audio Options")
        for option in only_audio:
            print(f"{current_number:>2}. {option.label}")
            current_number += 1
        print()

    selected_index = _read_choice(len(flat_options)) - 1
    selected = flat_options[selected_index]

    if not is_playlist:
        while True:
            try:
                print()
                print(f"Starting download: {selected.label}")
                if "video only" in selected.label.lower():
                    print("Note: this selection is video-only and may not include audio.")
                if selected.requires_ffmpeg:
                    print("This selection requires ffmpeg to be installed and available in PATH.")
                print("Preparing download...")
                download_video(url=url, option=selected)
                print()
                print("Download complete.")
                return
            except Exception as exc:
                print(f"Download failed: {exc}")
                if not _ask_retry_or_cancel():
                    print("Cancelled.")
                    return
    else:
        # playlist: download each entry sequentially using selected option
        summary = _download_playlist(entries, selected)
        print()
        print("Playlist download complete.")
        print(f"Summary: {summary.succeeded}/{summary.total} succeeded, {summary.failed} failed, {summary.skipped} skipped.")
        skipped_titles = [result.title for result in summary.results if result.status == "skipped"]
        if skipped_titles:
            print("Skipped items: " + ", ".join(skipped_titles))


if __name__ == "__main__":
    main()
