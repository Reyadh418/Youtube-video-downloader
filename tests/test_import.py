import unittest
from unittest.mock import patch

from tubermate.cli import _is_only_audio
from tubermate.cli import _is_without_audio
from tubermate.cli import _is_with_audio
from tubermate.cli import _split_options
from tubermate.cli import _ask_retry_or_cancel
from tubermate.cli import _read_choice
from tubermate.cli import main
from tubermate.downloader import FormatOption


class CliTests(unittest.TestCase):
    def test_main_callable(self) -> None:
        self.assertTrue(callable(main))

    def test_read_choice_after_invalid(self) -> None:
        inputs = iter(["x", "0", "2"])
        with patch("builtins.input", side_effect=lambda _: next(inputs)):
            self.assertEqual(_read_choice(3), 2)

    def test_retry_prompt(self) -> None:
        inputs = iter(["nope", "r"])
        with patch("builtins.input", side_effect=lambda _: next(inputs)):
            self.assertTrue(_ask_retry_or_cancel())

    def test_cancel_prompt(self) -> None:
        with patch("builtins.input", return_value="c"):
            self.assertFalse(_ask_retry_or_cancel())

    def test_main_cancel_on_invalid_url(self) -> None:
        inputs = iter(["bad-url", "c"])
        with patch("builtins.input", side_effect=lambda _: next(inputs)):
            main()

    def test_option_classification(self) -> None:
        with_audio = FormatOption(label="720p with audio (or closest lower)", format_selector="x")
        without_audio = FormatOption(label="720p video only (or closest lower)", format_selector="y")
        only_audio = FormatOption(label="Audio only (best original)", format_selector="z")

        self.assertTrue(_is_with_audio(with_audio))
        self.assertTrue(_is_without_audio(without_audio))
        self.assertTrue(_is_only_audio(only_audio))

    def test_split_options_order(self) -> None:
        options = [
            FormatOption(label="1080p with audio (or closest lower)", format_selector="1"),
            FormatOption(label="720p video only (or closest lower)", format_selector="2"),
            FormatOption(label="Audio only (best original)", format_selector="3"),
        ]
        with_audio, without_audio, only_audio = _split_options(options)

        self.assertEqual([option.label for option in with_audio], ["1080p with audio (or closest lower)"])
        self.assertEqual([option.label for option in without_audio], ["720p video only (or closest lower)"])
        self.assertEqual([option.label for option in only_audio], ["Audio only (best original)"])


if __name__ == "__main__":
    unittest.main()
