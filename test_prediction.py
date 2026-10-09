import tempfile
import unittest
from itertools import product
from pathlib import Path

from arxmentis import (
    contextual_adaptive_transition,
    evaluate_criterion,
    memory_dependent_transition,
    read_state,
    toggle_state,
    write_state,
)


class PredictionCapabilityTests(unittest.TestCase):
    def test_existing_memory_learns_and_predicts_fixed_binary_change_law(
        self,
    ) -> None:
        for initial_environment in (0, 1):
            for law in (0, 1):
                with self.subTest(
                    initial_environment=initial_environment,
                    law=law,
                ):
                    with tempfile.TemporaryDirectory() as directory:
                        root = Path(directory)
                        environment = root / "environment"
                        prediction = root / "prediction"
                        memory = root / "memory"

                        write_state(initial_environment, environment)
                        write_state(initial_environment, prediction)
                        write_state(1 - law, memory)

                        # One observed environment transition identifies whether
                        # the fixed law is STAY (0) or FLIP (1). D2 still holds
                        # the previous environment value when evaluation occurs.
                        if law == 1:
                            toggle_state(environment)

                        _, learned_law = evaluate_criterion(
                            environment,
                            prediction,
                            memory,
                        )
                        self.assertEqual(learned_law, law)
                        self.assertEqual(read_state(memory), law)

                        # Existing memory-dependent dynamics first synchronize
                        # the retained previous value to the current environment.
                        _, synchronized = memory_dependent_transition(
                            prediction,
                            memory,
                        )
                        self.assertEqual(
                            synchronized,
                            read_state(environment),
                        )

                        # From here, D2 is advanced before the environment.
                        # Equality is checked externally afterward so evaluation
                        # does not overwrite the learned law in M.
                        for _ in range(8):
                            _, predicted_next = memory_dependent_transition(
                                prediction,
                                memory,
                            )

                            current_environment = read_state(environment)
                            expected_next = current_environment ^ law
                            self.assertEqual(predicted_next, expected_next)

                            if law == 1:
                                toggle_state(environment)

                            self.assertEqual(
                                read_state(prediction),
                                read_state(environment),
                            )
                            self.assertEqual(read_state(memory), law)

    def test_two_policy_bits_can_represent_all_four_binary_transition_laws(
        self,
    ) -> None:
        for next_from_zero, next_from_one in product((0, 1), repeat=2):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                policy_zero = root / "policy-zero"
                policy_one = root / "policy-one"
                write_state(next_from_zero, policy_zero)
                write_state(next_from_one, policy_one)

                for current in (0, 1):
                    selected = policy_zero if current == 0 else policy_one
                    expected = next_from_zero if current == 0 else next_from_one
                    self.assertEqual(read_state(selected), expected)

    def test_current_contextual_update_fails_direct_acquisition_for_one_entry(
        self,
    ) -> None:
        trajectories: dict[tuple[int, int], list[int]] = {}

        for context, observed_next in product((0, 1), repeat=2):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                driver = root / "driver"
                target = root / "target"
                memory = root / "memory"
                policy_zero = root / "policy-zero"
                policy_one = root / "policy-one"
                write_state(0, memory)
                write_state(0, policy_zero)
                write_state(0, policy_one)

                selected_policy = policy_zero if context == 0 else policy_one
                trajectory: list[int] = []

                # Direct model-acquisition interpretation:
                # D1 is the previous/current context and D2 is the observed
                # next environment value. Each observation is replayed while
                # retaining only the learned policies.
                for _ in range(6):
                    write_state(context, driver)
                    write_state(observed_next, target)
                    contextual_adaptive_transition(
                        driver,
                        target,
                        memory,
                        policy_zero,
                        policy_one,
                    )
                    trajectory.append(read_state(selected_policy))

                trajectories[(context, observed_next)] = trajectory

        self.assertEqual(trajectories[(0, 0)], [0, 0, 0, 0, 0, 0])
        self.assertEqual(trajectories[(0, 1)], [1, 1, 1, 1, 1, 1])
        self.assertEqual(trajectories[(1, 1)], [0, 0, 0, 0, 0, 0])
        self.assertEqual(trajectories[(1, 0)], [1, 0, 1, 0, 1, 0])


if __name__ == "__main__":
    unittest.main()
