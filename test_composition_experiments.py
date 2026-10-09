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


class FactorizedSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        import json
        cls.operations = research.role_complete_basis(5)
        cls.raw = research.sample_basis(5, cls.operations)
        cls.basis, cls.aliases = research.canonical_basis(cls.raw)
        cls.target = research.family_table(research.factorized_family(), True)
        cls.evidence = json.loads(Path('composition_results.json').read_text(encoding='utf-8'))['factorized_selection']

    def test_complete_target_and_independent_selected_data_composition(self) -> None:
        expected = (0,1,2,3,4,6,5,7,10,11,8,9,13,15,12,14)
        self.assertEqual(research.family_table(research.factorized_family()), expected)
        # Independent runtime mechanisms, including the historical three-XOR swap.
        toggle = research.sample_program(2, (('toggle',(0,)),))
        swap = research.sample_program(2, (('xor',(0,1)),('xor',(1,0)),('xor',(0,1))))
        identity = tuple(range(4))
        for c0,c1 in research.states(2):
            self.assertEqual(research.compose(toggle if c0 else identity, swap if c1 else identity),
                             research.factorized_family()[2*c0+c1])
        self.assertNotEqual(research.compose(toggle, swap), research.compose(swap, toggle))
        self.assertEqual(research.compose(toggle,swap),(1,3,0,2))
        self.assertEqual(research.compose(swap,toggle),(2,0,3,1))

    def test_no_workspace_proof_is_rederived_for_every_four_role_call(self) -> None:
        target = research.family_table(research.factorized_family())
        self.assertEqual(len(set(target)),16)
        self.assertFalse(research.is_affine(target))
        self.assertEqual(research.algebraic_normal_form(target)['degree'],2)
        raw = research.sample_basis(4,research.role_complete_basis(4))
        for table in raw.values():
            if len(set(table))==16:
                self.assertTrue(research.is_affine(table))
            if not research.is_affine(table):
                self.assertLess(len(set(table)),16)

    def test_symbolic_encoding_matches_every_five_bit_primitive_table(self) -> None:
        self.assertEqual((len(self.raw),len(self.basis)),(225,175))
        tables = tuple(self.basis.values())
        words, evidence = research.symbolic_program_search(5,tuple(range(32)),tables[0],1,
                                                           max_programs=256,alternatives=tables)
        self.assertTrue(evidence['enumeration_complete'])
        self.assertEqual(len(words),175)
        call_tables = {op:self.raw[name] for name,op in self.operations.items()}
        self.assertEqual({call_tables[word[0]] for word in words},set(tables))
        goals=evidence['goal_witnesses']
        assert isinstance(goals,dict)
        for index,word in goals.items():
            self.assertEqual(call_tables[word[0]],tables[index])

    def test_constraint_search_independently_matches_complete_small_enumeration(self) -> None:
        tables=research.sample_basis(2,research.two_bit_basis())
        expected=research.shortest_solutions(tables,lambda t:t==(0,2,1,3),3)
        expected_ops={tuple(research.two_bit_basis()[name] for name in w) for w in expected}
        words,e=research.symbolic_program_search(2,(0,1,2,3),(0,2,1,3),3)
        self.assertTrue(e['enumeration_complete'])
        self.assertEqual(set(words),expected_ops)
        _, e=research.symbolic_program_search(2,(0,1,2,3),(0,2,1,3),3,max_programs=1)
        self.assertFalse(e['enumeration_complete'])
        self.assertEqual(e['stop_reason'],'program storage cap')

    def test_main_minimality_checks_every_length_below_seven(self) -> None:
        for length in range(7):
            words,e=research.symbolic_program_search(5,tuple(range(32)),self.target,length,enumerate_all=False)
            self.assertEqual(words,[])
            self.assertEqual(e['status'],'unsat')
            self.assertTrue(e['enumeration_complete'])
        self.assertEqual(research.sample_program(5,research.factorized_executor()),self.target)
        self.assertEqual(len(research.factorized_executor()),7)

    def test_all_retained_words_include_every_persistent_effect_and_honest_bounds(self) -> None:
        for key in ('shortest_witnesses',):
            item=self.evidence[key]
            for word in item['retained_canonical_words']:
                self.assertEqual(research.program_table(tuple(word),self.basis),self.target)
            if not item['search']['enumeration_complete']:
                self.assertIsNone(item['exact_total_shortest_count'])
        flat=self.evidence['flat_comparison']
        flat_target=research.family_table(research.flat_family(),True)
        for word in flat['shortest_witnesses']['retained_canonical_words']:
            self.assertEqual(research.program_table(tuple(word),self.basis),flat_target)
        self.assertEqual(research.sample_program(5,research.flat_executor()),flat_target)
        self.assertEqual(flat['minimum_executor_length'],6)
        self.assertEqual(flat['executable_compression_advantage'],-1)
        for check in flat['minimal_length_checks'][:6]:
            self.assertEqual(check['evidence']['status'],'unsat')

    def test_all_physical_assignments_and_arbitrary_workspace_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            physical=tuple(Path(directory)/name for name in (
                '.arxmentis-state','.arxmentis-state-2','.arxmentis-memory','.arxmentis-policy','.arxmentis-policy-1'))
            for paths in permutations(physical):
                for i,initial in enumerate(research.states(5)):
                    self.assertEqual(research.execute(initial,research.factorized_executor(),paths),research.states(5)[self.target[i]])

    def test_reuse_changes_only_data_and_preserves_selector_files_each_step(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths=tuple(Path(directory)/name for name in ('C0','C1','A','B','W'))
            for c0,c1 in research.states(2):
                research.execute((c0,c1,0,0,1),(),paths)
                saved=tuple(p.read_bytes() for p in paths[:2])
                for a,b in research.states(2)*2:
                    runtime.write_state(a,paths[2]);runtime.write_state(b,paths[3])
                    for op in research.factorized_executor():
                        research.apply_operation(op,paths)
                        self.assertEqual(tuple(p.read_bytes() for p in paths[:2]),saved)
                    self.assertEqual(tuple(runtime.read_state(p) for p in paths),
                                     (c0,c1,*research.states(2)[research.factorized_family()[2*c0+c1][2*a+b]],0))

    def test_selector_pair_persisted_in_one_process_consumed_in_another(self) -> None:
        import subprocess
        import sys
        initialize="from pathlib import Path; import sys; import arxmentis as r; [r.write_state(int(v),Path(p)) for v,p in zip(sys.argv[1:3],sys.argv[3:])]"
        consume="from pathlib import Path; import sys; import composition_experiments as r; p=tuple(Path(x) for x in sys.argv[1:]); [r.apply_operation(op,p) for op in r.factorized_executor()]"
        with tempfile.TemporaryDirectory() as directory:
            paths=tuple(Path(directory)/name for name in ('C0','C1','A','B','W'))
            for c0,c1 in research.states(2):
                subprocess.run([sys.executable,'-B','-c',initialize,str(c0),str(c1),*(str(p) for p in paths[:2])],check=True,capture_output=True)
                for a,b in ((0,1),(1,0)):
                    runtime.write_state(a,paths[2]);runtime.write_state(b,paths[3]);runtime.write_state(1,paths[4])
                    subprocess.run([sys.executable,'-B','-c',consume,*(str(p) for p in paths)],check=True,capture_output=True)
                    self.assertEqual(tuple(runtime.read_state(p) for p in paths),
                                     (c0,c1,*research.states(2)[research.factorized_family()[2*c0+c1][2*a+b]],0))

    def test_all_selector_code_bijections_transport_both_families(self) -> None:
        from collections import Counter
        self.assertEqual(len(set(permutations(range(4)))),24)
        for phi in permutations(range(4)):
            self.assertTrue(research.is_affine(phi))
            for family,executor in ((research.factorized_family(),research.factorized_executor()),
                                    (research.flat_family(),research.flat_executor())):
                target=research.family_table(research.selector_transport(family,phi),True)
                word=research.selector_conjugated_executor(executor,phi)
                self.assertEqual(research.sample_program(5,word),target)
        self.assertEqual(sum(Counter(len(research.selector_conjugated_executor(research.factorized_executor(),p))
                                     for p in permutations(range(4))).values()),24)


class PersistentOrderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        import json
        cls.operations = research.role_complete_basis(5)
        cls.raw = research.sample_basis(5, cls.operations)
        cls.basis, cls.aliases = research.canonical_basis(cls.raw)
        cls.domain = research.order_domain()
        cls.target = research.order_target()
        cls.evidence = json.loads(Path('composition_results.json').read_text(encoding='utf-8'))['persistent_order']

    def test_five_behaviors_information_bound_and_independent_runtime_composition(self) -> None:
        toggle = research.sample_program(2, (('toggle', (0,)),))
        swap = research.sample_program(2, (('xor', (0, 1)), ('xor', (1, 0)), ('xor', (0, 1))))
        family = research.order_family()
        self.assertEqual(family, (tuple(range(4)), tuple(range(4)), swap, swap, toggle, toggle,
                                  research.compose(toggle, swap), research.compose(swap, toggle)))
        self.assertEqual(len(set(family)), 5)
        self.assertLess(2**2, 5)
        self.assertGreaterEqual(2**3, 5)
        for a, b in zip(family[6], family[7], strict=True):
            self.assertNotEqual(a, b)

    def test_total_target_anf_and_all_length_proof_premises_from_all_runtime_calls(self) -> None:
        self.assertEqual(self.target, (0,1,2,3,4,5,6,7,8,10,9,11,12,14,13,15,
                                       18,19,16,17,22,23,20,21,25,27,24,26,30,28,31,29))
        self.assertEqual(len(set(self.target)), 32)
        self.assertFalse(research.is_affine(self.target))
        self.assertEqual(research.algebraic_normal_form(self.target)['degree'], 3)
        for index, (cx, cs, o, a, b) in enumerate(research.states(5)):
            expected = (cx, cs, o, a ^ cs*b ^ cs*a ^ cx ^ cx*cs ^ cx*cs*o,
                                   b ^ cs*b ^ cs*a ^ cx*cs ^ cx*cs*o)
            self.assertEqual(research.states(5)[self.target[index]], expected)
        self.assertEqual((len(self.raw), len(self.basis)), (225, 175))
        for table in self.raw.values():
            if len(set(table)) == 32:
                self.assertTrue(research.is_affine(table))
            if not research.is_affine(table):
                self.assertLess(len(set(table)), 32)

    def test_partial_domain_breaks_global_noninjectivity_argument_and_rank_pruning_is_safe(self) -> None:
        self.assertEqual(self.domain, (0,1,2,3,8,9,10,11,16,17,18,19,24,25,26,27,28,29,30,31))
        self.assertEqual(len({self.target[i] for i in self.domain}), 20)
        nonlinear = [t for t in self.basis.values() if not research.is_affine(t)]
        self.assertEqual(len(nonlinear), 60)
        self.assertEqual(sum(len({t[i] for i in self.domain}) == 20 for t in nonlinear), 6)
        table = research.sample_program(5, (('plastic', (1, 0, 2)),))
        self.assertEqual(len(set(table)), 24)
        self.assertEqual({table[i] for i in self.domain}, set(self.domain))
        viable = [t for t in self.basis.values() if len(set(t)) >= 20]
        self.assertEqual(len(viable), 85)
        for name, op in self.operations.items():
            if op[0] in ('copy', 'evaluate'):
                self.assertEqual(len(set(self.raw[name])), 16)

    def test_reserved_states_are_necessary_by_canonical_domain_invariant(self) -> None:
        allowed = {name:table for name,table in self.basis.items()
                   if {table[i] for i in self.domain} == set(self.domain)}
        self.assertEqual(len(allowed), 12)
        self.assertTrue(all(research.selector_independent_data_linear_part(t,self.domain)
                            for t in allowed.values()))
        self.assertFalse(research.selector_independent_data_linear_part(self.target,self.domain))
        for first in allowed.values():
            for second in allowed.values():
                self.assertTrue(research.selector_independent_data_linear_part(
                    research.compose(first,second),self.domain))

    def test_partial_constraint_search_and_refinement_match_independent_small_enumeration(self) -> None:
        basis = research.sample_basis(2, research.two_bit_basis())
        dom, required = (0,1,2), (0,2,1)
        expected = research.shortest_solutions(basis, lambda t: tuple(t[i] for i in dom) == required, 3)
        expected_ops = {tuple(research.two_bit_basis()[name] for name in word) for word in expected}
        for refined in (False, True):
            words, evidence = research.symbolic_program_search(2, dom, required, 3,
                incremental_rows=refined, injective_prefixes=True, allowed_schemas=('toggle', 'xor', 'plastic'))
            self.assertTrue(evidence['enumeration_complete'])
            self.assertEqual(set(words), expected_ops)
        # Restricting schemas changes the admitted space; do not label it the full basis.
        words, evidence = research.symbolic_program_search(2, dom, required, 3,
                                                           allowed_schemas=('toggle',))
        self.assertEqual(words, [])
        self.assertEqual(evidence['status'], 'unsat')

    def test_independent_complete_bfs_and_retained_length_by_length_search_limits(self) -> None:
        viable = {n:t for n,t in self.basis.items() if len(set(t)) >= 20}
        layers, counts = research.restricted_frontiers(viable, self.domain, 3, 250_000)
        self.assertEqual(counts, [1,31,596,9123])
        required = bytes(self.target[i] for i in self.domain)
        self.assertTrue(all(required not in layer for layer in layers))
        checks = self.evidence['search_records']['hierarchical']['records']
        for length in range(9):
            self.assertEqual(checks[length]['evidence']['status'], 'unsat')
            self.assertTrue(checks[length]['evidence']['enumeration_complete'])
        for check in checks[9:]:
            if check['evidence']['status'] == 'unknown':
                self.assertFalse(check['evidence']['enumeration_complete'])
        self.assertIsNone(self.evidence['executor']['minimum_length'])
        self.assertIsNone(self.evidence['executor']['exact_shortest_count'])

    def test_fixed_word_all_persistent_effects_and_restricted_prefix_rank(self) -> None:
        word = research.order_executor()
        actual = research.sample_program(5, word)
        self.assertEqual(len(word), 11)
        self.assertEqual(tuple(actual[i] for i in self.domain), tuple(self.target[i] for i in self.domain))
        self.assertLess(len(set(actual)), 32)
        trace = research.trace_restricted_program(self.domain, word)
        self.assertTrue(all(row['prefix_restricted_image_size'] == 20 for row in trace))
        self.assertTrue(all(row['restricted_primitive_injective'] for row in trace))
        self.assertTrue(any(row['reserved_selector_visits'] for row in trace))
        for row in trace:
            incoming = row['incoming_reachable_indices']
            assert isinstance(incoming, tuple)
            self.assertTrue(all(len({(i >> bit) & 1 for i in incoming}) == 2 for bit in range(5)))

    def test_all_120_physical_assignments_all_20_canonical_states(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            physical = tuple(Path(directory) / name for name in (
                '.arxmentis-state', '.arxmentis-state-2', '.arxmentis-memory',
                '.arxmentis-policy', '.arxmentis-policy-1'))
            rows = 0
            for paths in permutations(physical):
                for i in self.domain:
                    self.assertEqual(research.execute(research.states(5)[i], research.order_executor(), paths),
                                     research.states(5)[self.target[i]])
                    rows += 1
            self.assertEqual(rows, 2400)

    def test_persisted_selectors_reused_with_data_only_changes_and_exit_restoration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = tuple(Path(directory) / name for name in ('CX', 'CS', 'O', 'A', 'B'))
            for code in (0,2,4,6,7):
                research.execute((*research.states(3)[code], 0, 0), (), paths)
                saved = tuple(p.read_bytes() for p in paths[:3])
                for a,b in research.states(2) * 2:
                    runtime.write_state(a, paths[3]); runtime.write_state(b, paths[4])
                    for operation in research.order_executor():
                        research.apply_operation(operation, paths)
                    self.assertEqual(tuple(p.read_bytes() for p in paths[:3]), saved)
                    self.assertEqual(tuple(runtime.read_state(p) for p in paths),
                                     research.states(5)[self.target[4*code+2*a+b]])

    def test_only_order_bit_change_selects_opposite_order_on_all_data(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = tuple(Path(directory) / str(i) for i in range(5))
            for a,b in research.states(2):
                research.execute((1,1,0,a,b), research.order_executor(), paths)
                first = tuple(runtime.read_state(p) for p in paths)
                runtime.write_state(1, paths[2])
                runtime.write_state(a, paths[3]); runtime.write_state(b, paths[4])
                for op in research.order_executor():
                    research.apply_operation(op, paths)
                second = tuple(runtime.read_state(p) for p in paths)
                self.assertEqual(first, (1,1,0,b,1-a))
                self.assertEqual(second, (1,1,1,1-b,a))
                self.assertNotEqual(first[3:], second[3:])

    def test_selector_written_in_one_process_consumed_and_reused_in_fresh_processes(self) -> None:
        import subprocess
        import sys
        initialize = "from pathlib import Path; import sys; import arxmentis as r; [r.write_state(int(v),Path(p)) for v,p in zip(sys.argv[1:4],sys.argv[4:])]"
        consume = "from pathlib import Path; import sys; import composition_experiments as r; p=tuple(Path(x) for x in sys.argv[1:]); [r.apply_operation(op,p) for op in r.order_executor()]"
        with tempfile.TemporaryDirectory() as directory:
            paths = tuple(Path(directory) / str(i) for i in range(5))
            for code in (0,2,4,6,7):
                subprocess.run([sys.executable,'-B','-c',initialize,*(str(v) for v in research.states(3)[code]),
                                *(str(p) for p in paths[:3])],check=True,capture_output=True)
                saved = tuple(p.read_bytes() for p in paths[:3])
                for a,b in research.states(2) * 2:
                    runtime.write_state(a,paths[3]); runtime.write_state(b,paths[4])
                    subprocess.run([sys.executable,'-B','-c',consume,*(str(p) for p in paths)],
                                   check=True,capture_output=True)
                    self.assertEqual(tuple(p.read_bytes() for p in paths[:3]),saved)
                    self.assertEqual(tuple(runtime.read_state(p) for p in paths),
                                     research.states(5)[self.target[4*code+2*a+b]])

    def test_flat_assignment_transport_real_files_and_reserved_codes_are_map_relative(self) -> None:
        phi = research.order_flat_recoding()
        self.assertEqual(phi,(0,5,2,7,4,1,6,3))
        self.assertTrue(research.is_affine(phi))
        dom = tuple(sorted((phi[i >> 2] << 2) | (i & 3) for i in self.domain))
        self.assertEqual({i >> 2 for i in dom},{0,2,3,4,6})
        target = research.transport_selector_cube(self.target,phi)
        actual = research.sample_program(5,research.order_flat_executor())
        self.assertTrue(all(actual[i] == target[i] for i in dom))
        transported = (('xor',(2,0)),*research.order_executor(),('xor',(2,0)))
        self.assertEqual(research.sample_program(5,transported),
                         research.transport_selector_cube(research.sample_program(5,research.order_executor()),phi))
        trace = research.trace_restricted_program(dom,research.order_flat_executor(),(1,5,7))
        self.assertTrue(any(row['reserved_selector_visits'] for row in trace))
        self.assertEqual(research.algebraic_normal_form(target)['degree'],3)
        self.assertFalse(self.evidence['flat_comparison']['executable_advantage_established'])

    def test_evidence_preserves_history_and_separates_contract_from_total_extension(self) -> None:
        import hashlib
        import json
        artifact = json.loads(Path('composition_results.json').read_text(encoding='utf-8'))
        old = self.evidence['preserved_previous_sections_sha256']
        for key,expected in old.items():
            actual = hashlib.sha256(json.dumps(artifact[key],sort_keys=True).encode()).hexdigest()
            self.assertEqual(actual,expected)
        for name,expected in (
            ('arxmentis.py','94ad41dcc6c6d679b6d4056ecfe1ebeba4108b62dab2d6eef414eb6815ff360f'),
            ('test_arxmentis.py','0146544f9964131cc5101dbc244e616cccc76a835b2c9388a5bc60538cae2a3b')):
            self.assertEqual(hashlib.sha256(Path(name).read_bytes()).hexdigest(),expected)
        self.assertTrue(self.evidence['total_semantics']['all_length_impossible'])
        self.assertEqual(self.evidence['executor']['minimum_dedicated_workspace_bits_for_restricted_contract'],0)
        self.assertEqual(self.evidence['runtime_replay']['remapping_rows'],2400)


if __name__ == "__main__":
    unittest.main()
