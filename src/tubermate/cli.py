from __future__ import annotations

from tubermate.downloader import download_video, fetch_video_data


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
        raw = input("Select an option number: ").strip()
        if not raw.isdigit():
            print("Enter a valid number.")
            continue
        number = int(raw)
        if 1 <= number <= max_choice:
            return number
        print(f"Please choose a number between 1 and {max_choice}.")


def main() -> None:
    print("Tubermate")
    print("Single video downloader")

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

    options = video_data.options
    print(f"Title: {video_data.title}")
    print("Available download options:")
    for idx, option in enumerate(options, start=1):
        print(f"{idx}. {option.label}")

    selected_index = _read_choice(len(options)) - 1
    selected = options[selected_index]

    while True:
        try:
            print(f"Starting download: {selected.label}")
            if selected.requires_ffmpeg:
                print("This selection requires ffmpeg to be installed and available in PATH.")
            download_video(url=url, option=selected)
            print("Download complete.")
            return
        except Exception as exc:
            print(f"Download failed: {exc}")
            if not _ask_retry_or_cancel():
                print("Cancelled.")
                return


if __name__ == "__main__":
    main()
