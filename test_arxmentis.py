import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from arxmentis import read_state, toggle_state, write_state


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
