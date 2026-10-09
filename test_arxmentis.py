import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from arxmentis import (
    adaptive_transition,
    copy_transition,
    contextual_adaptive_transition,
    dependent_transition,
    evaluate_criterion,
    main,
    memory_dependent_transition,
    plastic_transition,
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

    def test_action_outcome_value_depends_on_context(self) -> None:
        successful_actions: dict[int, set[str]] = {}

        for context in (0, 1):
            successful_actions[context] = set()
            for action_name in ("copy", "xor"):
                with tempfile.TemporaryDirectory() as directory:
                    driver = Path(directory) / "driver"
                    target = Path(directory) / "target"
                    memory = Path(directory) / "memory"
                    write_state(context, driver)
                    write_state(1, target)

                    if action_name == "copy":
                        copy_transition(driver, target, memory)
                    else:
                        dependent_transition(driver, target)

                    self.assertEqual(read_state(driver), context)
                    if read_state(target) == 0:
                        successful_actions[context].add(action_name)

        self.assertEqual(successful_actions, {0: {"copy"}, 1: {"xor"}})

    def test_contextual_policy_learning_does_not_interfere(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            driver = root / "driver"
            target = root / "target"
            memory = root / "memory"
            policy_zero = root / "policy-zero"
            policy_one = root / "policy-one"
            write_state(0, driver)
            write_state(1, target)
            write_state(0, memory)
            write_state(0, policy_zero)
            write_state(1, policy_one)

            contextual_adaptive_transition(
                driver, target, memory, policy_zero, policy_one
            )
            self.assertEqual((read_state(target), read_state(memory)), (1, 1))
            self.assertEqual(
                (read_state(policy_zero), read_state(policy_one)),
                (1, 1),
            )
            contextual_adaptive_transition(
                driver, target, memory, policy_zero, policy_one
            )
            self.assertEqual((read_state(target), read_state(memory)), (0, 0))
            self.assertEqual(
                (read_state(policy_zero), read_state(policy_one)),
                (1, 1),
            )

            write_state(1, driver)
            write_state(1, target)
            contextual_adaptive_transition(
                driver, target, memory, policy_zero, policy_one
            )
            self.assertEqual((read_state(target), read_state(memory)), (1, 1))
            self.assertEqual(
                (read_state(policy_zero), read_state(policy_one)),
                (1, 0),
            )
            contextual_adaptive_transition(
                driver, target, memory, policy_zero, policy_one
            )
            self.assertEqual((read_state(target), read_state(memory)), (0, 0))
            self.assertEqual(
                (read_state(policy_zero), read_state(policy_one)),
                (1, 0),
            )

            for context, expected_policy in ((0, 1), (1, 0)):
                write_state(context, driver)
                write_state(1, target)
                previous, current, error, policy, updated_policy = (
                    contextual_adaptive_transition(
                        driver, target, memory, policy_zero, policy_one
                    )
                )
                self.assertEqual((previous, current, error), (1, 0, 0))
                self.assertEqual((policy, updated_policy), (expected_policy,) * 2)
                self.assertEqual(
                    (read_state(policy_zero), read_state(policy_one)),
                    (1, 0),
                )

    def test_existing_policy_actions_cannot_prepare_for_next_context_from_zero(self) -> None:
        for policy_value in (0, 1):
            with self.subTest(policy_value=policy_value):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    driver = root / "driver"
                    target = root / "target"
                    memory = root / "memory"
                    policy_zero = root / "policy-zero"
                    policy_one = root / "policy-one"
                    write_state(0, driver)
                    write_state(0, target)
                    write_state(0, memory)
                    write_state(policy_value, policy_zero)
                    write_state(0, policy_one)

                    _, prepared_target, _, _, _ = contextual_adaptive_transition(
                        driver,
                        target,
                        memory,
                        policy_zero,
                        policy_one,
                    )
                    self.assertEqual(prepared_target, 0)
                    self.assertEqual(
                        (read_state(driver), read_state(target)),
                        (0, 0),
                    )

                    toggle_state(driver)
                    self.assertEqual(
                        evaluate_criterion(driver, target, memory),
                        (False, 1),
                    )
                    self.assertEqual(
                        (read_state(driver), read_state(target)),
                        (1, 0),
                    )

    def test_toggle_before_alternating_environment_change_preserves_equality(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            driver = root / "driver"
            target = root / "target"
            memory = root / "memory"
            write_state(0, driver)
            write_state(0, target)
            write_state(0, memory)

            for expected_context in (1, 0) * 4:
                self.assertEqual(
                    (read_state(driver), read_state(target)),
                    (1 - expected_context, 1 - expected_context),
                )

                toggle_state(target)
                self.assertEqual(
                    (read_state(driver), read_state(target)),
                    (1 - expected_context, expected_context),
                )

                toggle_state(driver)
                self.assertEqual(
                    (read_state(driver), read_state(target)),
                    (expected_context, expected_context),
                )
                self.assertEqual(
                    evaluate_criterion(driver, target, memory),
                    (True, 0),
                )

    def test_policy_receives_credit_after_environment_transition(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            driver = root / "driver"
            target = root / "target"
            memory = root / "memory"
            policy = root / "policy"
            write_state(0, driver)
            write_state(0, target)
            write_state(0, memory)
            write_state(0, policy)

            outcomes: list[int] = []
            policy_updates: list[tuple[int, int]] = []
            for _ in range(8):
                write_state(read_state(driver), target)
                self.assertEqual(read_state(target), read_state(driver))

                selected_policy = read_state(policy)
                if selected_policy == 1:
                    toggle_state(target)
                prepared_target = read_state(target)
                self.assertEqual(prepared_target, read_state(driver) ^ selected_policy)

                toggle_state(driver)
                post_environment_state = (
                    read_state(driver),
                    read_state(target),
                )
                satisfied, error = evaluate_criterion(driver, target, memory)
                updated_policy = selected_policy if satisfied else 1 - selected_policy
                write_state(updated_policy, policy)

                outcomes.append(error)
                policy_updates.append((selected_policy, updated_policy))
                self.assertEqual(satisfied, error == 0)
                self.assertEqual(
                    post_environment_state[0] ^ post_environment_state[1],
                    error,
                )

            self.assertEqual(outcomes, [1, 0, 0, 0, 0, 0, 0, 0])
            self.assertEqual(policy_updates, [(0, 1)] + [(1, 1)] * 7)
            self.assertEqual(read_state(policy), 1)

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

    def test_memory_changes_future_with_present_held_fixed(self) -> None:
        next_target_values: list[int] = []

        for memory_value in (0, 1):
            with tempfile.TemporaryDirectory() as directory:
                first = Path(directory) / "distinction-1"
                second = Path(directory) / "distinction-2"
                memory = Path(directory) / "memory"
                write_state(0, first)
                write_state(0, second)
                write_state(memory_value, memory)

                _, next_target = memory_dependent_transition(second, memory)
                next_target_values.append(next_target)
                self.assertEqual(
                    (read_state(first), read_state(second)),
                    (0, next_target),
                )

        self.assertEqual(next_target_values, [0, 1])

    def test_cli_applies_memory_dependent_transition(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "distinction-1"
            second = Path(directory) / "distinction-2"
            memory = Path(directory) / "memory"
            write_state(0, first)
            write_state(0, second)
            write_state(1, memory)
            output = io.StringIO()

            with (
                patch("arxmentis.DISTINCTION_STATE_FILES", {1: first, 2: second}),
                patch(
                    "sys.argv",
                    [
                        "arxmentis.py",
                        "memory-step",
                        "--distinction",
                        "2",
                        "--memory-file",
                        str(memory),
                    ],
                ),
                redirect_stdout(output),
            ):
                main()

            self.assertEqual(output.getvalue().strip(), "D2: 0 -> 1")
            self.assertEqual((read_state(first), read_state(second)), (0, 1))
            self.assertEqual(read_state(memory), 1)

    def test_history_selects_transition_for_same_present_pair(self) -> None:
        final_states: list[tuple[int, int, int]] = []

        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "distinction-1"
            second = Path(directory) / "distinction-2"
            memory = Path(directory) / "memory"
            write_state(0, first)
            write_state(0, second)
            write_state(0, memory)
            toggle_state(second)

            self.assertEqual((read_state(first), read_state(second)), (0, 1))
            self.assertEqual(read_state(memory), 0)
            plastic_transition(first, second, memory)
            final_states.append(
                (read_state(first), read_state(second), read_state(memory))
            )

        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "distinction-1"
            second = Path(directory) / "distinction-2"
            memory = Path(directory) / "memory"
            write_state(0, first)
            write_state(1, second)
            write_state(0, memory)
            copy_transition(first, second, memory)
            toggle_state(second)

            self.assertEqual((read_state(first), read_state(second)), (0, 1))
            self.assertEqual(read_state(memory), 1)
            plastic_transition(first, second, memory)
            final_states.append(
                (read_state(first), read_state(second), read_state(memory))
            )

        self.assertEqual(final_states, [(0, 1, 0), (0, 0, 1)])

    def test_adaptive_transition_retains_success_and_shifts_after_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "distinction-1"
            second = Path(directory) / "distinction-2"
            memory = Path(directory) / "memory"
            policy = Path(directory) / "policy"
            write_state(1, first)
            write_state(0, second)
            write_state(1, memory)
            write_state(0, policy)

            self.assertEqual(
                adaptive_transition(first, second, memory, policy),
                (0, 1, 0, 0, 0),
            )
            self.assertEqual(
                adaptive_transition(first, second, memory, policy),
                (1, 0, 1, 0, 1),
            )
            self.assertEqual(
                adaptive_transition(first, second, memory, policy),
                (0, 1, 0, 1, 1),
            )

            for _ in range(3):
                self.assertEqual(
                    adaptive_transition(first, second, memory, policy),
                    (1, 1, 0, 1, 1),
                )

    def test_all_sixteen_initial_configurations_reach_satisfying_fixed_points(
        self,
    ) -> None:
        tested_configurations = 0

        for driver_value in (0, 1):
            for target_value in (0, 1):
                for memory_value in (0, 1):
                    for policy_value in (0, 1):
                        with tempfile.TemporaryDirectory() as directory:
                            root = Path(directory)
                            driver = root / "driver"
                            target = root / "target"
                            memory = root / "memory"
                            policy = root / "policy"
                            write_state(driver_value, driver)
                            write_state(target_value, target)
                            write_state(memory_value, memory)
                            write_state(policy_value, policy)

                            for _ in range(16):
                                before = (
                                    read_state(driver),
                                    read_state(target),
                                    read_state(memory),
                                    read_state(policy),
                                )
                                adaptive_transition(driver, target, memory, policy)
                                after = (
                                    read_state(driver),
                                    read_state(target),
                                    read_state(memory),
                                    read_state(policy),
                                )
                                if before == after and after[0] == after[1]:
                                    break
                            else:
                                self.fail(
                                    "Adaptive loop did not reach a satisfying fixed point "
                                    f"from {(driver_value, target_value, memory_value, policy_value)}"
                                )

                            settled = after
                            self.assertEqual(settled[0], settled[1])
                            self.assertEqual(settled[2], 0)
                            self.assertEqual(
                                (
                                    read_state(driver),
                                    read_state(target),
                                    read_state(memory),
                                    read_state(policy),
                                ),
                                settled,
                            )
                            tested_configurations += 1

        self.assertEqual(tested_configurations, 16)

    def test_adaptation_recovers_after_environment_bit_changes(self) -> None:
        for initial_environment in (0, 1):
            with self.subTest(initial_environment=initial_environment):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    driver = root / "driver"
                    target = root / "target"
                    memory = root / "memory"
                    policy = root / "policy"
                    write_state(initial_environment, driver)
                    write_state(initial_environment, target)
                    write_state(0, memory)
                    write_state(initial_environment, policy)

                    settled_before = (
                        read_state(driver),
                        read_state(target),
                        read_state(memory),
                        read_state(policy),
                    )
                    self.assertEqual(settled_before[:3], (initial_environment,) * 2 + (0,))
                    self.assertEqual(
                        adaptive_transition(driver, target, memory, policy),
                        (
                            initial_environment,
                            initial_environment,
                            0,
                            initial_environment,
                            initial_environment,
                        ),
                    )

                    toggle_state(driver)
                    after_perturbation = (
                        read_state(driver),
                        read_state(target),
                        read_state(memory),
                        read_state(policy),
                    )
                    self.assertEqual(after_perturbation[0], 1 - initial_environment)
                    self.assertEqual(after_perturbation[1:], settled_before[1:])

                    cycle_count = 0
                    while cycle_count < 8:
                        adaptive_transition(driver, target, memory, policy)
                        cycle_count += 1
                        after = (
                            read_state(driver),
                            read_state(target),
                            read_state(memory),
                            read_state(policy),
                        )
                        is_fixed_point = (
                            after[0] == after[1]
                            and after[2] == 0
                            and (after[3] == 1 or after[0] == 0)
                        )
                        if is_fixed_point:
                            break
                    else:
                        self.fail("Adaptation did not recover after environment change")

                    settled_after = (
                        read_state(driver),
                        read_state(target),
                        read_state(memory),
                        read_state(policy),
                    )
                    self.assertEqual(settled_after[0], settled_after[1])
                    self.assertEqual(settled_after[2], 0)
                    self.assertEqual(
                        cycle_count,
                        3 if initial_environment == 0 else 1,
                    )
                    self.assertEqual(
                        adaptive_transition(driver, target, memory, policy),
                        (
                            settled_after[1],
                            settled_after[1],
                            0,
                            settled_after[3],
                            settled_after[3],
                        ),
                    )

    def test_adaptation_learns_from_alternating_environment_changes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            driver = root / "driver"
            target = root / "target"
            memory = root / "memory"
            policy = root / "policy"
            write_state(0, driver)
            write_state(0, target)
            write_state(0, memory)
            write_state(0, policy)

            recovery_cycles: list[int] = []
            for perturbation_index in range(8):
                state_before_perturbation = (
                    read_state(driver),
                    read_state(target),
                    read_state(memory),
                    read_state(policy),
                )
                self.assertEqual(state_before_perturbation[0], perturbation_index % 2)
                self.assertEqual(state_before_perturbation[0], state_before_perturbation[1])
                self.assertEqual(state_before_perturbation[2], 0)

                toggle_state(driver)
                after_perturbation = (
                    read_state(driver),
                    read_state(target),
                    read_state(memory),
                    read_state(policy),
                )
                self.assertEqual(after_perturbation[0], 1 - state_before_perturbation[0])
                self.assertEqual(after_perturbation[1:], state_before_perturbation[1:])

                cycle_count = 0
                while cycle_count < 8:
                    adaptive_transition(driver, target, memory, policy)
                    cycle_count += 1
                    recovered = (
                        read_state(driver),
                        read_state(target),
                        read_state(memory),
                        read_state(policy),
                    )
                    is_fixed_point = (
                        recovered[0] == recovered[1]
                        and recovered[2] == 0
                        and (recovered[3] == 1 or recovered[0] == 0)
                    )
                    if is_fixed_point:
                        break
                else:
                    self.fail(
                        "Adaptation did not recover after alternating "
                        "environment changes"
                    )

                recovery_cycles.append(cycle_count)
                self.assertEqual(recovered[0], recovered[1])
                self.assertEqual(recovered[2], 0)
                self.assertEqual(recovered[3], 1)

            self.assertEqual(recovery_cycles, [3, 1, 1, 1, 1, 1, 1, 1])
            self.assertEqual(read_state(policy), 1)

    def test_learned_policy_improves_recovery_after_task_state_reset(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            training = root / "training"
            training.mkdir()
            driver = training / "driver"
            target = training / "target"
            memory = training / "memory"
            policy = training / "policy"
            write_state(0, driver)
            write_state(0, target)
            write_state(0, memory)
            write_state(0, policy)

            toggle_state(driver)
            for training_cycles in range(1, 9):
                adaptive_transition(driver, target, memory, policy)
                trained_state = (
                    read_state(driver),
                    read_state(target),
                    read_state(memory),
                    read_state(policy),
                )
                if (
                    trained_state[0] == trained_state[1]
                    and trained_state[2] == 0
                    and (trained_state[3] == 1 or trained_state[0] == 0)
                ):
                    break
            else:
                self.fail("Training did not reach a satisfying fixed point")

            self.assertEqual(training_cycles, 3)
            learned_policy = read_state(policy)
            self.assertEqual(learned_policy, 1)

            task_state = (0, 0, 0)
            recovery_times: dict[int, int] = {}
            for policy_value in (0, learned_policy):
                trial = root / f"trial-{policy_value}"
                trial.mkdir()
                trial_driver = trial / "driver"
                trial_target = trial / "target"
                trial_memory = trial / "memory"
                trial_policy = trial / "policy"
                write_state(task_state[0], trial_driver)
                write_state(task_state[1], trial_target)
                write_state(task_state[2], trial_memory)
                write_state(policy_value, trial_policy)

                self.assertEqual(
                    (
                        read_state(trial_driver),
                        read_state(trial_target),
                        read_state(trial_memory),
                    ),
                    task_state,
                )
                toggle_state(trial_driver)
                self.assertEqual(
                    (
                        read_state(trial_driver),
                        read_state(trial_target),
                        read_state(trial_memory),
                    ),
                    (1, 0, 0),
                )

                for recovery_cycles in range(1, 9):
                    adaptive_transition(
                        trial_driver,
                        trial_target,
                        trial_memory,
                        trial_policy,
                    )
                    recovered = (
                        read_state(trial_driver),
                        read_state(trial_target),
                        read_state(trial_memory),
                        read_state(trial_policy),
                    )
                    if (
                        recovered[0] == recovered[1]
                        and recovered[2] == 0
                        and (recovered[3] == 1 or recovered[0] == 0)
                    ):
                        break
                else:
                    self.fail(
                        f"Policy {policy_value} did not recover after task reset"
                    )

                recovery_times[policy_value] = recovery_cycles

            self.assertEqual(recovery_times, {0: 3, learned_policy: 1})

    def test_cli_runs_adaptive_policy_evaluate_update_cycle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "distinction-1"
            second = Path(directory) / "distinction-2"
            memory = Path(directory) / "memory"
            policy = Path(directory) / "policy"
            write_state(1, first)
            write_state(0, second)
            write_state(0, memory)
            write_state(0, policy)
            output = io.StringIO()

            with (
                patch("arxmentis.DISTINCTION_STATE_FILES", {1: first, 2: second}),
                patch(
                    "sys.argv",
                    [
                        "arxmentis.py",
                        "adapt",
                        "--distinction",
                        "2",
                        "--memory-file",
                        str(memory),
                        "--policy-file",
                        str(policy),
                    ],
                ),
                redirect_stdout(output),
            ):
                main()

            self.assertEqual(
                output.getvalue().strip(),
                "D2: 0 -> 1; criterion satisfied; P=0 -> 0",
            )
            self.assertEqual((read_state(first), read_state(second)), (1, 1))
            self.assertEqual(read_state(memory), 0)
            self.assertEqual(read_state(policy), 0)

    def test_cli_runs_context_selected_adaptation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "distinction-1"
            second = Path(directory) / "distinction-2"
            memory = Path(directory) / "memory"
            policy_zero = Path(directory) / "policy-zero"
            policy_one = Path(directory) / "policy-one"
            write_state(1, first)
            write_state(1, second)
            write_state(0, memory)
            write_state(1, policy_zero)
            write_state(0, policy_one)
            output = io.StringIO()

            with (
                patch("arxmentis.DISTINCTION_STATE_FILES", {1: first, 2: second}),
                patch(
                    "sys.argv",
                    [
                        "arxmentis.py",
                        "adapt-context",
                        "--memory-file",
                        str(memory),
                        "--policy-file",
                        str(policy_zero),
                        "--policy-1-file",
                        str(policy_one),
                    ],
                ),
                redirect_stdout(output),
            ):
                main()

            self.assertEqual(
                output.getvalue().strip(),
                "D2: 1 -> 0; criterion satisfied; P1=0 -> 0",
            )
            self.assertEqual((read_state(first), read_state(second)), (1, 0))
            self.assertEqual((read_state(memory), read_state(policy_zero)), (0, 1))
            self.assertEqual(read_state(policy_one), 0)

    def test_cli_runs_memory_selected_transition(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "distinction-1"
            second = Path(directory) / "distinction-2"
            memory = Path(directory) / "memory"
            write_state(0, first)
            write_state(1, second)
            write_state(0, memory)
            output = io.StringIO()

            with (
                patch("arxmentis.DISTINCTION_STATE_FILES", {1: first, 2: second}),
                patch(
                    "sys.argv",
                    [
                        "arxmentis.py",
                        "plastic-step",
                        "--distinction",
                        "2",
                        "--memory-file",
                        str(memory),
                    ],
                ),
                redirect_stdout(output),
            ):
                main()

            self.assertEqual(output.getvalue().strip(), "D2: 1 -> 1")
            self.assertEqual((read_state(first), read_state(second)), (0, 1))

    def test_criterion_evaluation_writes_derived_mismatch_to_memory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "distinction-1"
            second = Path(directory) / "distinction-2"
            memory = Path(directory) / "memory"

            write_state(0, first)
            write_state(0, second)
            write_state(1, memory)
            self.assertEqual(evaluate_criterion(first, second, memory), (True, 0))
            self.assertEqual(read_state(memory), 0)

            write_state(0, first)
            write_state(1, second)
            self.assertEqual(evaluate_criterion(first, second, memory), (False, 1))
            self.assertEqual(read_state(memory), 1)

    def test_criterion_feedback_selects_later_transition_rule(self) -> None:
        final_states: list[tuple[int, int, int]] = []

        for second_value in (1, 0):
            with tempfile.TemporaryDirectory() as directory:
                first = Path(directory) / "distinction-1"
                second = Path(directory) / "distinction-2"
                memory = Path(directory) / "memory"
                write_state(1, first)
                write_state(second_value, second)
                write_state(0, memory)

                satisfied, selector = evaluate_criterion(first, second, memory)
                previous, current = plastic_transition(first, second, memory)
                final_states.append(
                    (read_state(first), read_state(second), read_state(memory))
                )

                if second_value == 1:
                    self.assertTrue(satisfied)
                    self.assertEqual(selector, 0)
                    self.assertEqual((previous, current), (1, 0))
                else:
                    self.assertFalse(satisfied)
                    self.assertEqual(selector, 1)
                    self.assertEqual((previous, current), (0, 1))

        self.assertEqual(final_states, [(1, 0, 0), (1, 1, 1)])

    def test_cli_evaluates_equality_and_updates_memory_selector(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "distinction-1"
            second = Path(directory) / "distinction-2"
            memory = Path(directory) / "memory"
            write_state(0, first)
            write_state(1, second)
            write_state(0, memory)
            output = io.StringIO()

            with (
                patch("arxmentis.DISTINCTION_STATE_FILES", {1: first, 2: second}),
                patch(
                    "sys.argv",
                    ["arxmentis.py", "evaluate", "--memory-file", str(memory)],
                ),
                redirect_stdout(output),
            ):
                main()

            self.assertEqual(output.getvalue().strip(), "criterion not satisfied; M=1")
            self.assertEqual(read_state(memory), 1)

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
