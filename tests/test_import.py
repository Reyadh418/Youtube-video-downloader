import unittest
from unittest.mock import patch

from tubermate.cli import _ask_retry_or_cancel
from tubermate.cli import _read_choice
from tubermate.cli import main


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


if __name__ == "__main__":
    unittest.main()
