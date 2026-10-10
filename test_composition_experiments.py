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


class SlackWorkspaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        import json
        cls.evidence = json.loads(Path('composition_results.json').read_text(encoding='utf-8'))['slack_workspace']
        cls.calls = research.role_complete_basis(5)
        cls.raw = research.sample_basis(5,cls.calls)
        cls.basis,_ = research.canonical_basis(cls.raw)

    def test_finite_bound_exhaustive_small_functions_and_insufficient_cardinality(self) -> None:
        from itertools import combinations
        for size in range(1,5):
            for table in product(range(size),repeat=size):
                for k in range(size+1):
                    for domain in combinations(range(size),k):
                        m = research.state_space_slack(table,domain)
                        if m['injective_on_domain']:
                            self.assertLessEqual(k,len(set(table)))
                            self.assertGreaterEqual(size-k,size-len(set(table)))
        m = research.state_space_slack((0,0,1,1),(0,1))
        self.assertEqual(m['unused_states'],m['necessary_slack_for_injective_restriction'])
        self.assertFalse(m['injective_on_domain'])

    def test_every_runtime_primitive_image_and_slack_requirement(self) -> None:
        expected = {'toggle':(32,0),'xor':(32,0),'memory':(32,0),
                    'copy':(16,16),'evaluate':(16,16),'plastic':(24,8)}
        for name,op in self.calls.items():
            m = research.state_space_slack(self.raw[name],tuple(range(32)))
            self.assertEqual((m['primitive_image_size'],m['necessary_slack_for_injective_restriction']),expected[op[0]])
        self.assertEqual(len(self.evidence['primitive_slack']),175)

    def test_eight_element_group_matches_independent_bit_maps_and_relations(self) -> None:
        group = research.data_behavior_group()
        independent = {tuple(((i&1)<<1 | (i>>1)) ^ offset if swapped else i ^ offset for i in range(4))
                       for swapped in (False,True) for offset in range(4)}
        self.assertEqual(set(group),independent)
        self.assertTrue(all(research.compose(a,b) in group for a in group for b in group))
        x,s = (2,3,0,1),(0,2,1,3)
        self.assertEqual(research.compose(x,x),tuple(range(4)))
        self.assertEqual(research.compose(s,s),tuple(range(4)))
        xs = research.compose(x,s)
        self.assertEqual(research.compose(research.compose(xs,xs),research.compose(xs,xs)),tuple(range(4)))

    def test_group_shortest_existing_support_is_replayed(self) -> None:
        basis = research.two_bit_basis()
        for row in self.evidence['eight_behavior_group']:
            for names in row['shortest_existing_two_bit_words']:
                self.assertEqual(research.sample_program(2,tuple(basis[n] for n in names)),tuple(row['table']))

    def test_all_extensions_preserve_five_assignments_and_have_exact_domains(self) -> None:
        for count,expected in ((6,9),(7,18),(8,6)):
            families = research.behavior_extensions(count)
            self.assertEqual(len(families),expected)
            self.assertEqual(len({tuple(sorted(f.items())) for f in families}),expected)
            for family in families:
                for code in (0,2,4,6,7):
                    self.assertEqual(family[code],research.order_family()[code])
                domain,target = research.extension_contract(family)
                self.assertEqual(len(domain),count*4)
                self.assertEqual(set(domain),set(target))
                self.assertTrue(all(i>>2 == y>>2 for i,y in zip(domain,target,strict=True)))

    def test_affine_elimination_matches_independent_exhaustive_two_bit_maps(self) -> None:
        from typing import cast
        candidates = {tuple(c ^ (a if i&1 else 0) ^ (b if i&2 else 0) for i in range(4))
                      for c,a,b in product(range(4),repeat=3)}
        for required in product(range(4),repeat=4):
            result = research.affine_extension((0,1,2,3),required,2)
            self.assertEqual(result['exists'],required in candidates)
            if result['exists']:
                self.assertEqual(cast(research.Table,result['table']),required)
            else:
                feature = output = 0
                for row in cast(list[int],result['contradiction_rows']):
                    feature ^= row | 4; output ^= required[row]
                self.assertEqual(feature,0)
                self.assertNotEqual(output,0)

    def test_every_extension_has_a_recoverable_affine_contradiction(self) -> None:
        for count in ('6','7','8'):
            for row in self.evidence['extensions'][count]:
                cert = row['affine_extension']
                self.assertFalse(cert['exists'])
                feature = output = 0
                for index in cert['contradiction_rows']:
                    feature ^= row['domain'][index] | 32
                    output ^= row['required'][index]
                self.assertEqual(feature,0)
                self.assertEqual(output,cert['output_xor'])
                self.assertNotEqual(output,0)

    def test_complete_rank24_signed_graph_certificate_has_no_missing_edges(self) -> None:
        certificate = research.rank24_orientation_certificate(self.basis)
        saved = self.evidence['rank24_certificate']
        self.assertEqual((certificate['vertex_count'],certificate['edge_count']),(620,16460))
        self.assertEqual(certificate['signed_edges_sha256'],saved['signed_edges_sha256'])
        self.assertEqual(certificate['orientation'],saved['orientation'])
        self.assertTrue(certificate['connected'])

    def test_selector_transport_closure_exhausts_all_20160_injections(self) -> None:
        calls = research.role_complete_basis(3)
        basis,_ = research.canonical_basis(research.sample_basis(3,calls))
        basis = {n:t for n,t in basis.items() if len(set(t))>=6}
        layers,counts = research.restricted_frontiers(basis,(0,2,3,4,6,7),20,25000)
        self.assertFalse(layers[-1])
        self.assertEqual(sum(counts),20160)
        for item in self.evidence['selector_only_transports']:
            word = tuple((k,tuple(v)) for k,v in item['word'])
            table = research.sample_program(3,word)
            self.assertEqual(tuple(table[i] for i in item['domain']),tuple(item['required']))
            self.assertEqual(len(word),item['minimum_transport_length'])
            self.assertFalse(item['witness_enumeration_complete'])

    def test_six_case_split_and_actual_full_file_backed_witnesses(self) -> None:
        self.assertEqual(self.evidence['six_status_counts'],{'SAT witness found':3,'UNSAT proven':6,'bounded unresolved':0})
        for row in self.evidence['extensions']['6']:
            if row['target_parity']:
                self.assertEqual(row['status'],'UNSAT proven')
            else:
                word = tuple((k,tuple(v)) for k,v in row['word'])
                table = research.sample_program(5,word)
                self.assertEqual(tuple(table[i] for i in row['domain']),tuple(row['required']))
                self.assertEqual(row['proved_lower_bound'],9)
                self.assertIsNone(row['minimum_length'])

    def test_zero_margin_trajectories_fill_each_plastic_image(self) -> None:
        for row in self.evidence['extensions']['6']:
            if row['status']!='SAT witness found':
                continue
            for stage in row['trajectory']:
                self.assertEqual(stage['cardinality'],24)
                self.assertEqual(stage['affine_hull_size'],32)
                self.assertTrue(all(v is None for v in stage['fixed_bit_values']))
                if stage['next_operation'] and stage['next_operation'][0]=='plastic':
                    self.assertTrue(stage['next_is_injective'])
                    self.assertTrue(stage['next_fills_global_image'])

    def test_all_seven_and_eight_cases_have_all_length_rank_affine_proofs(self) -> None:
        for count in ('7','8'):
            rows = self.evidence['extensions'][count]
            self.assertEqual(len(rows),18 if count=='7' else 6)
            for row in rows:
                self.assertEqual(row['status'],'UNSAT proven')
                self.assertGreater(len(row['domain']),24)
                self.assertFalse(row['affine_extension']['exists'])
                if count=='8':
                    self.assertTrue(row['total_properties']['bijective'])
                    self.assertFalse(row['total_properties']['affine'])

    def test_derived_controlled_toggle_is_five_existing_calls_with_clean_W(self) -> None:
        word = research.derived_controlled_toggle(0,1,3)
        self.assertEqual(len(word),5)
        table = research.sample_program(6,word)
        for i,state in enumerate(research.states(6)):
            if state[5]==0:
                expected = (*state[:3],state[3] ^ (state[0]&state[1]),state[4],0)
                self.assertEqual(research.states(6)[table[i]],expected)

    def test_all_six_workspace_completions_are_replayed_for_both_old_W_values(self) -> None:
        for row in self.evidence['workspace']['eight_completions']:
            word = tuple((k,tuple(v)) for k,v in row['word'])
            self.assertEqual(research.sample_program(6,word),tuple(row['required']))
            self.assertEqual(len(row['domain']),64)
            self.assertTrue(all(y&1==0 for y in row['required']))
            self.assertEqual(row['both_old_W_values_trajectory'][0]['cardinality'],64)
            self.assertTrue(all(s['cardinality']==32 for s in row['both_old_W_values_trajectory'][1:]))
        self.assertEqual(self.evidence['workspace']['configured_runtime_carriers_added'],0)

    def test_seven_workspace_cases_are_exact_restrictions_of_verified_completions(self) -> None:
        parents = self.evidence['workspace']['eight_completions']
        for row in self.evidence['workspace']['all_eighteen_seven_extensions']:
            parent = next(p for p in parents if p['family']==row['parent_completion'])
            table = parent['actual_full_table']
            self.assertEqual(tuple(table[i] for i in row['domain']),tuple(row['required']))
            self.assertEqual(len(row['domain']),56)
            self.assertTrue(all(s['cardinality']==28 for s in row['trajectory']))
        self.assertEqual(self.evidence['workspace']['live_rows'],384)

    def test_preserved_fingerprints_and_six_bit_solver_encoding(self) -> None:
        import hashlib
        import json
        artifact = json.loads(Path('composition_results.json').read_text(encoding='utf-8'))
        for key,sha in self.evidence['preserved_previous_sections_sha256'].items():
            self.assertEqual(hashlib.sha256(json.dumps(artifact[key],sort_keys=True).encode()).hexdigest(),sha)
        target = research.sample_program(6,(('toggle',(5,)),))
        words,e = research.symbolic_program_search(6,tuple(range(64)),target,1,enumerate_all=False)
        self.assertEqual(e['status'],'sat')
        self.assertEqual(research.sample_program(6,words[0]),target)


class StoredSequenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        import json
        cls.evidence = json.loads(Path("composition_results.json").read_text(encoding="utf-8"))["stored_sequence"]
        cls.target = research.stored_sequence_target()

    def test_instruction_tables_and_four_words_are_independently_derived(self) -> None:
        x = research.sample_program(2, (("toggle", (0,)),))
        s = research.sample_program(2, (("xor", (0, 1)), ("xor", (1, 0)), ("xor", (0, 1))))
        r = research.compose(x, s)
        self.assertEqual(r, (1, 3, 0, 2))
        words = {2 * p0 + p1: research.compose((x, r)[p0], (x, r)[p1]) for p0, p1 in research.states(2)}
        self.assertEqual(words, {0: (0, 1, 2, 3), 1: (0, 2, 1, 3), 2: (3, 1, 2, 0), 3: (3, 2, 1, 0)})
        self.assertEqual(len(set(words.values())), 4)
        self.assertNotEqual(research.compose(x, r), research.compose(r, x))

    def test_complete_one_slot_target_and_arbitrary_old_workspace(self) -> None:
        target = research.stored_instruction_target()
        actual = research.sample_program(4, research.stored_instruction_executor())
        self.assertEqual(actual, target)
        for i, (instruction, a, b, _) in enumerate(research.states(4)):
            expected = (1 - a, b) if instruction == 0 else (b, 1 - a)
            self.assertEqual(research.states(4)[actual[i]], (instruction, *expected, 0))
        self.assertEqual(len(research.stored_instruction_executor()), 7)
        self.assertFalse(self.evidence["one_slot"]["zero_initialization_required"])

    def test_one_slot_minimum_is_proven_by_complete_clean_workspace_relaxations(self) -> None:
        operations = research.role_complete_basis(4)
        basis, _ = research.canonical_basis(research.sample_basis(4, operations))
        initial = tuple(range(0, 16, 2))
        for recoded in (False, True):
            target = research.stored_instruction_target(recoded)
            words, evidence = research.meet_shortest_programs(basis, initial,
                tuple(target[i] for i in initial), 3, 3, 500_000)
            self.assertEqual(words, [])
            self.assertEqual(evidence["meeting_counts"], [])
            self.assertEqual(research.sample_program(4, research.stored_instruction_executor(recoded)), target)
        self.assertEqual(self.evidence["one_slot"]["minimum_calls"], 7)

    def test_same_slot_schema_transports_and_leaves_other_slot_untouched(self) -> None:
        single = research.stored_instruction_executor()
        for slot in (0, 1):
            roles = (slot, 2, 3, 4)
            transported = tuple((kind, tuple(roles[i] for i in indices)) for kind, indices in single)
            self.assertEqual(transported, research.stored_slot_executor(slot))
            table = research.sample_program(5, transported)
            for i, state in enumerate(research.states(5)):
                instruction = state[slot]
                data = (1 - state[2], state[3]) if instruction == 0 else (state[3], 1 - state[2])
                self.assertEqual(research.states(5)[table[i]], (*state[:2], *data, 0))

    def test_slot_boundary_records_match_repeated_runtime_decoder_consumption(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = tuple(Path(directory) / str(i) for i in range(5))
            for row in self.evidence["slot_boundary_rows"]:
                mid = research.execute(tuple(row["initial"]), research.stored_slot_executor(0), paths)
                self.assertEqual(mid, tuple(row["after_slot0"]))
                for op in research.stored_slot_executor(1):
                    research.apply_operation(op, paths)
                self.assertEqual(tuple(runtime.read_state(p) for p in paths), tuple(row["after_slot1"]))
        self.assertEqual(research.stored_sequence_executor(), research.stored_slot_executor(0) + research.stored_slot_executor(1))
        self.assertEqual(len(research.stored_sequence_executor()), 14)

    def test_global_search_bounds_are_explicit_and_every_retained_full_word_replays(self) -> None:
        evidence = self.evidence
        self.assertEqual(evidence["global_proved_lower_bound"], 7)
        self.assertEqual(evidence["global_minimum_calls"], 7)
        self.assertEqual(evidence["global_calls"], 7)
        checks = evidence["global_search"]["records"]
        self.assertTrue(all(next(e for e in checks if e["length"] == k)["status"] == "unsat" for k in range(6)))
        six = next(e for e in checks if e["length"] == 6)
        self.assertEqual(six["status"], "unknown")
        relaxed = evidence["global_relaxation_search"]
        self.assertEqual(tuple(relaxed["initial"]), tuple(range(0, 32, 2)))
        self.assertEqual(tuple(relaxed["target"]), tuple(self.target[i] for i in relaxed["initial"]))
        lower = next(r["evidence"] for r in relaxed["records"] if r["evidence"]["length"] == 6)
        self.assertEqual(lower["status"], "unsat")
        self.assertTrue(lower["enumeration_complete"] and lower["injective_prefixes"])
        self.assertIsNone(evidence["global_shortest_word_count"])
        for raw in evidence["global_search"]["words"]:
            word = tuple((kind, tuple(roles)) for kind, roles in raw)
            self.assertEqual(research.sample_program(5, word), self.target)
        word = tuple((kind, tuple(roles)) for kind, roles in evidence["global_word"])
        self.assertEqual(research.sample_program(5, word), self.target)

    def test_repeated_instructions_are_two_identical_decoders_with_real_boundaries(self) -> None:
        for program, first_table, final_table in ((0, (2, 3, 0, 1), (0, 1, 2, 3)),
                                                   (3, (1, 3, 0, 2), (3, 2, 1, 0))):
            rows = [r for r in self.evidence["slot_boundary_rows"] if 2 * r["initial"][0] + r["initial"][1] == program]
            self.assertEqual(len(rows), 8)
            for row in rows:
                index = 2 * row["initial"][2] + row["initial"][3]
                self.assertEqual(2 * row["after_slot0"][2] + row["after_slot0"][3], first_table[index])
                self.assertEqual(2 * row["after_slot1"][2] + row["after_slot1"][3], final_table[index])

    def test_local_edits_replace_only_the_selected_instruction(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = tuple(Path(directory) / str(i) for i in range(5))
            for slot in (0, 1):
                runtime.write_state(0, paths[0]); runtime.write_state(1, paths[1])
                unchanged = paths[1 - slot].read_bytes()
                for program in ((0, 1), (1, 1) if slot == 0 else (0, 0)):
                    runtime.write_state(program[slot], paths[slot])
                    for a, b in research.states(2):
                        runtime.write_state(a, paths[2]); runtime.write_state(b, paths[3])
                        for op in research.stored_sequence_executor():
                            research.apply_operation(op, paths)
                        expected = self.target[research.states(5).index((*program, a, b, 0))]
                        self.assertEqual(tuple(runtime.read_state(p) for p in paths), research.states(5)[expected])
                        self.assertEqual(paths[1 - slot].read_bytes(), unchanged)

    def test_persist_once_reuse_with_data_only_rewrites(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = tuple(Path(directory) / str(i) for i in range(5))
            for p0, p1 in research.states(2):
                research.execute((p0, p1, 0, 0, 1), (), paths)
                saved = tuple(p.read_bytes() for p in paths[:2])
                for a, b in research.states(2) * 2:
                    runtime.write_state(a, paths[2]); runtime.write_state(b, paths[3])
                    for op in research.stored_sequence_executor():
                        research.apply_operation(op, paths)
                    self.assertEqual(tuple(p.read_bytes() for p in paths[:2]), saved)
                    self.assertEqual(tuple(runtime.read_state(p) for p in paths), research.states(5)[self.target[8 * (2 * p0 + p1) + 4 * a + 2 * b]])

    def test_word_written_in_one_process_consumed_in_fresh_processes(self) -> None:
        import subprocess
        import sys
        initialize = "from pathlib import Path; import sys,arxmentis as a; a.write_state(int(sys.argv[1]),Path(sys.argv[3])); a.write_state(int(sys.argv[2]),Path(sys.argv[4]))"
        consume = "from pathlib import Path; import sys,composition_experiments as r; p=tuple(Path(x) for x in sys.argv[1:]); [r.apply_operation(op,p) for op in r.stored_sequence_executor()]"
        with tempfile.TemporaryDirectory() as directory:
            paths = tuple(Path(directory) / str(i) for i in range(5))
            for p0, p1 in research.states(2):
                subprocess.run([sys.executable, "-B", "-c", initialize, str(p0), str(p1), str(paths[0]), str(paths[1])], check=True, capture_output=True)
                saved = tuple(p.read_bytes() for p in paths[:2])
                runtime.write_state(1, paths[4])
                for a, b in research.states(2) * 2:
                    runtime.write_state(a, paths[2]); runtime.write_state(b, paths[3])
                    subprocess.run([sys.executable, "-B", "-c", consume, *(str(p) for p in paths)], check=True, capture_output=True)
                    self.assertEqual(tuple(runtime.read_state(p) for p in paths), research.states(5)[self.target[8 * (2 * p0 + p1) + 4 * a + 2 * b]])
                    self.assertEqual(tuple(p.read_bytes() for p in paths[:2]), saved)

    def test_all_120_physical_assignments_and_all_32_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            physical = tuple(Path(directory) / name for name in (".arxmentis-state", ".arxmentis-state-2", ".arxmentis-memory", ".arxmentis-policy", ".arxmentis-policy-1"))
            for paths in permutations(physical):
                for i, initial in enumerate(research.states(5)):
                    self.assertEqual(research.execute(initial, research.stored_sequence_executor(), paths), research.states(5)[self.target[i]])

    def test_instruction_complement_transports_one_and_two_slot_targets(self) -> None:
        one = research.stored_instruction_target()
        self.assertEqual(research.transport_mask(one, 8), research.stored_instruction_target(True))
        self.assertEqual(research.transport_mask(self.target, 24), research.stored_sequence_target(recoded=True))
        self.assertEqual(research.sample_program(5, research.stored_sequence_executor(True)), research.stored_sequence_target(recoded=True))
        raw = self.evidence["recoding"]["global_word"]
        self.assertEqual(research.sample_program(5, tuple((k, tuple(v)) for k, v in raw)), research.stored_sequence_target(recoded=True))

    def test_position_transport_and_content_swap_have_distinct_full_state_effects(self) -> None:
        native = research.stored_sequence_executor()
        sigma = (1, 0, 2, 3, 4)
        transported = tuple((kind, tuple(sigma[i] for i in roles)) for kind, roles in native)
        forward = research.sample_program(5, native)
        reverse = research.sample_program(5, transported)
        for i, state in enumerate(research.states(5)):
            mapped = tuple(state[j] for j in sigma)
            mapped_index = research.states(5).index(mapped)
            output = tuple(research.states(5)[forward[i]][j] for j in sigma)
            self.assertEqual(research.states(5)[reverse[mapped_index]], output)
        # Reversing consumption retains 01; swapping contents makes 10.
        self.assertEqual(research.states(5)[reverse[8]][:2], (0, 1))
        self.assertEqual(research.states(5)[forward[16]][:2], (1, 0))
        self.assertEqual(research.states(5)[reverse[8]][2:], research.states(5)[forward[16]][2:])
        self.assertNotEqual(forward[8], reverse[8])

    def test_flat_control_has_exactly_same_extensional_search_problem(self) -> None:
        flat = self.evidence["flat_control"]
        self.assertEqual(tuple(flat["target"]), self.target)
        self.assertEqual(flat["minimum_calls"], 7)
        self.assertEqual(flat["properties"], self.evidence["properties"])
        self.assertEqual(flat["trajectory"], self.evidence["trajectories"]["global"])
        self.assertTrue(flat["local_edit_data_effects_identical"])
        # Independently expose the commuting membership alternative: S^(P0 xor P1), XY^P0.
        s, xy = (0, 2, 1, 3), (3, 2, 1, 0)
        self.assertEqual(research.compose(s, xy), research.compose(xy, s))
        for p0, p1 in research.states(2):
            f = research.compose(s if p0 ^ p1 else tuple(range(4)), xy if p0 else tuple(range(4)))
            self.assertEqual(tuple((self.target[8 * (2 * p0 + p1) + 2 * d] >> 1) & 3 for d in range(4)), f)

    def test_every_prefix_retains_required_classes_and_next_noninjective_use_is_safe(self) -> None:
        for pair in self.evidence["trajectories"].values():
            clean = pair["canonical_W0"]
            self.assertTrue(all(r["cardinality"] == 16 for r in clean))
            self.assertTrue(all(r["program_values_preserved"] for r in clean))
            self.assertTrue(all(r["selector_codes"] == r["program_codes"] for r in clean))
            for stage in clean:
                if stage["next_globally_noninjective"]:
                    self.assertTrue(stage["next_is_injective"])
            self.assertEqual(clean[-1]["W_fixed_value"], 0)
            self.assertEqual(pair["both_old_W"][0]["cardinality"], 32)
            self.assertEqual(pair["both_old_W"][-1]["cardinality"], 16)

    def test_no_workspace_total_bijections_are_impossible_in_complete_basis(self) -> None:
        for width, row in self.evidence["no_workspace_all_length_proofs"].items():
            target = tuple(row["target"])
            self.assertEqual(len(set(target)), 1 << int(width))
            self.assertFalse(research.is_affine(target))
            basis = research.sample_basis(int(width), research.role_complete_basis(int(width)))
            self.assertTrue(all(research.is_affine(t) for t in basis.values() if len(set(t)) == len(target)))
        self.assertEqual(self.evidence["minimum_dedicated_workspace_bits"], 1)
        self.assertEqual(self.evidence["configured_carriers_added"], 0)

    def test_every_previous_evidence_fingerprint_is_preserved(self) -> None:
        import hashlib
        import json
        artifact = json.loads(Path("composition_results.json").read_text(encoding="utf-8"))
        for key, sha in self.evidence["preserved_previous_sections_sha256"].items():
            self.assertEqual(hashlib.sha256(json.dumps(artifact[key], sort_keys=True).encode()).hexdigest(), sha)
        self.assertEqual(len(self.evidence["preserved_previous_sections_sha256"]), 11)


class SemanticLengthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        import json
        cls.evidence = json.loads(Path("composition_results.json").read_text(encoding="utf-8"))["semantic_length"]
        cls.alphabet = research.semantic_length_alphabet()
        cls.family = research.semantic_length_family(cls.alphabet)
        cls.word = research.semantic_length_executor()
        cls.initial, cls.target, cls.boundary = research.semantic_length_contract(cls.alphabet, True)
        cls.sampled = {op: research.sample_program(6, (op,)) for op in set(cls.word)}

    def test_composition_derived_six_meanings_are_distinct(self) -> None:
        expected = {0: (2, 3, 0, 1), 2: (1, 3, 0, 2), 4: (0, 1, 2, 3),
                    5: (0, 2, 1, 3), 6: (3, 1, 2, 0), 7: (3, 2, 1, 0)}
        self.assertEqual(self.family, expected)
        self.assertEqual(len(set(self.family.values())), 6)
        self.assertEqual(self.evidence["representation"]["minimum_bits"], 3)

    def test_natural_total_target_rank_and_degree(self) -> None:
        target = research.semantic_length_target(self.alphabet)
        self.assertEqual(len(set(target)), 32)
        self.assertFalse(research.is_affine(target))
        anf = research.table_properties(target)["algebraic_normal_form"]
        assert isinstance(anf, dict)
        self.assertEqual(anf["degree"], 3)
        for code in range(8):
            for d in range(4):
                expected = (self.alphabet[(code >> 1) & 1][d] if code < 4 else
                            research.compose(self.alphabet[(code >> 1) & 1], self.alphabet[code & 1])[d])
                self.assertEqual(target[4 * code + d], 4 * code + expected)

    def test_total_obstruction_premises_are_runtime_grounded(self) -> None:
        raw = research.sample_basis(5, research.role_complete_basis(5))
        self.assertEqual(len(raw), 225)
        self.assertTrue(all(research.is_affine(t) for t in raw.values() if len(set(t)) == 32))
        self.assertEqual({len(set(t)) for t in raw.values()}, {16, 24, 32})

    def test_canonical_domain_and_endpoint_are_odd(self) -> None:
        initial, target, boundary = research.semantic_length_contract(self.alphabet)
        self.assertEqual(len(initial), 24)
        self.assertEqual(set(initial), set(target))
        self.assertEqual(set(initial), set(boundary))
        self.assertEqual(research.permutation_parity(target, initial), 1)
        self.assertEqual(research.permutation_parity(boundary, initial), 1)
        self.assertEqual({i >> 2 for i in set(range(32)) - set(initial)}, {1, 3})

    def test_complete_orientation_certificate_recomputed(self) -> None:
        raw = research.sample_basis(5, research.role_complete_basis(5))
        basis, _ = research.canonical_basis(raw)
        certificate = research.rank24_orientation_certificate(basis)
        import json
        self.assertEqual(json.loads(json.dumps(certificate)), self.evidence["five_carrier"]["certificate"])
        self.assertEqual(certificate["vertex_count"], 620)
        self.assertEqual(certificate["edge_count"], 16460)
        self.assertEqual(certificate["candidate_edges_examined"], 52700)

    def test_temporary_workspace_full_contract_and_cut(self) -> None:
        actual = research.sample_program(6, self.word)
        self.assertEqual(tuple(actual[i] for i in self.initial), self.target)
        self.assertIn(7, research.semantic_length_cuts(self.initial, self.boundary, self.word, self.sampled))
        self.assertEqual(len(self.word), 14)

    def test_actual_file_boundary_and_suffix_without_reset(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            paths = tuple(Path(directory) / str(i) for i in range(6))
            for state, expected, middle in zip(self.initial, self.target, self.boundary, strict=True):
                self.assertEqual(research.execute(research.states(6)[state], self.word[:7], paths),
                                 research.states(6)[middle])
                for op in self.word[7:]:
                    research.apply_operation(op, paths)
                self.assertEqual(tuple(runtime.read_state(p) for p in paths), research.states(6)[expected])

    def test_both_repetitions_have_real_checkpoints(self) -> None:
        prefix = research.sample_program(6, self.word[:7])
        final = research.sample_program(6, self.word)
        for code in (4, 7):
            for d in range(4):
                i = 8 * code + 2 * d
                self.assertEqual((prefix[i] >> 1) & 3, self.alphabet[(code >> 1) & 1][d])
                self.assertEqual((final[i] >> 1) & 3, self.family[code][d])
        self.assertEqual(self.family[4], tuple(range(4)))
        self.assertEqual(self.family[7], (3, 2, 1, 0))

    def test_length_only_interventions_and_local_substitution(self) -> None:
        rows = self.evidence["interventions"]
        self.assertEqual(len(rows), 24)
        self.assertEqual(sum(r["changed_coordinate"] == 0 for r in rows), 8)
        for row in rows:
            first, second = row["codes"]
            changed = row["changed_coordinate"]
            self.assertEqual(sum(a != b for a, b in zip(research.states(3)[first], research.states(3)[second])), 1)
            self.assertNotEqual(research.states(3)[first][changed], research.states(3)[second][changed])
            d = row["data"]
            self.assertEqual(2 * row["before"][3] + row["before"][4], self.family[first][d])
            self.assertEqual(2 * row["after"][3] + row["after"][4], self.family[second][d])
            self.assertTrue(row["other_program_bytes_unchanged"])

    def test_persistent_program_reused_across_process_death(self) -> None:
        self.assertEqual(self.evidence["reuse"]["initializer_processes"], 6)
        self.assertEqual(self.evidence["reuse"]["consumer_processes"], 48)
        self.assertTrue(self.evidence["reuse"]["data_only_rewrites"])
        self.assertTrue(self.evidence["reuse"]["program_bytes_preserved"])

    def test_all_physical_remappings_include_slot_boundary(self) -> None:
        self.assertEqual(self.evidence["temporary_workspace"]["physical_remapping_assignments"], 120)
        self.assertEqual(self.evidence["temporary_workspace"]["physical_remapping_rows"], 2880)
        self.assertEqual(self.evidence["temporary_workspace"]["configured_added"], 0)

    def test_recoded_domains_and_program_meanings(self) -> None:
        for name, mask in (("length", 16), ("instructions", 12)):
            initial5, target5, _ = research.semantic_length_contract(self.alphabet, False, name)
            self.assertIn(tuple(sorted(initial5)), research.affine_flat_complements())
            self.assertEqual(research.permutation_parity(target5, initial5), 1)
            initial, target, boundary = research.semantic_length_contract(self.alphabet, True, name)
            self.assertEqual(initial, tuple(i ^ (2 * mask) for i in self.initial))
            self.assertEqual(target, tuple(i ^ (2 * mask) for i in self.target))
            self.assertEqual(boundary, tuple(i ^ (2 * mask) for i in self.boundary))
            word = research.semantic_length_executor(name)
            actual = research.sample_program(6, word)
            self.assertEqual(tuple(actual[i] for i in initial), target)
            sampled = {op: research.sample_program(6, (op,)) for op in set(word)}
            self.assertIn(7, research.semantic_length_cuts(initial, boundary, word, sampled))
            self.assertEqual(len(word), 16)

    def test_every_prefix_preserves_24_required_classes_without_reserved_codes(self) -> None:
        for name, pair in self.evidence["temporary_workspace"]["trajectories"].items():
            for row in pair["canonical_W0"]:
                self.assertEqual(row["cardinality"], 24)
                if name == "native":
                    self.assertEqual(row["reserved_codes_occupied"], [])
                if row["next_operation"] is not None:
                    self.assertTrue(row["next_is_injective"])
            self.assertEqual(pair["both_old_W"][0]["cardinality"], 48)
            self.assertEqual(pair["both_old_W"][-1]["cardinality"], 24)

    def test_reserved_extension_is_not_credited_as_total_length_semantics(self) -> None:
        actual = research.sample_program(6, self.word)
        natural = research.semantic_length_target(self.alphabet)
        self.assertTrue(any(actual[i] >> 1 != natural[i >> 1] for i in range(64)))
        self.assertTrue(all(actual[i] >> 1 == natural[i >> 1] for i in self.initial))

    def test_endpoint_and_boundary_searches_are_separate_and_bounds_honest(self) -> None:
        for name, row in self.evidence["temporary_workspace"]["searches"].items():
            self.assertLessEqual(row["lower_bound"], row["upper_bound"])
            word = tuple((kind, tuple(roles)) for kind, roles in row["word"])
            actual = research.sample_program(6, word)
            self.assertEqual(tuple(actual[i] for i in self.initial), self.target)
            sampled = {op: research.sample_program(6, (op,)) for op in set(word)}
            if name == "boundary":
                self.assertTrue(research.semantic_length_cuts(self.initial, self.boundary, word, sampled))
            for record in row["search"]["checks"]:
                self.assertEqual(record["boundary_required"], name == "boundary")
                if record["status"] == "unknown":
                    self.assertTrue(record["unknown_reason"])
            if row["minimum"] is not None:
                self.assertEqual(row["lower_bound"], row["upper_bound"])

    def test_symbolic_shared_boundary_accepts_real_cut_and_rejects_missing_cut(self) -> None:
        basis = research.sample_basis(2, research.two_bit_basis())
        initial = tuple(range(4))
        target = research.compose(basis["toggle(a)"], basis["toggle(b)"])
        words, record = research.symbolic_program_search(2, initial, target, 2,
            enumerate_all=False, boundary_target=basis["toggle(a)"], timeout_ms=5000)
        self.assertTrue(words)
        self.assertTrue(record["boundary_required"])
        words, record = research.symbolic_program_search(2, initial, target, 1,
            enumerate_all=False, boundary_target=basis["toggle(a)"], timeout_ms=5000)
        self.assertEqual(words, [])
        self.assertEqual(record["status"], "unsat")

    def test_flat_control_has_same_endpoint_and_no_semantic_cost_advantage(self) -> None:
        initial, target, _ = research.semantic_length_contract(self.alphabet)
        self.assertEqual(tuple(self.evidence["flat_control"]["canonical_target"]), target)
        self.assertEqual(len(initial), 24)
        self.assertTrue(self.evidence["flat_control"]["boundary_constraint_additional"])
        self.assertTrue(self.evidence["flat_control"]["no_cost_advantage_claimed"])

    def test_every_previous_evidence_section_is_preserved(self) -> None:
        import hashlib
        import json
        artifact = json.loads(Path("composition_results.json").read_text(encoding="utf-8"))
        fingerprints = self.evidence["preserved_previous_sections_sha256"]
        self.assertEqual(len(fingerprints), 12)
        for key, sha in fingerprints.items():
            self.assertEqual(hashlib.sha256(json.dumps(artifact[key], sort_keys=True).encode()).hexdigest(), sha)


class PersistentCursorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        import json
        cls.evidence = json.loads(Path("composition_results.json").read_text(encoding="utf-8"))["persistent_cursor"]
        cls.alphabet = research.semantic_length_alphabet()
        cls.target = research.cursor_step_target(cls.alphabet)
        cls.word = research.cursor_step_executor()

    def test_alphabet_unchanged_and_complete_target_composed_independently(self) -> None:
        self.assertEqual(self.alphabet, ((2, 3, 0, 1), (1, 3, 0, 2)))
        self.assertEqual(len(self.target), 64)
        for i, state in enumerate(research.states(6)):
            c, p0, p1, a, b, _ = state
            d = self.alphabet[p0 if c == 0 else p1][2 * a + b]
            self.assertEqual(research.states(6)[self.target[i]], (1 - c, p0, p1, d >> 1, d & 1, 0))
        self.assertEqual(tuple(self.evidence["target"]), self.target)

    def test_rank32_discards_exactly_old_workspace(self) -> None:
        self.assertEqual(len(set(self.target)), 32)
        preimages = {output: tuple(i for i, value in enumerate(self.target) if value == output)
                     for output in set(self.target)}
        self.assertTrue(all(len(pair) == 2 and pair[0] ^ pair[1] == 1 for pair in preimages.values()))
        self.assertFalse(research.is_affine(self.target))
        self.assertEqual(research.algebraic_normal_form(self.target)["degree"], 3)
        self.assertEqual(research.algebraic_normal_form(self.target)["degrees"], [1, 1, 1, 3, 3, 0])

    def test_modular20_word_matches_every_physical_input(self) -> None:
        self.assertEqual(len(self.word), 20)
        self.assertEqual(research.sample_program(6, self.word), self.target)
        self.assertEqual(self.evidence["modular_stage_cuts"], [6, 13, 19, 20])

    def test_actual_modular_selection_decode_restore_advance_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = tuple(Path(directory) / str(i) for i in range(6))
            for initial in research.states(6):
                research.execute(initial, (), paths)
                saved = tuple(p.read_bytes() for p in paths[1:3])
                stages = []
                for part in (self.word[:6], self.word[6:13], self.word[13:19], self.word[19:]):
                    for op in part:
                        research.apply_operation(op, paths)
                    stages.append(tuple(runtime.read_state(p) for p in paths))
                c, p0, p1, a, b, _ = initial
                active, inactive = (p0, p1) if c == 0 else (p1, p0)
                d = self.alphabet[active][2 * a + b]
                self.assertEqual(stages[0], (c, active, inactive, a, b, 0))
                self.assertEqual(stages[1], (c, active, inactive, d >> 1, d & 1, 0))
                self.assertEqual(stages[2], (c, p0, p1, d >> 1, d & 1, 0))
                self.assertEqual(stages[3], (1 - c, p0, p1, d >> 1, d & 1, 0))
                self.assertEqual(tuple(p.read_bytes() for p in paths[1:3]), saved)

    def test_inactive_slot_edit_on_real_files_is_irrelevant_to_step_data(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = tuple(Path(directory) / str(i) for i in range(6))
            for initial in research.states(6):
                baseline = research.execute(initial, self.word, paths)
                research.execute(initial, (), paths)
                changed = 2 if initial[0] == 0 else 1
                saved = tuple(p.read_bytes() for p in paths)
                runtime.toggle_state(paths[changed])
                self.assertTrue(all(p.read_bytes() == saved[j] for j, p in enumerate(paths) if j != changed))
                for op in self.word:
                    research.apply_operation(op, paths)
                actual = tuple(runtime.read_state(p) for p in paths)
                self.assertEqual(actual[3:5], baseline[3:5])
                self.assertEqual(actual[0], baseline[0])
                self.assertEqual(actual[changed], 1 - initial[changed])

    def test_cursor_only_intervention_selects_active_meaning(self) -> None:
        rows = [r for r in self.evidence["interventions"] if r["changed_role"] == 0]
        self.assertEqual(len(rows), 64)
        for row in rows:
            c, p0, p1, a, b, _ = row["initial"]
            first = self.alphabet[(p0, p1)[c]][2 * a + b]
            second = self.alphabet[(p0, p1)[1 - c]][2 * a + b]
            self.assertEqual(row["before"][3:5], [first >> 1, first & 1])
            self.assertEqual(row["after"][3:5], [second >> 1, second & 1])
            self.assertEqual(row["before"][0], 1 - c)
            self.assertEqual(row["after"][0], c)
            self.assertTrue(row["other_initial_bytes_preserved"])
        # X and R coincide on some data inputs; intervention need not always change data.
        self.assertTrue(any(r["before"][3:5] != r["after"][3:5] for r in rows))

    def test_active_instruction_substitution_uses_same_alphabet(self) -> None:
        active = [r for r in self.evidence["interventions"] if r["changed_role"] != 0 and not r["inactive_slot"]]
        self.assertEqual(len(active), 64)
        for row in active:
            c, p0, p1, a, b, _ = row["initial"]
            d = self.alphabet[1 - (p0, p1)[c]][2 * a + b]
            self.assertEqual(row["after"][3:5], [d >> 1, d & 1])

    def test_program_preserved_after_each_step_and_cursor_always_advances(self) -> None:
        for row in self.evidence["two_identical_steps"]:
            initial, middle, final = row["input"], row["after_STEP"], row["after_same_STEP_again"]
            self.assertEqual(middle[1:3], initial[1:3])
            self.assertEqual(final[1:3], initial[1:3])
            self.assertEqual(middle[0], 1 - initial[0])
            self.assertEqual(final[0], initial[0])
            self.assertTrue(row["program_bytes_preserved"])
            self.assertFalse(row["cursor_rewritten_between"])

    def test_same_word_twice_has_previous_two_slot_semantics_without_state_rewrites(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = tuple(Path(directory) / str(i) for i in range(6))
            for i in range(32):
                initial = research.states(6)[i]
                mid = research.execute(initial, self.word, paths)
                for op in self.word:
                    research.apply_operation(op, paths)
                final = tuple(runtime.read_state(p) for p in paths)
                _, p0, p1, a, b, _ = initial
                d = research.compose(self.alphabet[p0], self.alphabet[p1])[2 * a + b]
                self.assertEqual(mid[0], 1)
                self.assertEqual(final, (0, p0, p1, d >> 1, d & 1, 0))

    def test_fresh_process_continuation_requires_only_paths_and_step(self) -> None:
        rows = self.evidence["process_continuation"]["rows"]
        self.assertEqual(len(rows), 32)
        self.assertEqual(self.evidence["process_continuation"]["process_A_count"], 32)
        self.assertEqual(self.evidence["process_continuation"]["process_B_count"], 32)
        for row in rows:
            _, p0, p1, a, b, _ = row["input"]
            d0 = self.alphabet[p0][2 * a + b]
            d1 = self.alphabet[p1][d0]
            self.assertEqual(row["after_process_A"], [1, p0, p1, d0 >> 1, d0 & 1, 0])
            self.assertEqual(row["after_process_B"], [0, p0, p1, d1 >> 1, d1 & 1, 0])
            self.assertIn("no cursor or slot", row["continuation_arguments"])
            self.assertTrue(row["program_bytes_preserved"])

    def test_repetitions_have_separate_instruction_results(self) -> None:
        rows = self.evidence["two_identical_steps"]
        for row in rows:
            c, p0, p1, a, b, _ = row["input"]
            if c == 0 and p0 == p1:
                first = self.alphabet[p0][2 * a + b]
                second = self.alphabet[p0][first]
                self.assertEqual(row["after_STEP"][3:5], [first >> 1, first & 1])
                self.assertEqual(row["after_same_STEP_again"][3:5], [second >> 1, second & 1])
        self.assertEqual(research.compose(self.alphabet[0], self.alphabet[0]), (0, 1, 2, 3))
        self.assertEqual(research.compose(self.alphabet[1], self.alphabet[1]), (3, 2, 1, 0))

    def test_mixed_order_depends_on_stored_contents_and_cursor_cycle(self) -> None:
        xr = research.compose(self.alphabet[0], self.alphabet[1])
        rx = research.compose(self.alphabet[1], self.alphabet[0])
        self.assertNotEqual(xr, rx)
        self.assertEqual(xr, (0, 2, 1, 3))
        self.assertEqual(rx, (3, 1, 2, 0))

    def test_starting_cursor1_consumes_slot1_first(self) -> None:
        for row in self.evidence["two_identical_steps"]:
            c, p0, p1, a, b, _ = row["input"]
            if c == 1:
                d = self.alphabet[p1][2 * a + b]
                self.assertEqual(row["after_STEP"], [0, p0, p1, d >> 1, d & 1, 0])
                final = self.alphabet[p0][d]
                self.assertEqual(row["after_same_STEP_again"], [1, p0, p1, final >> 1, final & 1, 0])

    def test_repeated_invocation_is_cursor_cycle_without_done_or_halt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = tuple(Path(directory) / str(i) for i in range(6))
            research.execute((0, 0, 1, 0, 0, 1), (), paths)
            for count in range(1, 7):
                for op in self.word:
                    research.apply_operation(op, paths)
                self.assertEqual(runtime.read_state(paths[0]), count % 2)
        self.assertIn("DONE", self.evidence["unearned"])
        self.assertEqual(self.evidence["configured_carriers_added"], 0)

    def test_every_required_prefix_is_injective_despite_global_rank_loss(self) -> None:
        for pair in self.evidence["trajectories"].values():
            for row in pair["required32"]:
                self.assertEqual(row["cardinality"], 32)
                self.assertEqual(sum(row["cursor_value_distribution"]), 32)
                if row["next_operation"] is not None:
                    self.assertTrue(row["next_is_injective"])
            self.assertEqual(pair["both_old_W"][0]["cardinality"], 64)
            self.assertEqual(pair["both_old_W"][-1]["cardinality"], 32)
            self.assertEqual(pair["required32"][-1]["workspace_values"], [0])
        # Program contents may be exchanged during modular selection but are restored at STEP exit.
        self.assertTrue(self.evidence["trajectories"]["modular"]["required32"][-1]["program_bits_preserved"])

    def test_whole_target_search_bounds_are_honest_and_witness_replays(self) -> None:
        word = tuple((kind, tuple(roles)) for kind, roles in self.evidence["global_word"])
        self.assertEqual(research.sample_program(6, word), self.target)
        self.assertLessEqual(self.evidence["global_lower_bound"], len(word))
        for record in self.evidence["global_search"]["records"]:
            self.assertEqual(record["domain_rows"], 64)
            self.assertFalse(record["boundary_required"])
            if record["status"] == "unknown":
                self.assertTrue(record["unknown_reason"])
        if self.evidence["global_minimum"] is not None:
            self.assertEqual(self.evidence["global_lower_bound"], len(word))
        self.assertEqual(self.evidence["global_compression_found"], len(word) < 20)

    def test_complete_six_role_basis_and_aliases_are_runtime_grounded(self) -> None:
        raw = research.sample_basis(6, research.role_complete_basis(6))
        basis, aliases = research.canonical_basis(raw)
        self.assertEqual(len(raw), 426)
        self.assertEqual(len(basis), 336)
        self.assertEqual({name: tuple(table) for name, table in self.evidence["canonical_basis"].items()}, basis)
        self.assertEqual(self.evidence["basis_aliases"], aliases)

    def test_all_configured_physical_remappings_and_optional_budget_are_explicit(self) -> None:
        mapping = self.evidence["physical_remapping"]
        self.assertEqual(mapping["configured_role_assignments"], 120)
        self.assertEqual(mapping["full64_rows"], 7680)
        if mapping["full_six_assignments"]:
            self.assertEqual(mapping["full_six_assignments"], 720)
            self.assertEqual(mapping["full_six_clean_W_rows"], 23040)
        else:
            self.assertGreater(mapping["optional_estimated_seconds"], mapping["optional_estimated_cost_cap_seconds"])

    def test_instruction_and_cursor_recoding_have_separate_conjugate_targets(self) -> None:
        for name, mask in (("instructions", 24), ("cursor", 32)):
            actual = research.sample_program(6, research.cursor_step_executor(name))
            self.assertEqual(actual, tuple(mask ^ self.target[mask ^ i] for i in range(64)))
        self.assertEqual(len(self.evidence["recodings"]["actual_rows"]), 128)

    def test_cursor_recoding_slot_role_swap_and_content_edit_are_distinct(self) -> None:
        roles = (0, 2, 1, 3, 4, 5)
        transported = tuple((kind, tuple(roles[i] for i in indices)) for kind, indices in self.word)
        table = research.sample_program(6, transported)
        self.assertEqual(table, research.sample_program(6, research.cursor_step_executor("cursor")))
        # Same endpoint under these symmetric transports does not make the maps identical.
        domain = research.states(6)
        cursor_map = tuple(i ^ 32 for i in range(64))
        slot_map = tuple(domain.index(tuple(state[j] for j in roles)) for state in domain)
        self.assertNotEqual(cursor_map, slot_map)
        with tempfile.TemporaryDirectory() as directory:
            paths = tuple(Path(directory) / str(i) for i in range(6))
            original = research.execute((0, 0, 1, 0, 0, 0), self.word, paths)
            contents_edit = research.execute((0, 1, 0, 0, 0, 0), self.word, paths)
            cursor_edit = research.execute((1, 0, 1, 0, 0, 0), self.word, paths)
            remapped = research.execute((0, 1, 0, 0, 0, 0), transported, paths)
            self.assertEqual(original, (1, 0, 1, 1, 0, 0))
            self.assertEqual(contents_edit, (1, 1, 0, 0, 1, 0))
            self.assertEqual(cursor_edit, (0, 0, 1, 0, 1, 0))
            self.assertEqual(remapped, (1, 1, 0, 1, 0, 0))
        self.assertEqual(self.evidence["recodings"]["role_transport_rows"], 64)

    def test_external_branch_control_matches_table_but_keeps_assistance_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = tuple(Path(directory) / str(i) for i in range(6))
            table = tuple(research.states(6).index(research.cursor_external_selection_control(state, paths))
                          for state in research.states(6))
        self.assertEqual(table, self.target)
        self.assertTrue(self.evidence["external_selection_control"]["cursor_read_by_Python"])
        self.assertTrue(self.evidence["external_selection_control"]["slot_path_chosen_by_Python"])
        self.assertFalse(self.evidence["external_selection_control"]["internal_STEP_harness_branch"])

    def test_workspace_is_necessary_in_declared_five_role_basis(self) -> None:
        five = research.cursor_step_target(self.alphabet, False)
        self.assertEqual(len(set(five)), 32)
        self.assertFalse(research.is_affine(five))
        self.assertTrue(self.evidence["five_without_workspace"]["all_length_impossible"])
        self.assertEqual(self.evidence["minimum_extra_binary_capacity"], 1)

    def test_all_thirteen_previous_evidence_sections_remain_unchanged(self) -> None:
        import hashlib
        import json
        artifact = json.loads(Path("composition_results.json").read_text(encoding="utf-8"))
        fingerprints = self.evidence["preserved_previous_sections_sha256"]
        self.assertEqual(len(fingerprints), 13)
        for key, sha in fingerprints.items():
            self.assertEqual(hashlib.sha256(json.dumps(artifact[key], sort_keys=True).encode()).hexdigest(), sha)


class PersistentTerminalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        import json
        cls.artifact = json.loads(Path("composition_results.json").read_text(encoding="utf-8"))
        cls.evidence = cls.artifact["persistent_terminal"]
        cls.alphabet = research.semantic_length_alphabet()
        cls.domain, cls.target = research.terminal_step_contract(cls.alphabet)

    def test_canonical_bit_order_and_three_codes_require_two_bits(self) -> None:
        self.assertEqual(cls_codes := self.evidence["execution_codes"],
                         {"00": "SLOT 0", "01": "SLOT 1", "10": "DONE", "11": "RESERVED"})
        self.assertEqual(len(cls_codes), 4)
        self.assertEqual(self.evidence["representation_minimum_execution_bits"], 2)
        self.assertEqual(self.domain, tuple(range(48)))
        self.assertEqual({value >> 4 for value in self.domain}, {0, 1, 2})
        self.assertEqual(set(range(64)) - set(self.domain), set(range(48, 64)))

    def test_common_alphabet_is_freshly_runtime_grounded(self) -> None:
        self.assertEqual(self.alphabet, ((2, 3, 0, 1), (1, 3, 0, 2)))
        self.assertEqual(tuple(tuple(table) for table in self.evidence["alphabet"]), self.alphabet)

    def test_slot0_executes_p0_and_advances_to_slot1(self) -> None:
        for value in range(16):
            _, _, p0, p1, a, b = research.states(6)[value]
            data = self.alphabet[p0][2 * a + b]
            self.assertEqual(research.states(6)[self.target[value]], (0, 1, p0, p1, data >> 1, data & 1))

    def test_slot1_executes_p1_and_advances_to_done(self) -> None:
        for value in range(16, 32):
            _, _, p0, p1, a, b = research.states(6)[value]
            data = self.alphabet[p1][2 * a + b]
            self.assertEqual(research.states(6)[self.target[value]], (1, 0, p0, p1, data >> 1, data & 1))

    def test_done_requires_exact_identity_on_every_semantic_bit(self) -> None:
        self.assertEqual(self.target[32:], tuple(range(32, 48)))
        self.assertTrue(all((x & 12) == (y & 12) for x, y in zip(self.domain, self.target, strict=True)))

    def test_target_is_48_rows_not_an_invented_reserved_extension(self) -> None:
        self.assertEqual(len(self.target), 48)
        self.assertEqual(tuple(self.evidence["target"]), self.target)
        self.assertEqual(len(self.evidence["required_rows"]), 48)
        self.assertEqual(self.evidence["dedicated_workspace_capacities"], 0)
        self.assertEqual(self.evidence["temporary_semantic_execution_capacities"], 1)
        self.assertEqual(self.evidence["configured_carriers_added"], 0)

    def test_terminal_map_has32_outputs_and_exact_allowed_fibers(self) -> None:
        fibers = {y: [x for x in self.domain if self.target[x] == y] for y in set(self.target)}
        self.assertEqual(len(fibers), 32)
        self.assertEqual(sum(len(v) == 1 for v in fibers.values()), 16)
        self.assertEqual(sum(len(v) == 2 for v in fibers.values()), 16)
        for output, origins in fibers.items():
            if len(origins) == 1:
                self.assertEqual(origins[0] >> 4, 0)
                self.assertEqual(output >> 4, 1)
            else:
                self.assertEqual({x >> 4 for x in origins}, {1, 2})
                self.assertEqual(output >> 4, 2)
                self.assertEqual(origins[1], output)

    def test_collision_audit_allows_exact_goal_merges_and_rejects_wrong_ones(self) -> None:
        self.assertTrue(research.terminal_collision_audit(self.target, self.target)["compatible_with_target"])
        wrong = list(self.domain)
        wrong[1] = wrong[0]  # Distinct SLOT0 data outputs are not allowed to converge.
        self.assertFalse(research.terminal_collision_audit(tuple(wrong), self.target)["compatible_with_target"])
        allowed = list(self.domain)
        pair = next(v for v in self.evidence["target_collision_classes"]["merged_origin_rows"])
        allowed[pair[1]] = allowed[pair[0]]
        self.assertTrue(research.terminal_collision_audit(tuple(allowed), self.target)["compatible_with_target"])
        with self.assertRaises(ValueError):
            research.terminal_collision_audit((0,), ())

    def test_partial_target_has_no_affine_extension_certificate(self) -> None:
        certificate = research.affine_extension(self.domain, self.target, 6)
        self.assertFalse(certificate["exists"])
        inputs = outputs = 0
        from typing import cast
        for row in cast(list[int], certificate["contradiction_rows"]):
            inputs ^= self.domain[row] | 64
            outputs ^= self.target[row]
        self.assertEqual(inputs, 0)
        self.assertNotEqual(outputs, 0)
        self.assertEqual(certificate, self.evidence["affine_extension"])

    def test_primitive_family_rank_pattern_is_resampled_not_assumed(self) -> None:
        for kind, roles, rank, affine, degree in (
            ("toggle", (0,), 64, True, 1), ("xor", (0, 1), 64, True, 1),
            ("memory", (0, 1), 64, True, 1), ("copy", (0, 1, 2), 32, True, 1),
            ("evaluate", (0, 1, 2), 32, True, 1), ("plastic", (0, 1, 2), 48, False, 2)):
            table = research.sample_program(6, ((kind, roles),))
            self.assertEqual(len(set(table)), rank)
            self.assertEqual(research.is_affine(table), affine)
            self.assertEqual(research.algebraic_normal_form(table)["degree"], degree)
            summary = self.evidence["primitive_families"][kind]
            self.assertEqual(summary["image_sizes"], [rank])
            self.assertEqual(summary["affine_values"], [affine])
            self.assertEqual(summary["degrees"], [degree])

    def test_complete_basis_aliases_match_cursor_runtime_evidence(self) -> None:
        self.assertEqual(self.evidence["raw_calls"], 426)
        self.assertEqual(self.evidence["unique_tables"], 336)
        self.assertEqual(self.evidence["canonical_basis"], self.artifact["persistent_cursor"]["canonical_basis"])
        self.assertEqual(self.evidence["basis_aliases"], self.artifact["persistent_cursor"]["basis_aliases"])

    def test_all_one_call_geometry_and_collision_receipts_recompute(self) -> None:
        basis = self.evidence["canonical_basis"]
        self.assertEqual(len(self.evidence["one_call_candidates"]), 336)
        for candidate in self.evidence["one_call_candidates"]:
            table = tuple(basis[candidate["name"]])
            output = tuple(table[x] for x in self.domain)
            self.assertEqual(candidate["collision_audit"], research.terminal_collision_audit(output, self.target))
            trace = candidate["trajectory"]
            self.assertEqual(trace[0]["cardinality"], 48)
            self.assertEqual(trace[1]["ordered_outputs"], list(output))
            self.assertEqual(trace[1]["cardinality"], len(set(output)))
            self.assertEqual(trace[1]["execution_codes_occupied"], sorted({v >> 4 for v in output}))
            self.assertEqual(sum(trace[1]["data_distribution"]), len(set(output)))
            self.assertTrue(trace[1]["inside_prefix_full_image"])

    def test_injective48_plastic_calls_fill_their_complete_image(self) -> None:
        checked = 0
        for candidate in self.evidence["one_call_candidates"]:
            if candidate["plastic"] and candidate["collision_audit"]["cardinality"] == 48:
                self.assertTrue(candidate["fills_complete_primitive_image"])
                table = self.evidence["canonical_basis"][candidate["name"]]
                self.assertEqual({table[x] for x in self.domain}, set(table))
                self.assertTrue(candidate["trajectory"][0]["plastic_48_injective_constraint_applies"])
                checked += 1
        self.assertGreater(checked, 0)

    def test_symbolic_search_accepts_a_noninjective48_row_contract(self) -> None:
        operation = ("copy", (0, 1, 2))
        table = research.sample_program(6, (operation,))
        target = tuple(table[x] for x in self.domain)
        words, record = research.symbolic_program_search(6, self.domain, target, 1,
            enumerate_all=False, timeout_ms=5_000, wall_seconds=6)
        self.assertEqual(record["status"], "sat")
        self.assertTrue(words)
        for word in words:
            actual = research.sample_program(6, word)
            self.assertEqual(tuple(actual[x] for x in self.domain), target)
        with self.assertRaises(ValueError):
            research.symbolic_program_search(6, self.domain, self.target, 0, injective_prefixes=True)

    def test_search_bounds_separate_unsat_unknown_and_demonstrated_upper(self) -> None:
        search = self.evidence["search"]
        lower = 0
        for record in search["records"]:
            self.assertEqual(record["domain_rows"], 48)
            self.assertFalse(record["injective_prefixes"])
            if record["length"] == lower and record["status"] == "unsat":
                lower += 1
            if record["status"] == "unknown":
                self.assertTrue(record["unknown_reason"])
        self.assertEqual(search["proven_lower_bound"], lower)
        witnesses = self.evidence["witnesses"]
        self.assertEqual(self.evidence["terminal_execution_established"], bool(witnesses))
        if not witnesses:
            self.assertIsNone(search["demonstrated_upper_bound"])
            self.assertIsNone(search["proven_minimum"])

    def test_borrowing_semantic_execution_bit_as_workspace_is_rejected(self) -> None:
        control = self.evidence["borrow_execution_bit_as_workspace_control"]
        word = tuple((kind, tuple(roles)) for kind, roles in control["word"])
        table = research.sample_program(6, word)
        output = tuple(table[x] for x in self.domain)
        self.assertEqual(output, tuple(control["actual_outputs"]))
        self.assertEqual(control["matching_rows"], 16)
        self.assertFalse(research.terminal_collision_audit(output, self.target)["compatible_with_target"])

    def test_constructed_witness_replays_every_required_coordinate_and_prefix(self) -> None:
        self.assertTrue(self.evidence["witnesses"])
        self.assertEqual(len(research.terminal_step_executor()), 121)
        for witness in self.evidence["witnesses"]:
            word = tuple((kind, tuple(roles)) for kind, roles in witness["word"])
            table = research.sample_program(6, word)
            self.assertEqual(tuple(table[x] for x in self.domain), self.target)
            for row in witness["trajectory"]:
                self.assertTrue(row["collision_audit"]["compatible_with_target"])
            for row in witness["repeated_STEP"]:
                self.assertEqual(row["steps"][-1], row["steps"][-2])

    def test_support_words_have_independent_role_relative_effects_on_actual_files(self) -> None:
        for record in self.evidence["constructive_support"]:
            word = tuple((kind, tuple(roles)) for kind, roles in record["word"])
            actual = research.sample_program(6, word)
            self.assertEqual(actual, tuple(record["actual_full64_table"]))
            self.assertEqual(tuple(actual[x] for x in self.domain), tuple(record["required"]))
            self.assertEqual({actual[x] for x in self.domain}, set(self.domain))
        self.assertEqual([record["length"] for record in self.evidence["constructive_support"]], [3, 6, 18, 48])

    def test_branch_transports_target_each_code_and_restore_execution_state(self) -> None:
        for code in range(3):
            word = research.terminal_branch_toffoli(code, 2, 3, 4, 5)
            actual = research.sample_program(6, word)
            expected = tuple(x ^ (2 if x >> 4 == code and x & 8 and x & 4 else 0) for x in self.domain)
            self.assertEqual(tuple(actual[x] for x in self.domain), expected)
        with self.assertRaises(ValueError):
            research.terminal_branch_toffoli(3, 2, 3, 4, 5)
        with self.assertRaises(ValueError):
            research.terminal_branch_toffoli(0, 2, 2, 4, 5)

    def test_full_prefix_geometry_preserves48_until_exact_allowed_merge(self) -> None:
        witness = self.evidence["witnesses"][0]
        trace = witness["trajectory"]
        self.assertEqual(len(trace), 122)
        self.assertEqual([row["cardinality"] for row in trace[:117]], [48]*117)
        self.assertEqual([row["cardinality"] for row in trace[117:]], [32]*5)
        self.assertEqual(trace[116]["next_operation"], ["evaluate", [2, 3, 0]])
        self.assertFalse(trace[116]["next_is_injective"])
        self.assertTrue(trace[116]["next_collision_audit"]["compatible_with_target"])
        self.assertTrue(any(row["reserved_execution_code_occupied"] for row in trace))
        for row in trace:
            self.assertEqual(sum(row["data_distribution"]), row["cardinality"])
            self.assertTrue(row["collision_audit"]["compatible_with_target"])
            if row["plastic_48_injective_constraint_applies"]:
                self.assertTrue(row["plastic_complete_image_equality"])
        self.assertTrue(trace[-1]["program_bits_preserved"])
        self.assertEqual(trace[-1]["execution_codes_occupied"], [1, 2])

    def test_repeated_identical_steps_reach_done_and_remain_semantically_inert(self) -> None:
        witness = self.evidence["witnesses"][0]
        self.assertEqual(len(witness["repeated_STEP"]), 48)
        for row in witness["repeated_STEP"]:
            e0, e1, p0, p1, a, b = row["input"]
            code, data = 2*e0+e1, 2*a+b
            for state in row["steps"]:
                if code < 2:
                    data = self.alphabet[(p0,p1)[code]][data]
                code = min(code+1, 2)
                self.assertEqual(state, [code >> 1, code & 1, p0, p1, data >> 1, data & 1])
            self.assertFalse(row["external_E_edits"])
            self.assertTrue(row["program_bytes_preserved"])

    def test_done_preserves_all_six_physical_bytes_despite_running121_calls(self) -> None:
        word = research.terminal_step_executor()
        with tempfile.TemporaryDirectory() as directory:
            paths = tuple(Path(directory)/str(i) for i in range(6))
            for value in range(32,48):
                research.execute(research.states(6)[value], (), paths)
                original = tuple(path.read_bytes() for path in paths)
                for operation in word:
                    research.apply_operation(operation, paths)
                self.assertEqual(tuple(path.read_bytes() for path in paths), original)
        self.assertEqual(self.evidence["witnesses"][0]["low_level_calls_run_at_DONE"], 121)
        self.assertFalse(self.evidence["autonomous_cessation_established"])

    def test_fresh_processes_continue_then_execute_inert_done_without_dispatch(self) -> None:
        witness = self.evidence["witnesses"][0]
        self.assertEqual(len(witness["process_continuation"]),16)
        self.assertEqual(witness["fresh_process_count"],48)
        for row in witness["process_continuation"]:
            _, _, p0, p1, a, b = row["input"]
            first = self.alphabet[p0][2*a+b]
            second = self.alphabet[p1][first]
            self.assertEqual(row["fresh_process_states"][0], [0,1,p0,p1,first >> 1,first & 1])
            self.assertEqual(row["fresh_process_states"][1], [1,0,p0,p1,second >> 1,second & 1])
            self.assertEqual(row["fresh_process_states"][2],row["fresh_process_states"][1])
            self.assertIn("no execution code or slot",row["arguments"])
            self.assertTrue(row["program_bytes_preserved"])
        self.assertFalse(witness["harness_execution_state_dispatch"])

    def test_inactive_slot_interventions_and_done_ignore_instruction_contents(self) -> None:
        word = research.terminal_step_executor()
        with tempfile.TemporaryDirectory() as directory:
            paths = tuple(Path(directory)/str(i) for i in range(6))
            for value in self.domain:
                initial = research.states(6)[value]
                baseline = research.execute(initial,word,paths)
                code = value >> 4
                changed = 3 if code == 0 else 2
                edited = list(initial)
                edited[changed] ^= 1
                actual = research.execute(tuple(edited),word,paths)
                self.assertEqual(actual[:2],baseline[:2])
                self.assertEqual(actual[4:],baseline[4:])
                self.assertEqual(actual[changed],edited[changed])

    def test_construction_is_an_upper_bound_separate_from_global_solver(self) -> None:
        search = self.evidence["search"]
        self.assertEqual(search["demonstrated_upper_bound"],121)
        self.assertEqual(search["proven_lower_bound"],6)
        self.assertIsNone(search["proven_minimum"])
        self.assertEqual(search["words"],[])
        self.assertEqual(self.evidence["witnesses"][0]["source"],"derived construction")
        self.assertFalse(self.evidence["length_combined"])
        self.assertFalse(self.evidence["runtime_modified"])

    def test_previous_fourteen_evidence_sections_are_preserved(self) -> None:
        import hashlib
        fingerprints = self.evidence["preserved_previous_sections_sha256"]
        self.assertEqual(len(fingerprints), 14)
        import json
        for key, sha in fingerprints.items():
            self.assertEqual(hashlib.sha256(json.dumps(self.artifact[key], sort_keys=True).encode()).hexdigest(), sha)


if __name__ == "__main__":
    unittest.main()
