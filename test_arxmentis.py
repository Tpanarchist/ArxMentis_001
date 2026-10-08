import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from arxmentis import main, read_state, toggle_state, write_state


class PersistentStateTests(unittest.TestCase):
    def test_missing_state_reads_as_zero(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state"
            self.assertEqual(read_state(path), 0)
            self.assertFalse(path.exists())

    def test_toggle_persists_the_changed_value(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state"

            self.assertEqual(toggle_state(path), (0, 1))
            self.assertEqual(read_state(path), 1)

    def test_cli_recovers_state_in_a_new_process(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state"
            script = Path(__file__).with_name("arxmentis.py")

            toggled = subprocess.run(
                [sys.executable, str(script), "toggle", "--state-file", str(path)],
                check=True,
                capture_output=True,
                text=True,
            )
            recovered = subprocess.run(
                [sys.executable, str(script), "read", "--state-file", str(path)],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertEqual(toggled.stdout.strip(), "0 -> 1")
            self.assertEqual(recovered.stdout.strip(), "1")

    def test_distinctions_persist_independently(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "distinction-1"
            second = Path(directory) / "distinction-2"

            write_state(1, first)
            self.assertEqual(read_state(second), 0)
            self.assertEqual(toggle_state(second), (0, 1))
            self.assertEqual(read_state(first), 1)
            self.assertEqual(read_state(second), 1)

    def test_cli_selects_the_second_distinction_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "distinction-1"
            second = Path(directory) / "distinction-2"
            output = io.StringIO()

            with (
                patch("arxmentis.DISTINCTION_STATE_FILES", {1: first, 2: second}),
                patch("sys.argv", ["arxmentis.py", "toggle", "--distinction", "2"]),
                redirect_stdout(output),
            ):
                main()

            self.assertEqual(output.getvalue().strip(), "0 -> 1")
            self.assertEqual(read_state(first), 0)
            self.assertEqual(read_state(second), 1)

    def test_pair_relation_is_derived_from_both_persistent_bits(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "distinction-1"
            second = Path(directory) / "distinction-2"

            for first_value, second_value in ((0, 0), (0, 1), (1, 0), (1, 1)):
                write_state(first_value, first)
                write_state(second_value, second)
                relation = read_state(first) ^ read_state(second)
                self.assertEqual(relation, int(first_value != second_value))

    def test_write_rejects_values_other_than_zero_or_one(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state"
            with self.assertRaises(ValueError):
                write_state(2, path)

    def test_read_rejects_corrupted_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state"
            path.write_text("not-a-bit\n", encoding="ascii")

            with self.assertRaises(ValueError):
                read_state(path)


if __name__ == "__main__":
    unittest.main()
