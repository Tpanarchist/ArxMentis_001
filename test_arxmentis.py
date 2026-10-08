import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from arxmentis import (
    copy_transition,
    dependent_transition,
    main,
    read_state,
    toggle_state,
    write_state,
)


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

    def test_dependent_transition_persists_target_and_preserves_driver(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            driver = Path(directory) / "driver"
            target = Path(directory) / "target"
            write_state(1, driver)
            write_state(0, target)

            self.assertEqual(dependent_transition(driver, target), (0, 1))
            self.assertEqual(read_state(driver), 1)
            self.assertEqual(read_state(target), 1)

    def test_cli_steps_the_selected_distinction_from_the_other(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "distinction-1"
            second = Path(directory) / "distinction-2"
            write_state(1, first)
            write_state(0, second)
            output = io.StringIO()

            with (
                patch("arxmentis.DISTINCTION_STATE_FILES", {1: first, 2: second}),
                patch("sys.argv", ["arxmentis.py", "step", "--distinction", "2"]),
                redirect_stdout(output),
            ):
                main()

            self.assertEqual(output.getvalue().strip(), "D2: 0 -> 1")
            self.assertEqual(read_state(first), 1)
            self.assertEqual(read_state(second), 1)

    def test_cli_copies_the_other_distinction_into_the_selected_one(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "distinction-1"
            second = Path(directory) / "distinction-2"
            memory = Path(directory) / "memory"
            write_state(0, first)
            write_state(1, second)
            output = io.StringIO()

            with (
                patch("arxmentis.DISTINCTION_STATE_FILES", {1: first, 2: second}),
                patch(
                    "sys.argv",
                    [
                        "arxmentis.py",
                        "copy",
                        "--distinction",
                        "2",
                        "--memory-file",
                        str(memory),
                    ],
                ),
                redirect_stdout(output),
            ):
                main()

            self.assertEqual(output.getvalue().strip(), "D2: 1 -> 0")
            self.assertEqual(read_state(first), 0)
            self.assertEqual(read_state(second), 0)
            self.assertEqual(read_state(memory), 1)

    def test_counterfactual_driver_value_changes_target_transition(self) -> None:
        next_target_values: list[int] = []

        for driver_value in (0, 1):
            with tempfile.TemporaryDirectory() as directory:
                driver = Path(directory) / "driver"
                target = Path(directory) / "target"
                write_state(driver_value, driver)
                write_state(0, target)

                _, next_target = dependent_transition(driver, target)
                next_target_values.append(next_target)

        self.assertEqual(next_target_values, [0, 1])

    def test_xor_transition_is_bijective_and_copy_is_not(self) -> None:
        states = ((0, 0), (0, 1), (1, 0), (1, 1))
        xor_futures: list[tuple[int, int]] = []
        copy_futures: list[tuple[int, int]] = []

        for first_value, second_value in states:
            with tempfile.TemporaryDirectory() as directory:
                first = Path(directory) / "distinction-1"
                second = Path(directory) / "distinction-2"
                write_state(first_value, first)
                write_state(second_value, second)
                dependent_transition(first, second)
                xor_futures.append((read_state(first), read_state(second)))

            with tempfile.TemporaryDirectory() as directory:
                first = Path(directory) / "distinction-1"
                second = Path(directory) / "distinction-2"
                memory = Path(directory) / "memory"
                write_state(first_value, first)
                write_state(second_value, second)
                copy_transition(first, second, memory)
                copy_futures.append((read_state(first), read_state(second)))

        self.assertEqual(set(xor_futures), set(states))
        self.assertEqual(len(xor_futures), len(set(xor_futures)))
        self.assertEqual(copy_futures, [(0, 0), (0, 0), (1, 1), (1, 1)])
        self.assertLess(len(set(copy_futures)), len(copy_futures))

    def test_repeated_copy_transition_reaches_and_keeps_a_fixed_point(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            driver = Path(directory) / "distinction-1"
            target = Path(directory) / "distinction-2"
            memory = Path(directory) / "memory"
            write_state(1, driver)
            write_state(0, target)

            copy_transition(driver, target, memory)
            settled_state = (read_state(driver), read_state(target))
            copy_transition(driver, target, memory)

            self.assertEqual(settled_state, (1, 1))
            self.assertEqual((read_state(driver), read_state(target)), settled_state)

    def test_memory_bit_distinguishes_collapsed_histories(self) -> None:
        initial_states: list[tuple[int, int]] = []
        final_states: list[tuple[int, int]] = []
        memory_values: list[int] = []

        for initial_target in (0, 1):
            with tempfile.TemporaryDirectory() as directory:
                first = Path(directory) / "distinction-1"
                second = Path(directory) / "distinction-2"
                memory = Path(directory) / "memory"
                write_state(0, first)
                write_state(initial_target, second)
                write_state(0, memory)
                initial_states.append((read_state(first), read_state(second)))

                copy_transition(first, second, memory)
                final_states.append((read_state(first), read_state(second)))
                memory_values.append(read_state(memory))

        self.assertEqual(initial_states, [(0, 0), (0, 1)])
        self.assertEqual(final_states, [(0, 0), (0, 0)])
        self.assertEqual(memory_values, [0, 1])

    def test_cli_reads_the_persisted_memory_bit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            memory = Path(directory) / "memory"
            write_state(1, memory)
            output = io.StringIO()

            with (
                patch(
                    "sys.argv",
                    ["arxmentis.py", "read-memory", "--memory-file", str(memory)],
                ),
                redirect_stdout(output),
            ):
                main()

            self.assertEqual(output.getvalue().strip(), "1")

    def test_transition_order_changes_the_final_state(self) -> None:
        final_states: list[tuple[int, int]] = []

        for targets in ((2, 1), (1, 2)):
            with tempfile.TemporaryDirectory() as directory:
                first = Path(directory) / "distinction-1"
                second = Path(directory) / "distinction-2"
                write_state(1, first)
                write_state(0, second)
                paths = {1: first, 2: second}

                for target_distinction in targets:
                    driver_distinction = 3 - target_distinction
                    dependent_transition(
                        paths[driver_distinction],
                        paths[target_distinction],
                    )

                final_states.append((read_state(first), read_state(second)))

        self.assertEqual(final_states, [(0, 1), (1, 1)])

    def test_repeated_dependent_transition_has_period_two(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            driver = Path(directory) / "distinction-1"
            target = Path(directory) / "distinction-2"
            write_state(1, driver)
            write_state(0, target)
            target_values = [read_state(target)]

            for _ in range(4):
                dependent_transition(driver, target)
                target_values.append(read_state(target))

        self.assertEqual(target_values, [0, 1, 0, 1, 0])

    def test_repeated_ordered_pair_has_period_three(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "distinction-1"
            second = Path(directory) / "distinction-2"
            write_state(1, first)
            write_state(0, second)
            paths = {1: first, 2: second}
            round_states = [(read_state(first), read_state(second))]

            for _ in range(3):
                for target_distinction in (2, 1):
                    driver_distinction = 3 - target_distinction
                    dependent_transition(
                        paths[driver_distinction],
                        paths[target_distinction],
                    )
                round_states.append((read_state(first), read_state(second)))

        self.assertEqual(round_states, [(1, 0), (0, 1), (1, 1), (1, 0)])

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
