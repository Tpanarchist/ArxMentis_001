"""Evidence regressions; historical tests and runtime remain untouched."""
from __future__ import annotations

import tempfile
import unittest
from itertools import permutations, product
from pathlib import Path

import arxmentis as runtime
import composition_experiments as research


class CompositionEvidenceTests(unittest.TestCase):
    def test_derived_gated_write_over_all_inputs_and_physical_assignments(self) -> None:
        # This is a sequence of existing laws, not a gated_write runtime primitive.
        with tempfile.TemporaryDirectory() as directory:
            physical = tuple(Path(directory) / name for name in ("A", "B", "C", "unused"))
            for paths in permutations(physical):
                for d, t, s, guard in product((0, 1), repeat=4):
                    initial = (d, t, s, guard)
                    actual = research.execute(initial, (
                        ("xor", (0, 1)), ("plastic", (0, 1, 2)),
                    ), paths)
                    with self.subTest(paths=paths, initial=initial):
                        self.assertEqual(actual, (d, t if s == 0 else d, s, guard))

    def test_gate_order_is_essential(self) -> None:
        forward = research.sample_program(3, (("xor", (0, 1)), ("plastic", (0, 1, 2))))
        reverse = research.sample_program(3, (("plastic", (0, 1, 2)), ("xor", (0, 1))))
        self.assertNotEqual(forward, reverse)
        self.assertEqual(research.states(3)[forward[5]], (1, 1, 1))
        self.assertEqual(research.states(3)[reverse[5]], (1, 0, 1))

    def test_memory_named_law_is_role_remapped_dependent_xor(self) -> None:
        self.assertEqual(research.sample_program(3, (("memory", (1, 2)),)),
                         research.sample_program(3, (("xor", (2, 1)),)))

    def test_copy_full_effect_differs_from_plastic_copy_branch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = tuple(Path(directory) / name for name in ("d", "t", "s"))
            copied = research.execute((1, 0, 1), (("copy", (0, 1, 2)),), paths)
            selected = research.execute((1, 0, 1), (("plastic", (0, 1, 2)),), paths)
            self.assertEqual(copied, (1, 1, 0))
            self.assertEqual(selected, (1, 1, 1))
            self.assertEqual(copied[:2], selected[:2])
            self.assertNotEqual(copied, selected)

    def test_copy_pair_fixed_point_is_not_immediate_full_state_fixed_point(self) -> None:
        first = research.sample_program(3, (("copy", (0, 1, 2)),))
        second = research.sample_program(3, (("copy", (0, 1, 2)),) * 2)
        self.assertEqual(len(set(first)), 4)  # Old s is erased even though old t is retained.
        self.assertNotEqual(first, second)
        self.assertEqual(research.compose(second, first), second)

    def test_two_bit_closure_saturates_at_every_permutation(self) -> None:
        basis = research.sample_basis(2, research.two_bit_basis())
        found, counts, saturated = research.closure(basis, 8)
        self.assertTrue(saturated)
        self.assertEqual(counts, [1, 4, 9, 7, 3, 0])
        self.assertEqual(set(found), set(permutations(range(4))))
        self.assertTrue(all(research.transport(table) in found for table in found))

    def test_bfs_matches_independent_word_enumeration_and_shortest_lengths(self) -> None:
        basis = research.sample_basis(3, research.three_bit_basis())
        found, counts, saturated = research.closure(basis, 3)
        brute: dict[research.Table, int] = {}
        for length in range(4):
            for program in product(tuple(basis), repeat=length):
                table = research.program_table(program, basis)
                brute.setdefault(table, length)
        self.assertFalse(saturated)
        self.assertEqual(counts, [1, 8, 42, 147])
        self.assertEqual(set(found), set(brute))
        self.assertTrue(all(len(witness) == brute[table] for table, witness in found.items()))

    def test_every_short_closure_witness_replays_against_actual_files(self) -> None:
        operations = research.three_bit_basis()
        basis = research.sample_basis(3, operations)
        found, counts, saturated = research.closure(basis, 4)
        self.assertEqual(counts, [1, 8, 42, 147, 340])
        self.assertFalse(saturated)
        for table, witness in found.items():
            with self.subTest(witness=witness):
                actual = research.sample_program(3, tuple(operations[name] for name in witness))
                self.assertEqual(actual, table)

    def test_resource_cap_never_returns_false_complete_counts(self) -> None:
        basis = research.sample_basis(2, research.two_bit_basis())
        with self.assertRaisesRegex(RuntimeError, "resource cap"):
            research.closure(basis, 8, max_tables=2)

    def test_recoded_gate_uses_existing_composition_and_preserves_selector(self) -> None:
        gate_ops: tuple[research.Operation, ...] = (("xor", (0, 1)), ("plastic", (0, 1, 2)))
        gate = research.sample_program(3, gate_ops)
        transported = research.transport(gate)
        self.assertNotEqual(gate, transported)
        operations: tuple[research.Operation, ...] = (
            ("toggle", (2,)), *gate_ops, ("toggle", (2,)),
        )
        self.assertEqual(research.role_remapping_check(operations, transported), 48)
        for i, (d, t, s) in enumerate(research.states(3)):
            self.assertEqual(research.states(3)[transported[i]], (d, d if s == 0 else t, s))

    def test_all_bounded_transport_absences_have_existing_longer_support(self) -> None:
        basis = research.sample_basis(3, research.three_bit_basis())
        found, _, _ = research.closure(basis, 4)
        phi = ("toggle(d)", "toggle(t)", "toggle(s)")
        for table, witness in found.items():
            self.assertEqual(research.program_table(phi + witness + phi, basis),
                             research.transport(table))

    def test_adapt_reduces_including_every_persistent_output(self) -> None:
        direct = research.sample_program(4, (("adapt", (0, 1, 2, 3)),))
        lower = research.sample_program(4, (
            ("plastic", (0, 1, 3)), ("evaluate", (0, 1, 2)), ("xor", (2, 3)),
        ))
        self.assertEqual(direct, lower)

    def test_prediction_state_map_reduces_without_scratch_side_effect(self) -> None:
        direct = research.sample_program(3, (("predict", (0, 2)),))
        lower = research.sample_program(3, (
            ("evaluate", (0, 1, 2)), ("xor", (1, 2)), ("toggle", (2,)),
        ))
        self.assertEqual(direct, lower)
        for i, (d, t, _) in enumerate(research.states(3)):
            self.assertEqual(research.states(3)[lower[i]], (d, t, 1 - d))

    def test_context_protocol_reduces_with_explicit_host_branch(self) -> None:
        self.assertEqual(research.sample_program(5, (("context", (0, 1, 2, 3, 4)),)),
                         research.contextual_lower_table())

    def test_search_keeps_all_shortest_support_and_exposes_instance_overfit(self) -> None:
        basis = research.sample_basis(2, research.two_bit_basis())
        solutions = research.shortest_solutions(basis, lambda table: table[2] == 1, 4)
        self.assertEqual(len(solutions), 5)
        self.assertEqual({len(program) for program in solutions}, {2})
        self.assertEqual(len({research.program_table(p, basis) for p in solutions}), 4)
        swapped = (0, 2, 1, 3)
        for program in solutions:
            table = research.program_table(program, basis)
            self.assertNotEqual(table, swapped)
        # The first shortest solution transfers to the other unequal instance,
        # but breaks both equal instances of the intended swap class.
        self.assertEqual(research.program_table(solutions[0], basis), (3, 2, 1, 0))

    def test_class_search_swap_reuses_across_instances_paths_and_complement(self) -> None:
        operations = research.two_bit_basis()
        basis = research.sample_basis(2, operations)
        swap = (0, 2, 1, 3)
        solutions = research.shortest_solutions(basis, lambda table: table == swap, 4)
        self.assertEqual(len(solutions), 2)
        self.assertEqual({len(program) for program in solutions}, {3})
        self.assertEqual(research.transport(swap), swap)
        with tempfile.TemporaryDirectory() as directory:
            physical = (Path(directory) / "A", Path(directory) / "B")
            for paths in permutations(physical):
                for program in solutions:
                    for state in research.states(2):
                        self.assertEqual(research.execute(state, tuple(operations[n] for n in program), paths),
                                         tuple(reversed(state)))

    def test_low_level_copy_and_evaluation_reductions_replay_full_tables(self) -> None:
        copied = research.sample_program(3, (("copy", (0, 1, 2)),))
        evaluated = research.sample_program(3, (("evaluate", (0, 1, 2)),))
        self.assertEqual(copied, research.sample_program(3, (
            ("evaluate", (0, 1, 2)), ("xor", (2, 1)), ("xor", (0, 2)),
        )))
        self.assertEqual(evaluated, research.sample_program(3, (
            ("copy", (0, 1, 2)), ("xor", (0, 2)), ("xor", (2, 1)),
        )))

    def test_plastic_has_a_nonaffine_effect_missing_from_other_candidates(self) -> None:
        basis = research.sample_basis(3, research.three_bit_basis())
        for name, table in basis.items():
            self.assertEqual(research.is_affine(table), name != "plastic(d,t,s)")
        self.assertFalse(research.is_affine(research.program_table(
            ("xor(d,t)", "plastic(d,t,s)"), basis)))
        # Affine maps remain affine under composition; this is an all-length
        # obstruction, not a failure to find a short nonaffine word.
        affine = {name: table for name, table in basis.items() if research.is_affine(table)}
        found, _, _ = research.closure(affine, 4)
        self.assertTrue(all(research.is_affine(table) for table in found))

    def test_gated_write_has_an_alternative_witness_without_dependent_xor(self) -> None:
        gate = research.sample_program(3, (("xor", (0, 1)), ("plastic", (0, 1, 2))))
        alternative = research.sample_program(3, (("plastic", (0, 1, 2)),) * 2)
        self.assertEqual(gate, alternative)

    def test_aliasing_is_excluded_explicitly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "same"
            with self.assertRaisesRegex(ValueError, "distinct"):
                research.execute((0, 1), (("xor", (0, 1)),), (path, path))
            # Runtime itself permits aliasing; it has different behavior.
            runtime.write_state(1, path)
            runtime.dependent_transition(path, path)
            self.assertEqual(runtime.read_state(path), 0)



class MechanismReificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ops3 = research.role_complete_basis(3)
        cls.raw3 = research.sample_basis(3, cls.ops3)
        cls.b3, cls.aliases3 = research.canonical_basis(cls.raw3)
        cls.ops4 = research.role_complete_basis(4)
        cls.raw4 = research.sample_basis(4, cls.ops4)
        cls.b4, cls.aliases4 = research.canonical_basis(cls.raw4)
        cls.initial = tuple(range(0, 16, 2))
        cls.target3 = research.controlled_swap_table()
        cls.required = tuple(2 * value for value in cls.target3)
        cls.words, cls.search = research.meet_shortest_programs(cls.b4, cls.initial, cls.required)
        cls.normal = research.sample_program(4, research.selected_swap_workspace_program())
        cls.recoded = research.transport_mask(cls.normal, 8)
        cls.recoded_words, cls.recoded_search = research.meet_shortest_programs(
            cls.b4, cls.initial, tuple(cls.recoded[i] for i in cls.initial))

    def test_target_is_verified_nonaffine_bijection_with_degree_two(self) -> None:
        self.assertEqual(self.target3, (0, 1, 2, 3, 4, 6, 5, 7))
        self.assertEqual(len(set(self.target3)), 8)
        self.assertFalse(research.is_affine(self.target3))
        anf = research.algebraic_normal_form(self.target3)
        self.assertEqual(anf['degrees'], [1, 2, 2])
        self.assertEqual(anf['terms_by_output_coordinate'],
                         [[[0]], [[1], [0, 2], [0, 1]], [[2], [0, 2], [0, 1]]])
        for i, (c, a, b) in enumerate(research.states(3)):
            self.assertEqual(research.states(3)[self.target3[i]],
                             (c, a ^ (c & (a ^ b)), b ^ (c & (a ^ b))))

    def test_every_distinct_role_assignment_satisfies_proof_premises(self) -> None:
        self.assertEqual((len(self.raw3), len(self.b3)), (33, 24))
        self.assertEqual((len(self.raw4), len(self.b4)), (100, 76))
        expected_ranks = {'toggle': 8, 'xor': 8, 'memory': 8,
                          'copy': 4, 'evaluate': 4, 'plastic': 6}
        for name, operation in self.ops3.items():
            kind, roles = operation
            self.assertEqual(len(set(roles)), len(roles))
            self.assertEqual(len(set(self.raw3[name])), expected_ranks[kind])
            self.assertEqual(research.is_affine(self.raw3[name]), kind != 'plastic')
        for name, operation in self.ops4.items():
            self.assertEqual(len(set(operation[1])), len(operation[1]))
            if len(set(self.raw4[name])) == 16:
                self.assertTrue(research.is_affine(self.raw4[name]))

    def test_three_bit_bijections_exhaust_and_first_rank_loss_cannot_recover(self) -> None:
        bijective = {name: table for name, table in self.b3.items() if len(set(table)) == 8}
        group, counts, saturated = research.closure(bijective, 12, 5_000)
        self.assertTrue(saturated)
        self.assertEqual(len(group), 1344)
        self.assertEqual(counts, [1, 9, 51, 187, 393, 474, 215, 14, 0])
        self.assertNotIn(self.target3, group)
        noninjective = [t for t in self.b3.values() if len(set(t)) < 8]
        for prefix in group:
            for irreversible in noninjective:
                self.assertLess(len(set(research.compose(prefix, irreversible))), 8)
        retained, _, _ = research.closure(research.sample_basis(3, research.three_bit_basis()), 4)
        self.assertEqual(len(retained), 538)
        self.assertNotIn(self.target3, retained)

    def test_bidirectional_search_matches_independent_small_word_search(self) -> None:
        basis = research.sample_basis(2, research.two_bit_basis())
        expected = research.shortest_solutions(basis, lambda t: t == (0, 2, 1, 3), 3)
        actual, _ = research.meet_shortest_programs(basis, (0, 1, 2, 3), (0, 2, 1, 3), 1, 2)
        self.assertEqual(set(actual), set(expected))
        # A noninjective map has multiple preimages. A single chosen inverse
        # would silently lose valid paths; the backward search must keep all.
        layers, _ = research.backward_frontiers({'erase': (0, 0, 2, 2)}, (0, 2), 1)
        self.assertEqual(set(layers[0]) | set(layers[1]),
                         {bytes(x) for x in ((0, 2), (0, 3), (1, 2), (1, 3))})
        with self.assertRaisesRegex(RuntimeError, 'resource cap'):
            research.backward_frontiers({'erase': (0, 0, 2, 2)}, (0, 2), 1, max_tables=2)

    def test_complete_six_step_search_has_all_support_and_no_shorter_solution(self) -> None:
        self.assertEqual(self.search['minimum_length'], 6)
        self.assertEqual(self.search['forward_new_at_length'], [1, 22, 394, 6226])
        self.assertEqual(self.search['backward_new_at_length'], [1, 13, 2422, 51970])
        self.assertEqual(self.search['meeting_counts'],
                         [{'prefix_length': 3, 'suffix_length': 3, 'maps': 38}])
        self.assertEqual(len(self.words), 502)
        self.assertEqual({len(word) for word in self.words}, {6})
        classes = set()
        label_count = 0
        for word in self.words:
            table = research.program_table(word, self.b4)
            self.assertEqual(tuple(table[i] for i in self.initial), self.required)
            classes.add(table)
            count = 1
            for name in word:
                count *= len(self.aliases4[name])
            label_count += count
        self.assertEqual(len(classes), 22)
        self.assertEqual(label_count, 5008)
        self.assertEqual({len(set(t)) for t in classes}, {8})

    def test_all_full_behavioral_classes_have_real_file_representatives(self) -> None:
        representatives: dict[research.Table, research.Program] = {}
        for word in self.words + self.recoded_words:
            representatives.setdefault(research.program_table(word, self.b4), word)
        self.assertEqual(len(representatives), 44)
        for table, word in representatives.items():
            actual = research.sample_program(4, tuple(self.ops4[name] for name in word))
            self.assertEqual(actual, table)

    def test_workspace_witness_preserves_injectivity_on_admissible_domain(self) -> None:
        prefix = tuple(range(16))
        for operation in research.selected_swap_workspace_program():
            prefix = research.compose(prefix, research.sample_program(4, (operation,)))
            self.assertEqual(len(set(prefix[i] for i in self.initial)), 8)
            self.assertEqual(len(set(prefix)), 8)  # Old workspace erased by first copy.
            self.assertTrue(all((prefix[i] >> 3) == (i >> 3) for i in range(16)))
        self.assertEqual(tuple(prefix[i] for i in self.initial), self.required)

    def test_workspace_initialization_and_total_domain_are_separate_claims(self) -> None:
        normalized = tuple(2 * self.target3[i // 2] for i in range(16))
        preserved_workspace = tuple(2 * self.target3[i // 2] + (i & 1) for i in range(16))
        self.assertEqual(self.normal, normalized)
        self.assertNotEqual(self.normal, preserved_workspace)
        self.assertEqual(len(set(self.normal)), 8)
        self.assertEqual(len(set(preserved_workspace)), 16)
        self.assertFalse(research.is_affine(preserved_workspace))
        # Initialization is unnecessary for selected data behavior; an unknown
        # W is overwritten, not returned intact. The W=0 restoration contract
        # describes the chosen reusable workspace subset.
        for i in range(0, 16, 2):
            self.assertEqual(self.normal[i], self.normal[i + 1])
            self.assertEqual(self.normal[i] & 1, 0)

    def test_selector_is_causally_consumed_and_reused_without_harness_branch(self) -> None:
        operations = research.selected_swap_workspace_program()
        with tempfile.TemporaryDirectory() as directory:
            paths = tuple(Path(directory) / name for name in ('C', 'A', 'B', 'W'))
            outputs = []
            for c in (0, 1):
                research.execute((c, 0, 1, 0), operations, paths)
                outputs.append((runtime.read_state(paths[1]), runtime.read_state(paths[2])))
                saved_selector = paths[0].read_bytes()
                for a, b in ((1, 0), (0, 0), (1, 1), (0, 1)) * 2:
                    runtime.write_state(a, paths[1])
                    runtime.write_state(b, paths[2])
                    for operation in operations:
                        research.apply_operation(operation, paths)
                        self.assertEqual(paths[0].read_bytes(), saved_selector)
                    self.assertEqual(tuple(runtime.read_state(p) for p in paths),
                                     research.states(4)[self.normal[(c << 3) | (a << 2) | (b << 1)]])
            self.assertEqual(outputs, [(0, 1), (1, 0)])

    def test_physical_role_permutations_and_unused_fifth_carrier(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            physical = tuple(Path(directory) / name for name in (
                '.arxmentis-state', '.arxmentis-state-2', '.arxmentis-memory', '.arxmentis-policy'))
            guard = Path(directory) / '.arxmentis-policy-1'
            for paths in permutations(physical):
                for c, a, b, untouched in product((0, 1), repeat=4):
                    for operations, table in (
                        (research.selected_swap_workspace_program(), self.normal),
                        (research.recoded_swap_workspace_program(), self.recoded),
                    ):
                        actual = research.execute((c, a, b, 0, untouched), operations, (*paths, guard))
                        expected = research.states(4)[table[(c << 3) | (a << 2) | (b << 1)]]
                        self.assertEqual(actual, (*expected, untouched))

    def test_selector_only_recoding_has_another_minimal_six_step_executor(self) -> None:
        self.assertNotEqual(self.normal, self.recoded)
        self.assertEqual(research.sample_program(4, research.recoded_swap_workspace_program()), self.recoded)
        self.assertEqual(self.recoded_search['minimum_length'], 6)
        self.assertEqual(len(self.recoded_words), 384)
        conjugated: tuple[research.Operation, ...] = (
            ('toggle', (0,)), *research.selected_swap_workspace_program(), ('toggle', (0,)),
        )
        self.assertEqual(research.sample_program(4, conjugated), self.recoded)
        for c, a, b in research.states(3):
            expected = (c, a ^ ((1 - c) & (a ^ b)), b ^ ((1 - c) & (a ^ b)), 0)
            self.assertEqual(research.states(4)[self.recoded[(c << 3) | (a << 2) | (b << 1)]], expected)

    def test_fixed_executor_consumes_selector_persisted_across_processes(self) -> None:
        import subprocess
        import sys
        child = ("from pathlib import Path; import sys; import composition_experiments as r; "
                 "paths=tuple(Path(p) for p in sys.argv[1:]); "
                 "[r.apply_operation(op,paths) for op in r.selected_swap_workspace_program()]")
        with tempfile.TemporaryDirectory() as directory:
            paths = tuple(Path(directory) / name for name in ('C', 'A', 'B', 'W'))
            for c in (0, 1):
                research.execute((c, 0, 1, 0), (), paths)
                for a, b in ((0, 1), (1, 0)):
                    runtime.write_state(a, paths[1])
                    runtime.write_state(b, paths[2])
                    subprocess.run([sys.executable, '-B', '-c', child, *(str(p) for p in paths)],
                                   check=True, capture_output=True, text=True,
                                   cwd=Path(__file__).resolve().parent)
                    self.assertEqual(tuple(runtime.read_state(p) for p in paths),
                                     research.states(4)[self.normal[(c << 3) | (a << 2) | (b << 1)]])


if __name__ == "__main__":
    unittest.main()
