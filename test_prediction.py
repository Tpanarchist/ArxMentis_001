import tempfile
import unittest
from itertools import product
from pathlib import Path

from arxmentis import (
    contextual_adaptive_transition,
    dependent_transition,
    evaluate_criterion,
    memory_dependent_transition,
    plastic_transition,
    read_state,
    toggle_state,
    write_state,
)


def store_observed_transition_with_existing_laws(
    context: Path,
    observed_next: Path,
    model_zero: Path,
    model_one: Path,
) -> None:
    """Fixed composition: store observed_next in the model entry for context."""

    # XOR then plastic with selector=1 is assignment; with selector=0 the
    # pair cancels back to the old target. Complement context to address P0.
    toggle_state(context)
    dependent_transition(observed_next, model_zero)
    plastic_transition(observed_next, model_zero, context)
    toggle_state(context)

    # Original context directly addresses P1.
    dependent_transition(observed_next, model_one)
    plastic_transition(observed_next, model_one, context)


def load_prediction_with_existing_laws(
    context: Path,
    model_zero: Path,
    model_one: Path,
    prediction: Path,
) -> None:
    """Fixed composition: copy the context-selected model entry to prediction."""

    toggle_state(context)
    dependent_transition(model_zero, prediction)
    plastic_transition(model_zero, prediction, context)
    toggle_state(context)

    dependent_transition(model_one, prediction)
    plastic_transition(model_one, prediction, context)


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

    def test_existing_laws_acquire_and_predict_all_four_binary_transition_laws(
        self,
    ) -> None:
        for law in product((0, 1), repeat=2):
            with self.subTest(law=law):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    context = root / "context"
                    observed_next = root / "observed-next"
                    model_zero = root / "model-zero"
                    model_one = root / "model-one"

                    # Start both model entries wrong so successful acquisition
                    # cannot be attributed to initialization.
                    write_state(1 - law[0], model_zero)
                    write_state(1 - law[1], model_one)

                    # The environment/harness supplies one observation from
                    # each possible current state. The acquisition program is
                    # fixed and does not branch on context or observed value.
                    for current in (0, 1):
                        write_state(current, context)
                        write_state(law[current], observed_next)
                        store_observed_transition_with_existing_laws(
                            context,
                            observed_next,
                            model_zero,
                            model_one,
                        )
                        self.assertEqual(read_state(context), current)
                        self.assertEqual(read_state(observed_next), law[current])

                    self.assertEqual(
                        (read_state(model_zero), read_state(model_one)),
                        law,
                    )

                    # Prediction is also a fixed composition. D2 is deliberately
                    # initialized wrong, then overwritten before realization.
                    for current in (0, 1):
                        write_state(current, context)
                        write_state(1 - law[current], observed_next)
                        load_prediction_with_existing_laws(
                            context,
                            model_zero,
                            model_one,
                            observed_next,
                        )
                        predicted = read_state(observed_next)
                        self.assertEqual(predicted, law[current])

                        # Environment realizes its transition only after the
                        # prediction is already persisted.
                        write_state(law[current], context)
                        self.assertEqual(read_state(context), predicted)

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
