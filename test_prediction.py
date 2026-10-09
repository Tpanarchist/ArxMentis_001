import tempfile
import unittest
from pathlib import Path

from arxmentis import (
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


if __name__ == "__main__":
    unittest.main()
