import tempfile
import unittest
from itertools import product
from pathlib import Path

from arxmentis import (
    dependent_transition,
    plastic_transition,
    read_state,
    toggle_state,
    write_state,
)


def store_observed_transition(
    context: Path,
    observed_next: Path,
    model_zero: Path,
    model_one: Path,
) -> None:
    toggle_state(context)
    dependent_transition(observed_next, model_zero)
    plastic_transition(observed_next, model_zero, context)
    toggle_state(context)

    dependent_transition(observed_next, model_one)
    plastic_transition(observed_next, model_one, context)


def candidate_laws(
    observations: list[tuple[int, int]],
) -> set[tuple[int, int]]:
    laws = set(product((0, 1), repeat=2))
    return {
        law
        for law in laws
        if all(law[current] == observed_next for current, observed_next in observations)
    }


def intervene_if_underdetermined(
    underdetermined: Path,
    environment: Path,
) -> None:
    """Toggle environment iff U was 0; preserve U afterward."""
    toggle_state(underdetermined)
    dependent_transition(underdetermined, environment)
    toggle_state(underdetermined)


def mark_context_one_observed(
    context: Path,
    underdetermined: Path,
) -> None:
    """Derived gated write: if context=1, set U to 1; else preserve U."""
    dependent_transition(context, underdetermined)
    plastic_transition(context, underdetermined, context)


class ActiveLearningTests(unittest.TestCase):
    def test_uncertainty_sensitive_intervention_reduces_model_ambiguity(
        self,
    ) -> None:
        # These are exactly the two laws that are passively indistinguishable
        # forever from initial environment state 0.
        for hidden_law in ((0, 0), (0, 1)):
            with self.subTest(hidden_law=hidden_law):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    environment = root / "environment"
                    context = root / "context"
                    underdetermined = root / "underdetermined"
                    model_zero = root / "model-zero"
                    model_one = root / "model-one"

                    write_state(0, environment)
                    write_state(0, context)
                    write_state(0, underdetermined)
                    write_state(1, model_zero)
                    write_state(1 - hidden_law[1], model_one)

                    observations: list[tuple[int, int]] = []

                    # First passive transition: both hidden-law candidates yield
                    # 0 -> 0, so ambiguity remains.
                    write_state(hidden_law[0], environment)
                    observations.append((0, read_state(environment)))
                    store_observed_transition(
                        context,
                        environment,
                        model_zero,
                        model_one,
                    )

                    candidates_after_passive = candidate_laws(observations)
                    self.assertEqual(
                        candidates_after_passive,
                        {(0, 0), (0, 1)},
                    )
                    self.assertEqual(read_state(underdetermined), 0)

                    # Counterfactual control: observing 0 -> 0 again would not
                    # reduce ambiguity.
                    no_intervention_candidates = candidate_laws(
                        observations + [(0, 0)]
                    )
                    self.assertEqual(
                        no_intervention_candidates,
                        candidates_after_passive,
                    )

                    # The same fixed action program is run for either hidden
                    # law. U=0 causes an intervention to the unobserved context.
                    intervene_if_underdetermined(
                        underdetermined,
                        environment,
                    )
                    self.assertEqual(read_state(environment), 1)

                    # Retain the intervention context before the revealing
                    # transition occurs. This action is committed before the
                    # successor observation exists.
                    toggle_state(context)
                    self.assertEqual(read_state(context), 1)

                    write_state(hidden_law[1], environment)
                    observations.append((1, read_state(environment)))

                    candidates_after_intervention = candidate_laws(observations)
                    self.assertEqual(candidates_after_intervention, {hidden_law})
                    self.assertLess(
                        len(candidates_after_intervention),
                        len(candidates_after_passive),
                    )

                    store_observed_transition(
                        context,
                        environment,
                        model_zero,
                        model_one,
                    )
                    mark_context_one_observed(
                        context,
                        underdetermined,
                    )

                    self.assertEqual(read_state(underdetermined), 1)
                    self.assertEqual(
                        (read_state(model_zero), read_state(model_one)),
                        hidden_law,
                    )

                    # With U=1, the same decision program no longer intervenes.
                    before = read_state(environment)
                    intervene_if_underdetermined(
                        underdetermined,
                        environment,
                    )
                    self.assertEqual(read_state(environment), before)


if __name__ == "__main__":
    unittest.main()
