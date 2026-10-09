import unittest

from formalism import (
    bits_required,
    can_predict_all_binary_deterministic_laws,
    can_predict_fixed_binary_change_laws,
    can_represent_all_binary_context_mappings,
    can_retain_binary_past,
    minimum_states_for_all_binary_context_mappings,
    minimum_states_for_all_binary_deterministic_prediction,
    minimum_states_for_binary_past,
    minimum_states_for_fixed_binary_change_prediction,
)


class FormalMinimalityTests(unittest.TestCase):
    def test_one_state_cannot_retain_one_lost_binary_distinction(self) -> None:
        self.assertFalse(can_retain_binary_past(1))

    def test_two_states_can_retain_one_lost_binary_distinction(self) -> None:
        self.assertTrue(can_retain_binary_past(2))
        self.assertEqual(minimum_states_for_binary_past(), 2)
        self.assertEqual(bits_required(2), 1)

    def test_fewer_than_four_states_cannot_encode_all_two_context_binary_policies(
        self,
    ) -> None:
        for state_count in (1, 2, 3):
            with self.subTest(state_count=state_count):
                self.assertFalse(
                    can_represent_all_binary_context_mappings(state_count)
                )

    def test_four_states_encode_all_two_context_binary_policies(self) -> None:
        self.assertTrue(can_represent_all_binary_context_mappings(4))
        self.assertEqual(
            minimum_states_for_all_binary_context_mappings(),
            4,
        )
        self.assertEqual(bits_required(4), 2)

    def test_one_model_state_cannot_predict_both_stay_and_flip_laws(self) -> None:
        self.assertFalse(can_predict_fixed_binary_change_laws(1))

    def test_two_model_states_are_minimal_for_stay_and_flip_prediction(self) -> None:
        self.assertTrue(can_predict_fixed_binary_change_laws(2))
        self.assertEqual(
            minimum_states_for_fixed_binary_change_prediction(),
            2,
        )
        self.assertEqual(bits_required(2), 1)

    def test_fewer_than_four_model_states_cannot_represent_all_binary_laws(
        self,
    ) -> None:
        for state_count in (1, 2, 3):
            with self.subTest(state_count=state_count):
                self.assertFalse(
                    can_predict_all_binary_deterministic_laws(state_count)
                )

    def test_four_model_states_are_minimal_for_all_binary_laws(self) -> None:
        self.assertTrue(can_predict_all_binary_deterministic_laws(4))
        self.assertEqual(
            minimum_states_for_all_binary_deterministic_prediction(),
            4,
        )
        self.assertEqual(bits_required(4), 2)


if __name__ == "__main__":
    unittest.main()
