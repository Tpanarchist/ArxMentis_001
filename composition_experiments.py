"""External finite experiments over the unchanged file-backed runtime.

Tables are sampled from runtime calls. Programs list operations in execution
order. This research harness adds no runtime controller or persistent macro.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from collections.abc import Callable, Sequence
from itertools import combinations, permutations, product
from pathlib import Path
from typing import cast

import arxmentis as runtime

type State = tuple[int, ...]
type Table = tuple[int, ...]
type Operation = tuple[str, tuple[int, ...]]
type Program = tuple[str, ...]


def states(width: int) -> tuple[State, ...]:
    return tuple(product((0, 1), repeat=width))


def apply_operation(operation: Operation, paths: Sequence[Path]) -> None:
    kind, roles = operation
    p = tuple(paths[i] for i in roles)
    if kind == "toggle":
        runtime.toggle_state(p[0])
    elif kind == "xor":
        runtime.dependent_transition(p[0], p[1])
    elif kind == "memory":
        runtime.memory_dependent_transition(p[0], p[1])
    elif kind == "copy":
        runtime.copy_transition(p[0], p[1], p[2])
    elif kind == "plastic":
        runtime.plastic_transition(p[0], p[1], p[2])
    elif kind == "evaluate":
        runtime.evaluate_criterion(p[0], p[1], p[2])
    elif kind == "predict":
        runtime.commit_alternating_prediction(p[0], p[1])
    elif kind == "adapt":
        runtime.adaptive_transition(p[0], p[1], p[2], p[3])
    elif kind == "context":
        runtime.contextual_adaptive_transition(p[0], p[1], p[2], p[3], p[4])
    else:
        raise ValueError(f"Unknown operation {kind}")


def execute(initial: State, operations: Sequence[Operation], paths: Sequence[Path]) -> State:
    if len(initial) != len(paths) or len(set(paths)) != len(paths):
        raise ValueError("Declare one distinct physical path per state coordinate")
    for value, path in zip(initial, paths, strict=True):
        runtime.write_state(value, path)
    for operation in operations:
        apply_operation(operation, paths)
    return tuple(runtime.read_state(path) for path in paths)


def sample_program(width: int, operations: Sequence[Operation]) -> Table:
    domain = states(width)
    indices = {state: i for i, state in enumerate(domain)}
    with tempfile.TemporaryDirectory() as directory:
        paths = tuple(Path(directory) / f"cell-{i}" for i in range(width))
        return tuple(indices[execute(state, operations, paths)] for state in domain)


def sample_basis(width: int, basis: dict[str, Operation]) -> dict[str, Table]:
    return {name: sample_program(width, (op,)) for name, op in basis.items()}


def compose(first: Table, second: Table) -> Table:
    """Run first then second; include every persistent coordinate."""
    if len(first) != len(second):
        raise ValueError("Composition requires the same declared domain")
    return tuple(second[output] for output in first)


def program_table(program: Program, basis: dict[str, Table]) -> Table:
    if not basis:
        raise ValueError("A nonempty basis is required")
    table = tuple(range(len(next(iter(basis.values())))))
    for name in program:
        table = compose(table, basis[name])
    return table


def closure(basis: dict[str, Table], max_length: int, max_tables: int = 50_000
            ) -> tuple[dict[Table, Program], list[int], bool]:
    """BFS of full-table equivalence classes, with shortest support.

    Identity counts at depth zero. Only an empty complete next frontier proves
    saturation. A length bound is not an absence proof. A cap raises rather
    than returning counts from an incomplete frontier.
    """
    if not basis or max_length < 0 or max_tables < 1:
        raise ValueError("Invalid basis or resource bounds")
    identity = tuple(range(len(next(iter(basis.values())))))
    witnesses: dict[Table, Program] = {identity: ()}
    frontier: dict[Table, Program] = {identity: ()}
    new_counts = [1]
    for _ in range(max_length):
        following: dict[Table, Program] = {}
        for table, program in frontier.items():
            for name, op in basis.items():
                result = compose(table, op)
                if result not in witnesses:
                    if len(witnesses) >= max_tables:
                        raise RuntimeError("Transformation resource cap exceeded")
                    witness = program + (name,)
                    witnesses[result] = witness
                    following[result] = witness
        new_counts.append(len(following))
        if not following:
            return witnesses, new_counts, True
        frontier = following
    return witnesses, new_counts, False


def transport(table: Table) -> Table:
    """Simultaneous complement of every coordinate: phi F phi^-1."""
    mask = len(table) - 1
    if len(table) < 2 or len(table) & mask:
        raise ValueError("Domain must be a nonempty binary cube")
    return tuple(mask ^ table[mask ^ i] for i in range(len(table)))


def shortest_solutions(basis: dict[str, Table], criterion: Callable[[Table], bool],
                       max_length: int) -> list[Program]:
    """Enumerate ALL words at each depth, retaining all shortest solutions.

    Alternative programs with equal tables are preserved here. The criterion
    receives behavior, never the desired sequence. Use only tiny bounded bases.
    """
    if not basis or max_length < 0:
        raise ValueError("Invalid search basis or bound")
    for length in range(max_length + 1):
        solutions = [program for program in product(tuple(basis), repeat=length)
                     if criterion(program_table(program, basis))]
        if solutions:
            return solutions
    return []


def is_affine(table: Table) -> bool:
    """Check the whole GF(2) map against its zero and unit-vector images."""
    offset = table[0]
    width = (len(table) - 1).bit_length()
    for x, actual in enumerate(table):
        expected = offset
        for bit in range(width):
            if x & (1 << bit):
                expected ^= table[1 << bit] ^ offset
        if expected != actual:
            return False
    return True


def two_bit_basis() -> dict[str, Operation]:
    return {"toggle(a)": ("toggle", (0,)), "toggle(b)": ("toggle", (1,)),
            "xor(a,b)": ("xor", (0, 1)), "xor(b,a)": ("xor", (1, 0))}


def three_bit_basis() -> dict[str, Operation]:
    return {
        "toggle(d)": ("toggle", (0,)), "toggle(t)": ("toggle", (1,)),
        "toggle(s)": ("toggle", (2,)), "xor(d,t)": ("xor", (0, 1)),
        "memory(t,s)": ("memory", (1, 2)), "copy(d,t,s)": ("copy", (0, 1, 2)),
        "plastic(d,t,s)": ("plastic", (0, 1, 2)),
        "evaluate(d,t,s)": ("evaluate", (0, 1, 2)),
    }


def role_remapping_check(operations: Sequence[Operation], expected: Table) -> int:
    checked = 0
    domain = states(3)
    with tempfile.TemporaryDirectory() as directory:
        physical = tuple(Path(directory) / name for name in ("A", "B", "C"))
        for paths in permutations(physical):
            for i, state in enumerate(domain):
                actual = execute(state, operations, paths)
                if actual != domain[expected[i]]:
                    raise AssertionError((paths, state, actual, domain[expected[i]]))
                checked += 1
    return checked


def contextual_lower_table() -> Table:
    """Lower operations plus explicit external data-dependent path choice."""
    domain = states(5)
    indices = {state: i for i, state in enumerate(domain)}
    outputs: list[int] = []
    with tempfile.TemporaryDirectory() as directory:
        paths = tuple(Path(directory) / f"cell-{i}" for i in range(5))
        for state in domain:
            active = 3 if state[0] == 0 else 4  # Harness branch, not a primitive.
            operations: tuple[Operation, ...] = (
                ("plastic", (0, 1, active)), ("evaluate", (0, 1, 2)),
                ("xor", (0, 2)), ("xor", (2, active)),
            )
            outputs.append(indices[execute(state, operations, paths)])
    return tuple(outputs)


def table_rows(table: Table, width: int) -> list[dict[str, State]]:
    domain = states(width)
    return [{"input": state, "output": domain[table[i]]} for i, state in enumerate(domain)]



def role_complete_basis(width: int) -> dict[str, Operation]:
    """Existing six low-level schemas, every distinct-carrier assignment.

    Labels include duplicates (memory/XOR and symmetric evaluator arguments)
    so the property audit checks every admitted call, before table pruning.
    Neither initialization writes nor high-level controls are free primitives.
    """
    basis: dict[str, Operation] = {}
    for i in range(width):
        basis[f"toggle({i})"] = ("toggle", (i,))
    for roles in permutations(range(width), 2):
        for kind in ("xor", "memory"):
            basis[f"{kind}{roles}"] = (kind, roles)
    for roles in permutations(range(width), 3):
        for kind in ("copy", "plastic", "evaluate"):
            basis[f"{kind}{roles}"] = (kind, roles)
    return basis


def canonical_basis(basis: dict[str, Table]) -> tuple[dict[str, Table], dict[str, list[str]]]:
    names: dict[Table, str] = {}
    tables: dict[str, Table] = {}
    aliases: dict[str, list[str]] = {}
    for name, table in basis.items():
        if table in names:
            aliases[names[table]].append(name)
        else:
            names[table] = name
            tables[name] = table
            aliases[name] = [name]
    return tables, aliases


def controlled_swap_table() -> Table:
    """Desired total three-bit behavior, specified without an executor word."""
    domain = states(3)
    return tuple(domain.index((c, a ^ (c & (a ^ b)), b ^ (c & (a ^ b))))
                 for c, a, b in domain)


def algebraic_normal_form(table: Table) -> dict[str, object]:
    """Recover ANF from every truth-table row using the binary Mobius transform.

    Mask bit zero is the LAST coordinate, matching the existing table indices.
    Terms are recorded as input-coordinate lists, including [] for a constant.
    """
    width = (len(table) - 1).bit_length()
    coordinates: list[list[list[int]]] = []
    degrees: list[int] = []
    for output_coordinate in range(width):
        coefficients = [(value >> (width - 1 - output_coordinate)) & 1 for value in table]
        for bit in range(width):
            for mask in range(len(table)):
                if mask & (1 << bit):
                    coefficients[mask] ^= coefficients[mask ^ (1 << bit)]
        terms = [[i for i in range(width) if mask & (1 << (width - 1 - i))]
                 for mask, coefficient in enumerate(coefficients) if coefficient]
        coordinates.append(terms)
        degrees.append(max((len(term) for term in terms), default=0))
    return {"terms_by_output_coordinate": coordinates, "degrees": degrees,
            "degree": max(degrees, default=0)}


def restricted_frontiers(basis: dict[str, Table], initial: Table, max_length: int,
                         max_tables: int = 500_000
                         ) -> tuple[list[dict[bytes, tuple[bytes, str] | None]], list[int]]:
    """BFS over full output tuples of a DECLARED input subset.

    These are eight-row maps into the sixteen-state cube, not single-instance
    success. Rank loss is safely pruned because distinct required outputs can
    never be recovered by a deterministic suffix. bytes.translate is the same
    composition as compose(), executed in C for the bounded four-bit search.
    Parent pointers preserve support, and no branch depends on a runtime bit.
    """
    if not basis or max_length < 0 or max_tables < 1:
        raise ValueError("Invalid restricted search bounds")
    if len(set(initial)) != len(initial):
        raise ValueError("The declared input subset must have distinct states")
    transitions = {name: bytes(table) + bytes(256 - len(table)) for name, table in basis.items()}
    start = bytes(initial)
    seen = {start}
    layers: list[dict[bytes, tuple[bytes, str] | None]] = [{start: None}]
    counts = [1]
    for _ in range(max_length):
        following: dict[bytes, tuple[bytes, str] | None] = {}
        for table in layers[-1]:
            for name, translation in transitions.items():
                result = table.translate(translation)
                if len(set(result)) != len(initial) or result in seen:
                    continue
                if len(seen) >= max_tables:
                    raise RuntimeError("Restricted transformation resource cap exceeded")
                seen.add(result)
                following[result] = (table, name)
        layers.append(following)
        counts.append(len(following))
        if not following:
            break
    return layers, counts



def backward_frontiers(basis: dict[str, Table], target: Table, max_length: int,
                       max_tables: int = 500_000
                       ) -> tuple[list[dict[bytes, tuple[bytes, str] | None]], list[int]]:
    """Complete bounded preimage search for an injective restricted goal.

    Every possible predecessor tuple is considered, even for full-cube
    noninjective primitives. It is incorrect to substitute one inverse for
    such a primitive. Distinct output rows have disjoint preimage sets.
    Layers deduplicate equal predecessor behaviors, retaining one support.
    """
    if not basis or max_length < 0 or max_tables < 1 or len(set(target)) != len(target):
        raise ValueError("Invalid backward search domain or bounds")
    size = len(next(iter(basis.values())))
    inverses = {
        name: tuple(tuple(i for i, output in enumerate(table) if output == y)
                    for y in range(size)) for name, table in basis.items()
    }
    start = bytes(target)
    layers: list[dict[bytes, tuple[bytes, str] | None]] = [{start: None}]
    seen = {start}
    counts = [1]
    for _ in range(max_length):
        following: dict[bytes, tuple[bytes, str] | None] = {}
        for required in layers[-1]:
            for name, inverse in inverses.items():
                choices = tuple(inverse[y] for y in required)
                if any(not options for options in choices):
                    continue
                for predecessor in product(*choices):
                    candidate = bytes(predecessor)
                    if candidate in seen:
                        continue
                    if len(seen) >= max_tables:
                        raise RuntimeError("Backward transformation resource cap exceeded")
                    seen.add(candidate)
                    following[candidate] = (required, name)
        layers.append(following)
        counts.append(len(following))
        if not following:
            break
    return layers, counts


def frontier_witness(layers: list[dict[bytes, tuple[bytes, str] | None]],
                     table: bytes, depth: int) -> Program:
    reversed_word: list[str] = []
    while depth:
        parent = layers[depth][table]
        if parent is None:
            raise AssertionError("Missing nonidentity support")
        table, name = parent
        reversed_word.append(name)
        depth -= 1
    return tuple(reversed(reversed_word))



def meet_shortest_programs(basis: dict[str, Table], initial: Table, target: Table,
                          max_prefix: int = 3, max_suffix: int = 3,
                          max_tables: int = 500_000
                          ) -> tuple[list[Program], dict[str, object]]:
    """Bidirectional BFS on restricted maps, preserving ALL shortest support.

    Complete forward and preimage layers certify every split within the bound.
    At the shortest depth, every prefix/suffix has minimal distance to its
    meeting tuple; otherwise replacing it would produce a shorter solution.
    Re-enumerating edges between these layers recovers support discarded by
    behavior deduplication, including equal restricted maps from distinct full
    primitives. Canonical primitive-table aliases are handled by the caller.
    """
    forward, forward_counts = restricted_frontiers(basis, initial, max_prefix, max_tables)
    backward, backward_counts = backward_frontiers(basis, target, max_suffix, max_tables)
    meetings = [(i, j, forward[i].keys() & backward[j].keys())
                for i in range(len(forward)) for j in range(len(backward))]
    successful = [(i, j, common) for i, j, common in meetings if common]
    evidence: dict[str, object] = {
        "max_prefix_length": max_prefix, "max_suffix_length": max_suffix,
        "maximum_complete_program_length": max_prefix + max_suffix,
        "per_direction_table_cap": max_tables,
        "forward_new_at_length": forward_counts,
        "backward_new_at_length": backward_counts,
        "meeting_counts": [{"prefix_length": i, "suffix_length": j, "maps": len(common)}
                           for i, j, common in successful],
        "pruning": "equal full-output tuples on all admissible inputs; irreversible rank loss excluded",
    }
    if not successful:
        evidence["minimum_length"] = None
        return [], evidence
    minimum = min(i + j for i, j, _ in successful)
    # One split suffices to enumerate every word at the minimum length.
    prefix_depth, suffix_depth, common = next(
        (i, j, common) for i, j, common in successful if i + j == minimum
    )
    translations = {name: bytes(table) + bytes(256 - len(table)) for name, table in basis.items()}
    prefix_words: dict[bytes, list[Program]] = {meeting: [] for meeting in common}

    def prefixes(current: bytes, depth: int, word: Program) -> None:
        if depth == prefix_depth:
            if current in common:
                prefix_words[current].append(word)
            return
        for name, translation in translations.items():
            following = current.translate(translation)
            if following in forward[depth + 1]:
                prefixes(following, depth + 1, word + (name,))

    def suffixes(current: bytes, remaining: int) -> list[Program]:
        if remaining == 0:
            return [()] if current == bytes(target) else []
        words: list[Program] = []
        for name, translation in translations.items():
            following = current.translate(translation)
            if following in backward[remaining - 1]:
                words.extend((name,) + tail for tail in suffixes(following, remaining - 1))
        return words

    prefixes(bytes(initial), 0, ())
    programs = sorted({prefix + suffix for meeting in common
                       for prefix in prefix_words[meeting]
                       for suffix in suffixes(meeting, suffix_depth)})
    for word in programs:
        table = bytes(initial)
        for name in word:
            table = table.translate(translations[name])
        if table != bytes(target):
            raise AssertionError("Bidirectional support replay differs from the goal")
    evidence["minimum_length"] = minimum
    evidence["all_shortest_canonical_program_count"] = len(programs)
    evidence["complete_shortest_layer"] = True
    return programs, evidence


def selected_swap_workspace_program() -> tuple[Operation, ...]:
    """A fixed shortest witness over C,A,B,W; no harness branch on data.

    This constant word is in the complete six-step search result. It uses one
    existing workspace carrier, erases its prior value, and clears it at exit.
    It is experimental support, not a new runtime primitive or interpreter.
    """
    return (("copy", (1, 2, 3)), ("plastic", (3, 1, 0)),
            ("plastic", (1, 3, 0)), ("plastic", (2, 1, 0)),
            ("copy", (3, 1, 2)), ("xor", (1, 3)))


def recoded_swap_workspace_program() -> tuple[Operation, ...]:
    """Six-step transported witness for selector-only complement encoding."""
    return (("copy", (1, 2, 3)), ("plastic", (3, 1, 0)),
            ("plastic", (1, 3, 0)), ("plastic", (2, 1, 0)),
            ("copy", (1, 3, 2)), ("xor", (1, 3)))


def transport_mask(table: Table, mask: int) -> Table:
    """Complement just the declared coordinates, on the full binary cube."""
    if mask < 0 or mask >= len(table) or len(table) & (len(table) - 1):
        raise ValueError("Invalid binary-coordinate transport")
    return tuple(mask ^ table[mask ^ i] for i in range(len(table)))


def table_properties(table: Table) -> dict[str, object]:
    collision = next(((i, j, table[i]) for i in range(len(table))
                      for j in range(i + 1, len(table)) if table[i] == table[j]), None)
    return {"table": table, "image_size": len(set(table)),
            "bijective": collision is None, "affine": is_affine(table),
            "algebraic_normal_form": algebraic_normal_form(table),
            "collision_input_indices_and_output": collision}


def mechanism_reification_experiment(retained: dict[Table, Program]) -> dict[str, object]:
    target = controlled_swap_table()
    ops3 = role_complete_basis(3)
    raw3 = sample_basis(3, ops3)
    b3, aliases3 = canonical_basis(raw3)
    bijective3 = {name: t for name, t in b3.items() if len(set(t)) == 8}
    inverse_premises3 = all(is_affine(t) for t in bijective3.values())
    nonaffine_loss3 = all(len(set(t)) < 8 for t in raw3.values() if not is_affine(t))
    group3, counts3, saturated3 = closure(bijective3, 12, 5_000)
    assert len(set(target)) == 8 and not is_affine(target)
    assert inverse_premises3 and nonaffine_loss3 and saturated3 and target not in group3

    ops4 = role_complete_basis(4)
    raw4 = sample_basis(4, ops4)
    b4, aliases4 = canonical_basis(raw4)
    initial = tuple(range(0, 16, 2))  # All and only W=0, ordered by C,A,B.
    required = tuple(2 * x for x in target)
    words, search = meet_shortest_programs(b4, initial, required)
    assert words
    selected_ops = selected_swap_workspace_program()
    selected_full = sample_program(4, selected_ops)
    normalization = tuple(2 * target[i // 2] for i in range(16))
    assert selected_full == normalization
    classes: dict[Table, list[int]] = {}
    for index, word in enumerate(words):
        table = program_table(word, b4)
        assert tuple(table[i] for i in initial) == required
        classes.setdefault(table, []).append(index)
    # Prove each distinct full-cube class against real files, not just one word.
    for table, members in classes.items():
        representative = tuple(ops4[name] for name in words[members[0]])
        assert sample_program(4, representative) == table
    chosen_table = sample_program(4, selected_ops)
    assert any(program_table(word, b4) == chosen_table for word in words)
    selected_primitive_tables = {op: sample_program(4, (op,)) for op in selected_ops}
    canonical_selected = tuple(next(name for name, t in b4.items()
                                    if t == selected_primitive_tables[op]) for op in selected_ops)
    assert canonical_selected in words
    raw_words = sorted({expanded for word in words
                        for expanded in product(*(aliases4[name] for name in word))})

    recoded_target = transport_mask(normalization, 8)
    recoded_required = tuple(recoded_target[i] for i in initial)
    recoded_words, recoded_search = meet_shortest_programs(b4, initial, recoded_required)
    recoded_ops = recoded_swap_workspace_program()
    recoded_full = sample_program(4, recoded_ops)
    assert recoded_full == recoded_target and recoded_full != selected_full
    recoded_primitive_tables = {op: sample_program(4, (op,)) for op in recoded_ops}
    canonical_recoded = tuple(next(name for name, t in b4.items()
                                   if t == recoded_primitive_tables[op]) for op in recoded_ops)
    assert canonical_recoded in recoded_words
    conjugated = (("toggle", (0,)),) + selected_ops + (("toggle", (0,)),)
    assert sample_program(4, conjugated) == recoded_full
    recoded_classes: dict[Table, list[int]] = {}
    for index, word in enumerate(recoded_words):
        recoded_classes.setdefault(program_table(word, b4), []).append(index)
    for table, members in recoded_classes.items():
        representative = tuple(ops4[name] for name in recoded_words[members[0]])
        assert sample_program(4, representative) == table
    recoded_raw_words = sorted({expanded for word in recoded_words
                                for expanded in product(*(aliases4[name] for name in word))})
    role_rows = 0
    reuse_rows = 0
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        physical = tuple(root / name for name in (
            ".arxmentis-state", ".arxmentis-state-2", ".arxmentis-memory", ".arxmentis-policy"))
        guard = root / ".arxmentis-policy-1"
        for paths in permutations(physical):
            for c, a, b, guard_value in product((0, 1), repeat=4):
                for operations, full in ((selected_ops, selected_full), (recoded_ops, recoded_full)):
                    actual = execute((c, a, b, 0, guard_value), operations, (*paths, guard))
                    expected = states(4)[full[(c << 3) | (a << 2) | (b << 1)]]
                    assert actual == (*expected, guard_value)
                    role_rows += 1
        paths = (*physical, guard)
        for c in (0, 1):
            execute((c, 0, 0, 0, 1), (), paths)
            persisted_selector = paths[0].read_bytes()
            for a, b in ((0, 1), (1, 0), (0, 0), (1, 1)) * 2:
                runtime.write_state(a, paths[1])
                runtime.write_state(b, paths[2])
                for operation in selected_ops:
                    apply_operation(operation, paths)
                    assert paths[0].read_bytes() == persisted_selector
                expected = states(4)[normalization[(c << 3) | (a << 2) | (b << 1)]]
                assert tuple(runtime.read_state(path) for path in paths) == (*expected, 1)
                reuse_rows += 1
    prefix = tuple(range(16))
    prefix_rows = []
    for operation in selected_ops:
        prefix = compose(prefix, sample_program(4, (operation,)))
        restricted = tuple(prefix[i] for i in initial)
        prefix_rows.append({"operation": operation, "full_image_size": len(set(prefix)),
                            "admissible_image_size": len(set(restricted)), "admissible_table": restricted,
                            "selector_preserved": all((prefix[i] >> 3) == (i >> 3) for i in range(16))})
    return {
        "roles": ["C", "A", "B", "W"],
        "selector_semantics": "0=IDENTITY, 1=SWAP; meanings supplied by experiment",
        "target_three_bit": table_properties(target),
        "target_rows": table_rows(target, 3),
        "target_in_prior_538_inventory": target in retained,
        "three_bit_basis": {"raw_operation_count": len(raw3), "canonical_operation_count": len(b3),
                            "operations": ops3, "aliases": aliases3,
                            "properties": {name: table_properties(t) for name, t in raw3.items()}},
        "three_bit_bijective_search": {"basis": list(bijective3), "max_length": 12,
                                       "table_cap": 5_000, "new_at_length": counts3,
                                       "unique_total": len(group3), "saturated": saturated3,
                                       "target_present": target in group3},
        "impossibility": {
            "total_three_bit_proven": inverse_premises3 and nonaffine_loss3,
            "proof": "The first noninjective factor follows a bijective prefix, loses distinguishable inputs, and no deterministic suffix recovers them. Thus any total bijection uses only bijective affine primitives. The target is a degree-2 nonaffine bijection.",
            "aliases": "excluded; all operation role indices are distinct",
            "total_four_bit_preserving_workspace_proven_impossible": all(
                is_affine(t) for t in raw4.values() if len(set(t)) == 16),
            "scope": "the declared six low-level schemas, arbitrary distinct-carrier assignments, fixed straight-line programs, complete binary cubes"},
        "workspace": {
            "admissible_input_indices": initial, "required_output_indices": required,
            "workspace_contract": "W=0 at entry and exit; one of the existing five carriers",
            "four_bit_basis": {"raw_operation_count": len(raw4), "canonical_operation_count": len(b4),
                               "operations": ops4, "aliases": aliases4,
                               "properties": {name: table_properties(t) for name, t in raw4.items()}},
            "search": search, "selected_executor": selected_ops,
            "selected_canonical_word": canonical_selected,
            "selected_full_table": selected_full, "prefixes": prefix_rows,
            "all_shortest_canonical_words": words, "all_shortest_raw_label_words": raw_words,
            "restricted_behavioral_classes": 1,
            "full_behavioral_classes": [{"table": t, "program_indices": members}
                                        for t, members in classes.items()],
            "real_file_class_representatives": len(classes),
            "real_file_class_representative_rows": 16 * len(classes),
            "initialization_observation": "Selected executor ignores prior W and clears it for all 16 inputs; zero initialization is not needed for data behavior, but the prior workspace value is not preserved.",
            "minimum_workspace_bits": 1,
            "minimum_length": len(selected_ops)},
        "regressions": {"normal_and_recoded_role_guard_rows": role_rows,
                        "physical_assignments": 24, "selector_reuse_executions": reuse_rows,
                        "selector_preserved_each_selected_prefix": True},
        "selector_recoding": {
            "mask": 8, "data_coordinates_complemented": False, "invariant": False,
            "transported_full_table": recoded_full, "selected_executor": recoded_ops,
            "selected_canonical_word": canonical_recoded, "search": recoded_search,
            "all_shortest_canonical_words": recoded_words,
            "all_shortest_raw_label_words": recoded_raw_words,
            "full_behavioral_classes": [{"table": t, "program_indices": members}
                                        for t, members in recoded_classes.items()],
            "real_file_class_representatives": len(recoded_classes),
            "real_file_class_representative_rows": 16 * len(recoded_classes),
            "conjugation_executor_length": len(conjugated),
            "minimum_length": len(recoded_ops)},
        "earned_claim": "A persistent distinction selects IDENTITY or SWAP across independent data through one fixed externally supplied executor of existing runtime transformations, using one expendable existing workspace carrier.",
        "external_contributions": {
            "carrier_state": "harness assigns roles, initializes selector/data, declares expendable workspace and controls resets",
            "laws": "existing runtime tables; no added task-specific primitive",
            "representation": "harness assigns the two selector meanings and recoding",
            "sequencing": "external synthesis, fixed word retention, operation calls, reuse schedule and stopping",
            "environment": "temporary files and supplied independent data; no intervening environment transition",
            "evaluator": "experiment supplies the complete desired map and exact output/selector/workspace checks"},
        "unearned": ["arbitrary programs as data", "stored sequences", "general interpreter", "program synthesis inside runtime", "self-modification", "endogenous search", "autonomous execution control"],
        "new_primitive_needed_for_restricted_target": False,
        "next_frontier": "How much effective-transformation selection can a fixed executor encode, and how does expendable workspace constrain it? No extension implemented.",
    }


def factorized_family() -> tuple[Table, ...]:
    """Selector index 2*C0+C1; execution order X then S (S composed with X)."""
    return tuple(tuple(((b << 1) | (a ^ c0)) if c1 else (((a ^ c0) << 1) | b)
                       for a, b in states(2)) for c0, c1 in states(2))


def flat_family() -> tuple[Table, ...]:
    """Lookup comparator differs only at code 11: X after S, rather than S after X.

    This supplied lookup collapses to the opposite-order factorization. That is
    a result, not evidence that flat lookup is intrinsically unstructured.
    """
    return ((0, 1, 2, 3), (0, 2, 1, 3), (2, 3, 0, 1), (2, 0, 3, 1))


def flat_executor() -> tuple[Operation, ...]:
    return (("evaluate", (2, 3, 4)), ("evaluate", (0, 4, 3)),
            ("plastic", (2, 4, 1)), ("evaluate", (3, 4, 2)),
            ("xor", (2, 3)), ("xor", (3, 4)))


def selector_transport(family: Sequence[Table], permutation: Table) -> tuple[Table, ...]:
    """phi acts on selector codes alone: physical code phi(old code)."""
    if sorted(permutation) != list(range(4)):
        raise ValueError("Selector map must be a bijection on four codes")
    inverse = tuple(permutation.index(i) for i in range(4))
    return tuple(family[inverse[i]] for i in range(4))


def selector_conjugated_executor(operations: Sequence[Operation], permutation: Table) -> tuple[Operation, ...]:
    """Transport uses phi^-1 first, original executor, then phi."""
    b = two_bit_basis()
    closure2, _, saturated = closure(sample_basis(2, b), 8)
    if not saturated or permutation not in closure2:
        raise AssertionError("Selector permutation has no established support")
    inverse = tuple(permutation.index(i) for i in range(4))
    return tuple(b[name] for name in closure2[inverse]) + tuple(operations) + tuple(b[name] for name in closure2[permutation])


def family_table(family: Sequence[Table], workspace: bool = False) -> Table:
    """Preserve selectors and apply their extensional data map; discard old W."""
    if len(family) != 4 or any(sorted(table) != list(range(4)) for table in family):
        raise ValueError("Declare four data permutations")
    target = tuple((code << 2) | family[code][data] for code in range(4) for data in range(4))
    return tuple(2 * target[i // 2] for i in range(32)) if workspace else target


def factorized_executor() -> tuple[Operation, ...]:
    """Known upper bound, never a special-case search restriction."""
    roles = (1, 2, 3, 4)  # Prior C,A,B,W are now C1,A,B,W.
    return (("xor", (0, 2)),) + tuple((kind, tuple(roles[i] for i in indices))
                                    for kind, indices in selected_swap_workspace_program())


def symbolic_program_search(width: int, initial: Table, target: Table, length: int,
                            max_programs: int = 128, timeout_ms: int = 120_000,
                            enumerate_all: bool = True,
                            alternatives: Sequence[Table] | None = None,
                            wall_seconds: float = 180.0,
                            allowed_schemas: Sequence[str] | None = None,
                            incremental_rows: bool = False,
                            injective_prefixes: bool = False,
                            boundary_target: Table | None = None,
                            boundary_coordinates: Sequence[int] | None = None) -> tuple[list[tuple[Operation, ...]], dict[str, object]]:
    """Exact finite-word constraint search, an external meta-tool.

    A single operation choice per position is shared by EVERY declared input.
    Whole-coordinate bitplanes encode all persistent effects, including copy.
    Canonical schemas omit memory/XOR and evaluator-input-order aliases only.
    UNKNOWN/timeout never means absence or completeness. Model blocking
    projects on operation choices, so each returned word appears once.
    """
    import time
    import z3
    if width < 2 or width > 6 or len(initial) != len(target) or length < 0:
        raise ValueError("Invalid finite search domain")
    rows = len(initial)
    if injective_prefixes and (len(set(initial)) != rows or len(set(target)) != rows):
        raise ValueError("Prefix injectivity is admissible only for an injective declared contract")
    solver = z3.SolverFor("QF_BV")
    solver.set(timeout=timeout_ms, random_seed=0)
    full = (1 << rows) - 1
    planes: list[z3.BitVecRef] = [z3.BitVecVal(sum(((state >> (width - 1 - j)) & 1) << r
                              for r, state in enumerate(initial)), rows) for j in range(width)]
    choices = []
    boundary_conditions = []
    if boundary_target is not None and len(boundary_target) != rows:
        raise ValueError("Boundary rows must correspond to initial rows")
    coordinates = tuple(range(width)) if boundary_coordinates is None else tuple(boundary_coordinates)
    if any(j < 0 or j >= width for j in coordinates):
        raise ValueError("Invalid boundary coordinate")
    for step in range(length):
        kind, d, t, m = (z3.BitVec(f"op_{step}_{name}", 3) for name in ("kind", "d", "t", "m"))
        choices.append((kind, d, t, m))
        if allowed_schemas is not None:
            schema_indices = [("toggle", "xor", "copy", "evaluate", "plastic").index(name)
                              for name in allowed_schemas]
            solver.add(z3.Or(*(kind == index for index in schema_indices)))
        solver.add(z3.ULT(kind, 5), z3.ULT(d, width), z3.ULT(t, width), z3.ULT(m, width))
        # Canonical calls: toggle fixes unused roles; xor fixes its unused m.
        solver.add(z3.Implies(kind == 0, z3.And(t == 0, m == 0)))
        solver.add(z3.Implies(kind == 1, z3.And(d != t, m == 0)))
        solver.add(z3.Implies(z3.UGE(kind, 2), z3.And(d != t, d != m, t != m)))
        solver.add(z3.Implies(kind == 3, z3.ULT(d, t)))
        def select(index: z3.BitVecRef) -> z3.BitVecRef:
            result = planes[-1]
            for j in range(width - 2, -1, -1):
                result = cast(z3.BitVecRef, z3.If(index == j, planes[j], result))
            return cast(z3.BitVecRef, result)
        driver, old_target, selector = select(d), select(t), select(m)
        outputs: list[z3.BitVecRef] = []
        for j in range(width):
            expression = z3.If(kind == 0, z3.If(d == j, planes[j] ^ full, planes[j]),
                         z3.If(kind == 1, z3.If(t == j, driver ^ old_target, planes[j]),
                         z3.If(kind == 2, z3.If(t == j, driver, z3.If(m == j, old_target, planes[j])),
                         z3.If(kind == 3, z3.If(m == j, driver ^ old_target, planes[j]),
                               z3.If(t == j, driver ^ (old_target & ~selector), planes[j])))))
            output = z3.BitVec(f"plane_{step}_{j}", rows)
            solver.add(output == expression)
            outputs.append(output)
        if injective_prefixes:
            encoded_rows = [z3.Concat(*(z3.Extract(row, row, plane) for plane in outputs))
                            for row in range(rows)]
            solver.add(z3.Distinct(*encoded_rows))
        planes = outputs
        if boundary_target is not None and step + 1 < length:
            boundary_conditions.append(z3.And(*(planes[j] == sum(
                ((state >> (width - 1 - j)) & 1) << r
                for r, state in enumerate(boundary_target)) for j in coordinates)))
    if boundary_target is not None:
        # A single cut shared by all rows; this is an external search constraint.
        solver.add(z3.Or(*boundary_conditions))
    goal_targets = (target,) if alternatives is None else tuple(alternatives)
    goal = z3.BitVec("goal", max(1, (len(goal_targets) - 1).bit_length()))
    asserted_rows = {0} if incremental_rows else set(range(rows))
    refinement_checks = 0
    if incremental_rows:
        if alternatives is not None:
            raise ValueError("Incremental row refinement currently requires one target")
        solver.add(goal == 0)
        for j, plane in enumerate(planes):
            solver.add((plane & 1) == ((target[0] >> (width - 1 - j)) & 1))
    else:
        solver.add(z3.Or(*(z3.And(goal == g, *(plane == sum(((state >> (width - 1 - j)) & 1) << r
                                                            for r, state in enumerate(required))
                                              for j, plane in enumerate(planes)))
                           for g, required in enumerate(goal_targets))))
    words: list[tuple[Operation, ...]] = []
    goal_witnesses: dict[int, tuple[Operation, ...]] = {}
    started = time.perf_counter()
    status = "unknown"
    complete = False
    stop_reason = None
    while True:
        remaining_ms = int(1000 * (wall_seconds - (time.perf_counter() - started)))
        if remaining_ms <= 0:
            stop_reason = "wall time cap"
            break
        solver.set(timeout=min(timeout_ms, remaining_ms))
        result = solver.check()
        if result == z3.unsat:
            status = "sat" if words else "unsat"
            complete = True
            break
        if result != z3.sat:
            status = "unknown"
            stop_reason = solver.reason_unknown()
            break
        model = solver.model()
        if incremental_rows:
            output_planes = [cast(z3.BitVecNumRef, model.eval(plane, model_completion=True)).as_long()
                             for plane in planes]
            concrete_outputs = tuple(sum(((plane >> row) & 1) << (width - 1 - j)
                                for j, plane in enumerate(output_planes)) for row in range(rows))
            mismatch = next((row for row in range(rows) if concrete_outputs[row] != target[row]), None)
            if mismatch is not None:
                bit = 1 << mismatch
                for j, plane in enumerate(planes):
                    solver.add((plane & bit) == (((target[mismatch] >> (width - 1 - j)) & 1) << mismatch))
                asserted_rows.add(mismatch)
                refinement_checks += 1
                continue
        assignments = [tuple(cast(z3.BitVecNumRef, model.eval(v, model_completion=True)).as_long() for v in choice) for choice in choices]
        word: list[Operation] = []
        for k, d_value, t_value, m_value in assignments:
            schema = ("toggle", "xor", "copy", "evaluate", "plastic")[k]
            roles = ((d_value,) if k == 0 else (d_value, t_value) if k == 1
                     else (d_value, t_value, m_value))
            word.append((schema, roles))
        words.append(tuple(word))
        goal_index = cast(z3.BitVecNumRef, model.eval(goal, model_completion=True)).as_long()
        goal_witnesses[goal_index] = tuple(word)
        if len(words) % 10 == 0:
            print(f"constraint search length={length}: {len(words)} words retained", flush=True)
        status = "sat"
        if not enumerate_all or len(words) >= max_programs:
            stop_reason = "one witness requested" if not enumerate_all else "program storage cap"
            break
        if alternatives is not None:
            solver.add(goal != goal_index)
        else:
            solver.add(z3.Or(*(variable != value for choice, values in zip(choices, assignments, strict=True)
                               for variable, value in zip(choice, values, strict=True))))
    return sorted(words), {"method": "complete finite bit-vector constraint search",
                          "width": width, "domain_rows": rows, "length": length,
                          "boundary_required": boundary_target is not None,
                          "boundary_coordinates": list(coordinates) if boundary_target is not None else None,
                          "allowed_schemas": list(allowed_schemas) if allowed_schemas is not None else None,
                          "incremental_rows": incremental_rows, "injective_prefixes": injective_prefixes, "asserted_row_count": len(asserted_rows),
                          "refinement_checks": refinement_checks,
                          "solver_version": z3.get_version_string(), "timeout_per_check_ms": timeout_ms,
                          "program_storage_cap": max_programs, "status": status,
                          "enumeration_complete": complete, "programs_retained": len(words), "goal_witnesses": goal_witnesses,
                          "seconds": round(time.perf_counter() - started, 3),
                          "unknown_reason": solver.reason_unknown() if status == "unknown" else None,
                          "wall_seconds_cap": wall_seconds, "stop_reason": stop_reason,
                          "frontier_sizes": None,
                          "frontier_note": "constraint search represents all words at this exact length; no materialized BFS frontier"}


def factorized_selection_experiment(search_records: dict[str, object]) -> dict[str, object]:
    """Evidence assembly in the same format; search records remain external support."""
    import inspect
    ops4 = role_complete_basis(4)
    raw4 = sample_basis(4, ops4)
    ops5 = role_complete_basis(5)
    raw5 = sample_basis(5, ops5)
    basis5, aliases5 = canonical_basis(raw5)
    target = family_table(factorized_family())
    assert sorted(target) == list(range(16)) and not is_affine(target)
    assert all(is_affine(t) for t in raw4.values() if len(set(t)) == 16)
    selected = factorized_executor()
    full_target = family_table(factorized_family(), True)
    assert sample_program(5, selected) == full_target
    flat_target = family_table(flat_family(), True)
    assert sample_program(5, flat_executor()) == flat_target
    schema_names = {(kind, roles): name for name, (kind, roles) in ops5.items()}

    def witness_summary(key: str, required: Table) -> dict[str, object]:
        data = search_records[key]
        if not isinstance(data, dict):
            raise ValueError("Expected retained search record")
        words = [tuple((kind, tuple(roles)) for kind, roles in word) for word in data['words']]
        classes = set()
        labels: list[Program] = []
        canonical_words: list[Program] = []
        for word in words:
            table = tuple(range(32))
            names = []
            for operation in word:
                op_table = raw5[schema_names[operation]]
                name = next(n for n, t in basis5.items() if t == op_table)
                names.append(name)
                table = compose(table, op_table)
            assert table == required
            classes.add(table)
            canonical_words.append(tuple(names))
            labels.extend(product(*(aliases5[name] for name in names)))
        return {'search': data['evidence'], 'retained_canonical_words': canonical_words,
                'retained_raw_label_words': sorted(set(labels)),
                'canonical_count_lower_bound': len(words), 'labeled_count_lower_bound': len(set(labels)),
                'exact_total_shortest_count': len(words) if data['evidence']['enumeration_complete'] else None,
                'full_behavioral_classes': len(classes),
                'class_scope': 'All valid words have this same complete 32-row map by the total-domain criterion.'}

    transport_rows = []
    flat_transport_rows = []
    for phi in permutations(range(4)):
        assert is_affine(phi)
        for family, executor, destination in (
            (factorized_family(), selected, transport_rows), (flat_family(), flat_executor(), flat_transport_rows),
        ):
            transported_family = selector_transport(family, phi)
            word = selector_conjugated_executor(executor, phi)
            required = family_table(transported_family, True)
            assert sample_program(5, word) == required
            destination.append({'selector_permutation': phi, 'affine': True,
                                'executor': word, 'witness_length_upper_bound': len(word),
                                'target': required, 'real_file_rows': 32})
    physical_rows = 0
    reuse_rows = 0
    with tempfile.TemporaryDirectory() as directory:
        physical = tuple(Path(directory) / name for name in (
            '.arxmentis-state', '.arxmentis-state-2', '.arxmentis-memory', '.arxmentis-policy', '.arxmentis-policy-1'))
        for paths in permutations(physical):
            for i, initial in enumerate(states(5)):
                assert execute(initial, selected, paths) == states(5)[full_target[i]]
                physical_rows += 1
        for c0, c1 in states(2):
            execute((c0, c1, 0, 0, 1), (), physical)
            saved = tuple(p.read_bytes() for p in physical[:2])
            for a, b in states(2) * 2:
                runtime.write_state(a, physical[2])
                runtime.write_state(b, physical[3])
                for operation in selected:
                    apply_operation(operation, physical)
                    assert tuple(p.read_bytes() for p in physical[:2]) == saved
                expected = (c0, c1, *states(2)[factorized_family()[2 * c0 + c1][2 * a + b]], 0)
                assert tuple(runtime.read_state(p) for p in physical) == expected
                reuse_rows += 1
    identity, swap, toggle_a, swap_after_toggle = factorized_family()
    assert compose(toggle_a, swap) == swap_after_toggle
    opposite = compose(swap, toggle_a)
    assert opposite != swap_after_toggle and opposite == flat_family()[3]
    for c0, c1 in states(2):
        contribution = compose(toggle_a if c0 else identity, swap if c1 else identity)
        assert contribution == factorized_family()[2 * c0 + c1]
    return {
        'roles': ['C0', 'C1', 'A', 'B', 'W'],
        'convention': 'selector index=2*C0+C1; program order X then S; compose(first,second)=second after first',
        'selector_meanings': ['IDENTITY', 'S', 'X', 'S after X'],
        'family': factorized_family(), 'target_four_bit': table_properties(target), 'target_rows': table_rows(target, 4),
        'target_five_bit': table_properties(full_target),
        'workspace_contract': 'all 32 initial states; discard arbitrary old W; final W=0',
        'no_workspace': {'proven_impossible_all_lengths': True,
                         'basis_operations': ops4, 'properties': {name: table_properties(t) for name, t in raw4.items()},
                         'proof': 'A first noninjective factor irreversibly merges total-cube inputs. Every bijective factor is affine, so every realizable total bijection is affine. Target is a nonaffine bijection.'},
        'minimum_workspace_bits': 1,
        'basis_five_bit': {'operations': ops5, 'raw_count': len(raw5), 'canonical_count': len(basis5),
                           'canonical_tables': basis5, 'aliases': aliases5,
                           'properties': {name: table_properties(t) for name, t in raw5.items()}},
        'minimum_executor_length': 7, 'selected_executor': selected,
        'minimal_length_checks': search_records['main_minimum'],
        'shortest_witnesses': witness_summary('main_enumeration', full_target),
        'encoding_independent_runtime_check': search_records['encoding_check'],
        'composition_law': {'X': toggle_a, 'S': swap, 'code_11': swap_after_toggle,
                            'independent_composition': compose(toggle_a, swap), 'opposite_order': opposite,
                            'differing_data_indices': [i for i in range(4) if opposite[i] != swap_after_toggle[i]],
                            'order_source': 'executor structure; selector bits determine inclusion only'},
        'regressions': {'physical_assignments': 120, 'physical_full_state_rows': physical_rows,
                        'persistent_reuse_executions': reuse_rows,
                        'selectors_preserved_every_selected_primitive': True},
        'selector_transport': {'definition': 'phi on selectors alone; F_phi=phi F phi^-1',
                               'all_24_affine': True, 'all_24_realizable': True,
                               'recodings': transport_rows, 'bounded_joint_search': search_records['transport_search'],
                               'minimum_lengths_all_24_established': False,
                               'grouping_scope': 'witness length upper bounds, not universal minimum lengths'},
        'flat_comparison': {'family': flat_family(), 'meanings': ['IDENTITY','S','X','X after S'],
                            'selection_rationale': 'Change only code 11 to the measured opposite order; keep component data maps and degree controlled.',
                            'target_four_bit': table_properties(family_table(flat_family())),
                            'minimum_workspace_bits': 1, 'minimum_executor_length': 6,
                            'selected_executor': flat_executor(), 'minimal_length_checks': search_records['flat_minimum'],
                            'shortest_witnesses': witness_summary('flat_enumeration', flat_target),
                            'all_24_transported_recodings': flat_transport_rows,
                            'factorization_discovered': 'This lookup itself equals S^C1 then X^C0; flat versus factorized is not an intrinsic carrier type.',
                            'executable_compression_advantage': -1,
                            'comparison_limit': 'Main seven versus opposite-order lookup six; order-specific cost, not a universal flat/factorized distinction.'},
        'additional_unrelated_flat_probe': {'family': ((0,1,2,3),(0,2,1,3),(2,3,0,1),(1,0,3,2)),
                                           'target_four_bit': table_properties(family_table(((0,1,2,3),(0,2,1,3),(2,3,0,1),(1,0,3,2)))),
                                           'search': search_records['cubic_flat_probe'],
                                           'realizability_with_one_workspace': 'unresolved; not found through timed length-eight queries is not impossibility',
                                           'minimum_length': None, 'compression_comparison': 'unresolved'},
        'search_source_sha256': hashlib.sha256(inspect.getsource(symbolic_program_search).encode()).hexdigest(),
        'earned_claim': 'Two persisted selector bits factorize four effective data transformations by inclusion of X and S; one fixed externally supplied executor composes their effects in externally supplied order.',
        'external_contributions': {'carrier_state': 'initialization, data interventions, five existing capacities, expendable W',
                                   'laws': 'unchanged low-level runtime maps; solver formalization independently replayed',
                                   'representation': 'assigned selector meanings and recoding maps',
                                   'sequencing': 'external synthesis, witness storage, invocation, fixed order, process schedule and stopping',
                                   'environment': 'temporary persistent file backend and external data',
                                   'evaluator': 'complete target table, preserved selectors and workspace normalization'},
        'unearned': ['arbitrary sequences as data','selector-controlled ordering','variable length programs',
                    'stored primitive identities','instruction pointer','general interpreter','endogenous synthesis',
                    'autonomous execution','self-modification'],
        'next_boundary': 'Can persistent state encode order as well as inclusion? Not implemented.',
    }


def order_family() -> tuple[Table, ...]:
    """Total natural semantics; selector index 4*CX+2*CS+O, data index 2*A+B."""
    identity, swap, toggle_a, swap_after_toggle = factorized_family()
    opposite = compose(swap, toggle_a)
    return (identity, identity, swap, swap, toggle_a, toggle_a, swap_after_toggle, opposite)


def order_target() -> Table:
    return tuple((code << 2) | order_family()[code][data]
                 for code in range(8) for data in range(4))


def order_domain() -> Table:
    """Only canonical selector codes at entry and exit; ascending full-state indices."""
    return tuple((code << 2) | data for code in (0, 2, 4, 6, 7) for data in range(4))


def order_flat_recoding() -> Table:
    """Explicit affine code permutation: phi(CX,CS,O)=(CX XOR O,CS,O)."""
    return tuple(code ^ (4 if code & 1 else 0) for code in range(8))


def transport_selector_cube(table: Table, permutation: Table) -> Table:
    """Conjugate only the three selector bits; preserve physical data encoding."""
    if len(table) != 32 or sorted(permutation) != list(range(8)):
        raise ValueError("Declare a full three-bit selector permutation")
    inverse = tuple(permutation.index(i) for i in range(8))
    result = []
    for physical in range(32):
        old = (inverse[physical >> 2] << 2) | (physical & 3)
        output = table[old]
        result.append((permutation[output >> 2] << 2) | (output & 3))
    return tuple(result)


def trace_restricted_program(initial: Table, operations: Sequence[Operation],
                             reserved_codes: Sequence[int] = (1, 3, 5)) -> list[dict[str, object]]:
    """Keep actual full-cube maps, restricted images, collisions and reserved-code visits."""
    prefix = tuple(range(32))
    current = initial
    rows: list[dict[str, object]] = []
    for step, operation in enumerate(operations, 1):
        primitive = sample_program(5, (operation,))
        next_image = tuple(primitive[state] for state in current)
        prefix = compose(prefix, primitive)
        rows.append({'step': step, 'operation': operation,
                     'primitive_full_image_size': len(set(primitive)),
                     'incoming_reachable_indices': current,
                     'restricted_primitive_injective': len(set(next_image)) == len(current),
                     'outgoing_reachable_indices': next_image,
                     'prefix_full_image_size': len(set(prefix)),
                     'prefix_restricted_image_size': len(set(next_image)),
                     'reserved_selector_visits': [{'initial_index': i, 'intermediate_index': result,
                                                    'selector_code': result >> 2}
                                                  for i,result in zip(initial,next_image,strict=True)
                                                  if result >> 2 in reserved_codes]})
        current = next_image
    return rows


def order_executor() -> tuple[Operation, ...]:
    """Externally discovered fixed word; five roles CX,CS,O,A,B, no workspace."""
    return (('xor', (0, 3)), ('xor', (4, 3)), ('xor', (3, 2)), ('xor', (3, 4)), ('toggle', (1,)), ('plastic', (3, 2, 1)), ('xor', (2, 4)), ('plastic', (3, 2, 1)), ('xor', (3, 2)), ('toggle', (1,)), ('xor', (4, 3)))


def order_flat_executor() -> tuple[Operation, ...]:
    """Witness for phi(CX,CS,O)=(CX XOR O,CS,O); no minimum claim."""
    return (('toggle', (1,)), ('xor', (4, 3)), ('xor', (0, 3)), ('xor', (1, 2)), ('plastic', (3, 2, 1)), ('plastic', (4, 2, 1)), ('plastic', (3, 4, 1)), ('xor', (2, 3)), ('plastic', (2, 4, 1)), ('plastic', (2, 4, 1)), ('xor', (4, 2)), ('toggle', (1,)))


def selector_independent_data_linear_part(table: Table, domain: Table) -> bool:
    """Check the invariant (c,z)->(g(c),L*z+h(c)), with one shared data matrix L."""
    signatures = []
    for code in sorted({i >> 2 for i in domain}):
        outputs = tuple(table[4*code+data] for data in range(4))
        if len({value >> 2 for value in outputs}) != 1:
            return False
        differences = tuple((value & 3) ^ (outputs[0] & 3) for value in outputs)
        if differences[3] != differences[1] ^ differences[2]:
            return False
        signatures.append(differences)
    return len(set(signatures)) == 1


def persistent_order_experiment(search_records: dict[str, object]) -> dict[str, object]:
    """Audit the partial specification against real runtime tables and files."""
    calls = role_complete_basis(5)
    raw = sample_basis(5, calls)
    basis, aliases = canonical_basis(raw)
    target, domain = order_target(), order_domain()
    required = tuple(target[i] for i in domain)
    assert len(set(target)) == 32 and not is_affine(target)
    assert all(is_affine(table) for table in raw.values() if len(set(table)) == 32)
    assert all(len(set(table)) < 32 for table in raw.values() if not is_affine(table))
    # Rank <=16 can never be followed by an injective twenty-output map.
    viable = {name: table for name, table in basis.items() if len(set(table)) >= 20}
    layers, counts = restricted_frontiers(viable, domain, 3, 250_000)
    assert all(bytes(required) not in layer for layer in layers)
    canonical_only = {name: table for name, table in basis.items()
                      if {table[i] for i in domain} == set(domain)}
    assert all(selector_independent_data_linear_part(table, domain) for table in canonical_only.values())
    assert not selector_independent_data_linear_part(target, domain)
    selected = order_executor()
    actual = sample_program(5, selected)
    assert tuple(actual[i] for i in domain) == required
    trace = trace_restricted_program(domain, selected)
    for row in trace:
        incoming = cast(Table, row['incoming_reachable_indices'])
        row['all_nonaffine_primitive_restricted_image_sizes'] = {
            name: len({table[i] for i in incoming})
            for name, table in basis.items() if not is_affine(table)}
        assert row['prefix_restricted_image_size'] == 20
        assert row['restricted_primitive_injective']
        # A single globally clean bit would leave at most sixteen configurations.
        assert all(len({(i >> bit) & 1 for i in incoming}) == 2 for bit in range(5))
    phi = order_flat_recoding()
    flat_domain = tuple(sorted((phi[i >> 2] << 2) | (i & 3) for i in domain))
    flat_target = transport_selector_cube(target, phi)
    flat_actual = sample_program(5, order_flat_executor())
    assert all(flat_actual[i] == flat_target[i] for i in flat_domain)
    # Transport uses two ordinary XOR calls, never a harness selector branch.
    conjugated = (('xor', (2, 0)), *selected, ('xor', (2, 0)))
    assert sample_program(5, conjugated) == transport_selector_cube(actual, phi)
    remap_rows = reuse_rows = flat_rows = 0
    with tempfile.TemporaryDirectory() as directory:
        physical = tuple(Path(directory) / name for name in (
            '.arxmentis-state', '.arxmentis-state-2', '.arxmentis-memory',
            '.arxmentis-policy', '.arxmentis-policy-1'))
        for paths in permutations(physical):
            for i in domain:
                assert execute(states(5)[i], selected, paths) == states(5)[target[i]]
                remap_rows += 1
        for code in (0, 2, 4, 6, 7):
            paths = physical
            execute((*states(3)[code], 0, 0), (), paths)
            saved = tuple(path.read_bytes() for path in paths[:3])
            for a, b in states(2) * 2:
                runtime.write_state(a, paths[3]); runtime.write_state(b, paths[4])
                for operation in selected:
                    apply_operation(operation, paths)
                assert tuple(path.read_bytes() for path in paths[:3]) == saved
                assert tuple(runtime.read_state(p) for p in paths) == states(5)[target[4*code+2*a+b]]
                reuse_rows += 1
        for i in flat_domain:
            assert execute(states(5)[i], order_flat_executor(), physical) == states(5)[flat_target[i]]
            assert execute(states(5)[i], conjugated, physical) == states(5)[flat_target[i]]
            flat_rows += 2
    restrictions = {name: len({table[i] for i in domain}) for name, table in basis.items()
                    if not is_affine(table)}
    counterexample = sample_program(5, (('plastic', (1, 0, 2)),))
    assert len(set(counterexample)) == 24 and len({counterexample[i] for i in domain}) == 20
    lower_bounds = {}
    for label in ('hierarchical', 'flat'):
        checks = cast(dict[str, object], search_records[label])['records']
        proved: set[int] = set()
        for check in cast(list[dict[str, object]], checks):
            evidence = cast(dict[str, object], check['evidence'])
            if evidence['status'] == 'unsat' and evidence['enumeration_complete']:
                proved.add(cast(int, evidence['length']))
        lower = 0
        while lower in proved:
            lower += 1
        lower_bounds[label] = max(lower, 4 if label == 'hierarchical' else 0)
    result = {
        'roles': ['CX', 'CS', 'O', 'A', 'B'], 'configured_carrier_count': 5,
        'information_lower_bound': {'distinct_behaviors': 5, 'two_selector_bits_codes': 4,
                                    'minimum_selector_bits': 3, 'three_selector_bits_codes': 8,
                                    'claim': 'representation only; execution does not follow'},
        'total_semantics': {'family': order_family(), 'target': table_properties(target),
                            'rows': table_rows(target, 5),
                            'all_length_impossible': True,
                            'proof': 'A first globally noninjective primitive permanently reduces rank below 32; without one, every generator and composition is affine. The target is a nonaffine bijection.'},
        'primitive_inventory': {'raw_calls': len(raw), 'canonical_tables': len(basis),
                               'tables': [{'name': name, 'operation': calls[name], 'aliases': aliases[name],
                                           'table': table, 'image_size': len(set(table)), 'affine': is_affine(table)}
                                          for name, table in basis.items()],
                               'every_bijective_primitive_affine': True,
                               'every_nonaffine_primitive_globally_noninjective': True,
                               'rank_pruned_search_tables': len(viable),
                               'excluded': 'copy and evaluation have full image size 16 <20; memory aliases XOR'},
        'restricted_contract': {'canonical_selector_codes': [0, 2, 4, 6, 7],
                                'reserved_selector_codes': [1, 3, 5], 'domain': domain,
                                'required_outputs': required, 'entry_and_exit_rows': 20,
                                'reserved_codes_have_no_required_semantics': True},
        'reserved_states_necessary': {'canonical_domain_preserving_primitive_names': list(canonical_only),
                                      'invariant_verified_for_every_admitted_primitive': True,
                                      'target_violates_invariant': True,
                                      'all_length_proof': 'An injective twenty-row prefix confined to the twenty canonical states has image exactly that domain. Each next primitive must permute that domain. Every such primitive has control output independent of data and a shared, selector-independent linear data matrix. These properties survive composition, whereas the target selects both identity and swap matrices. Some prefix must leave the canonical domain.'},
        'restricted_counterexample': {'operation': ['plastic', [1, 0, 2]], 'full_image_size': 24,
                                     'restricted_outputs': [counterexample[i] for i in domain],
                                     'restricted_image_size': 20,
                                     'all_nonaffine_initial_restrictions': restrictions,
                                     'meaning': 'A globally noninjective primitive is injective on this twenty-state subset; the total proof does not extend.'},
        'independent_bfs': {'max_length': 3, 'table_cap': 250_000, 'new_at_length': counts,
                            'complete_through_bound': True, 'target_present': False,
                            'closure_saturated': False, 'basis_tables': len(viable)},
        'search_records': search_records,
        'executor': {'word': selected, 'length': len(selected), 'minimum_length': None,
                     'proved_lower_bound': lower_bounds['hierarchical'], 'upper_bound': len(selected),
                     'exact_shortest_count': None, 'retained_verified_words': 1,
                     'actual_full_cube': table_properties(actual), 'prefix_trace': trace,
                     'selectors_restored_at_exit': True, 'selectors_unchanged_at_every_prefix': False,
                     'minimum_dedicated_workspace_bits_for_restricted_contract': 0,
                     'five_bits_necessary_for_twenty_distinct_inputs': True,
                     'sixth_bit_required': False},
        'runtime_replay': {'physical_assignments': 120, 'remapping_rows': remap_rows,
                           'selector_reuse_executions': reuse_rows, 'flat_and_transport_rows': flat_rows,
                           'separate_processes': 'validated by PersistentOrderTests, recorded in validation_results.json'},
        'order_pair': {'110_data_outputs': order_family()[6], '111_data_outputs': order_family()[7],
                       'different_on_all_four_inputs': all(a != b for a,b in zip(order_family()[6],order_family()[7],strict=True))},
        'flat_comparison': {'selector_permutation': phi, 'inverse': phi,
                            'canonical_domain': flat_domain, 'required_outputs': [flat_target[i] for i in flat_domain],
                            'canonical_meanings': {'000': 'I', '100': 'X', '010': 'S', '110': 'X then S', '011': 'S then X'},
                            'word': order_flat_executor(), 'length': len(order_flat_executor()),
                            'minimum_length': None, 'proved_lower_bound': lower_bounds['flat'], 'exact_shortest_count': None,
                            'transported_total_target': table_properties(flat_target),
                            'actual_full_cube': table_properties(flat_actual),
                            'prefix_trace': trace_restricted_program(flat_domain, order_flat_executor(), (1, 5, 7)),
                            'conjugated_main_word_length': len(conjugated),
                            'executable_advantage_established': False,
                            'partial_degree_note': 'A partial map has no unique full-cube ANF; the declared transported total extension has degree three.'},
        'earned': 'Persistent state selects membership and relative order in a fixed two-generator family on the twenty canonical inputs, using representational slack without a dedicated workspace carrier.',
        'external_contributions': {'carrier': 'OS file persistence; harness roles and initialization',
                                   'law': 'unchanged hard-coded toggle, XOR and plastic transformations',
                                   'representation': 'harness declares five meanings, twelve inadmissible inputs and affine flat map',
                                   'sequencing': 'external solver discovers fixed word; Python harness retains and executes every position, with no selector-dependent branch',
                                   'environment': 'harness sets initial data and changes only data between executions; controls process lifetimes',
                                   'evaluator': 'experiment supplies complete desired twenty-row map, exact selector restoration and equality checks'},
        'unearned': ['shortest executor and counts', 'encoding cost advantage', 'arbitrary operation identities',
                    'variable length sequence representation', 'repeated instructions as stored data',
                    'instruction pointer', 'branching and loops', 'universal interpreter',
                    'endogenous synthesis or execution control', 'universal slack-as-workspace principle'],
        'next_boundary': 'Determine whether representational redundancy systematically substitutes for physical workspace; do not add sequence machinery yet.'}
    path = Path(__file__).resolve().parent / 'composition_results.json'
    if path.exists():
        previous = json.loads(path.read_text(encoding='utf-8'))
        result['preserved_previous_sections_sha256'] = {
            key: hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
            for key, value in previous.items() if key not in ('scope', 'persistent_order')}
    return result


def search_persistent_order(max_length: int = 12) -> dict[str, object]:
    """Explicit bounded reproduction. Timeouts leave minimality unresolved."""
    records: dict[str, object] = {}
    for label, phi in (('hierarchical', tuple(range(8))), ('flat', order_flat_recoding())):
        domain = tuple(sorted((phi[i >> 2] << 2) | (i & 3) for i in order_domain()))
        target = transport_selector_cube(order_target(), phi)
        checks = []
        for length in range(max_length + 1):
            words, evidence = symbolic_program_search(5, domain, tuple(target[i] for i in domain),
                length, enumerate_all=False, timeout_ms=120_000, wall_seconds=125,
                allowed_schemas=('toggle', 'xor', 'plastic'))
            checks.append({'words': words, 'evidence': evidence})
            if words:
                break
        records[label] = {'domain': domain, 'maximum_length': max_length, 'records': checks}
    return persistent_order_experiment(records)


def search_factorized_selection() -> dict[str, object]:
    """Explicit expensive reproduction; bounded search records use the existing evidence format."""
    records: dict[str, object] = {}
    for prefix, family, maximum in (("main", factorized_family(), 7), ("flat", flat_family(), 6)):
        checks = []
        for length in range(maximum + 1):
            words, evidence = symbolic_program_search(5, tuple(range(32)), family_table(family, True),
                                                       length, enumerate_all=False)
            checks.append({'words': words, 'evidence': evidence})
            if length < maximum and evidence['status'] != 'unsat':
                raise RuntimeError("Minimality reproduction unresolved; do not reuse a shortest claim")
        records[prefix + '_minimum'] = checks
        words, evidence = symbolic_program_search(5, tuple(range(32)), family_table(family, True), maximum)
        records[prefix + '_enumeration'] = {'words': words, 'evidence': evidence}
    basis, _ = canonical_basis(sample_basis(5, role_complete_basis(5)))
    _, evidence = symbolic_program_search(5, tuple(range(32)), next(iter(basis.values())), 1,
                                           alternatives=tuple(basis.values()), max_programs=256)
    records['encoding_check'] = {'raw_count': 225, 'canonical_count': 175, 'evidence': evidence}
    targets = tuple(family_table(selector_transport(factorized_family(), phi), True)
                    for phi in permutations(range(4)))
    queries = []
    for length in range(8):
        _, evidence = symbolic_program_search(5, tuple(range(32)), targets[0], length,
                                               alternatives=targets)
        queries.append(evidence)
    records['transport_search'] = {'selector_permutations': list(permutations(range(4))), 'searches': queries}
    cubic = ((0,1,2,3),(0,2,1,3),(2,3,0,1),(1,0,3,2))
    checks = []
    for length in range(9):
        words, evidence = symbolic_program_search(5,tuple(range(32)),family_table(cubic,True),length,
                                                   enumerate_all=False)
        checks.append({'words': words, 'evidence': evidence})
        if words:
            break
    records['cubic_flat_probe'] = checks
    return factorized_selection_experiment(records)


def state_space_slack(table: Table, domain: Table) -> dict[str, object]:
    """Cardinality facts only; unused configurations have representation-relative status."""
    size = len(table)
    if len(set(domain)) != len(domain) or any(i < 0 or i >= size for i in domain):
        raise ValueError("Declare a subset of the full finite domain")
    if any(i < 0 or i >= size for i in table):
        raise ValueError("A total table must map into its declared state space")
    image = len(set(table))
    restricted = len({table[i] for i in domain})
    return {'physical_states': size, 'declared_states': len(domain),
            'unused_states': size-len(domain), 'primitive_image_size': image,
            'necessary_slack_for_injective_restriction': size-image,
            'restricted_image_size': restricted, 'injective_on_domain': restricted == len(domain)}


def affine_extension(domain: Table, required: Table, width: int) -> dict[str, object]:
    """Exact GF(2) elimination, including a recoverable inconsistent row sum."""
    if len(domain) != len(required) or not domain:
        raise ValueError("Declare nonempty matching input/output rows")
    pivots: dict[int, tuple[int, int, int]] = {}
    for row, (state, output) in enumerate(zip(domain, required, strict=True)):
        feature, rhs, support = state | (1 << width), output, 1 << row
        while feature:
            pivot = feature.bit_length()-1
            if pivot not in pivots:
                pivots[pivot] = (feature, rhs, support)
                break
            old_feature, old_rhs, old_support = pivots[pivot]
            feature ^= old_feature; rhs ^= old_rhs; support ^= old_support
        if not feature and rhs:
            witness = [i for i in range(len(domain)) if support >> i & 1]
            return {'exists': False, 'contradiction_rows': witness,
                    'contradiction_input_indices': [domain[i] for i in witness],
                    'feature_xor': 0, 'output_xor': rhs}
    coefficients = [0]*(width+1)
    for pivot in sorted(pivots):
        feature, rhs, _ = pivots[pivot]
        for bit in range(pivot):
            if feature >> bit & 1:
                rhs ^= coefficients[bit]
        coefficients[pivot] = rhs
    table = []
    for state in range(1 << width):
        result = coefficients[width]
        for bit in range(width):
            if state >> bit & 1:
                result ^= coefficients[bit]
        table.append(result)
    assert all(table[i] == y for i,y in zip(domain,required,strict=True))
    return {'exists': True, 'coefficients': coefficients, 'table': tuple(table)}


def permutation_parity(outputs: Table, target_order: Table) -> int:
    """Sign relative to two ordered equally sized sets; no semantic equivalence."""
    if len(set(outputs)) != len(outputs) or set(outputs) != set(target_order):
        raise ValueError("Parity requires a bijection between the ordered sets")
    indices = {state:i for i,state in enumerate(target_order)}
    order = [indices[state] for state in outputs]
    return sum(order[i] > order[j] for i in range(len(order)) for j in range(i+1,len(order))) % 2


def affine_flat_complements() -> tuple[Table, ...]:
    """All complements of affine three-flats in the five-bit cube, exactly 620."""
    flats: set[Table] = set()
    for first, second in combinations(range(1,32),2):
        for a,b in product((0,1),repeat=2):
            flats.add(tuple(i for i in range(32) if (i & first).bit_count()%2 == a
                           and (i & second).bit_count()%2 == b))
    return tuple(sorted(tuple(i for i in range(32) if i not in flat) for flat in flats))


def rank24_orientation_certificate(basis: dict[str, Table]) -> dict[str, object]:
    """Complete signed set-transition graph; consistent potential proves even loops."""
    vertices = affine_flat_complements()
    indices = {value:i for i,value in enumerate(vertices)}
    adjacency: list[list[tuple[int,int]]] = [[] for _ in vertices]
    edges: list[tuple[int,str,int,int]] = []
    for source,domain in enumerate(vertices):
        for name,table in basis.items():
            if len(set(table)) < 24:
                continue
            outputs = tuple(table[i] for i in domain)
            if len(set(outputs)) != 24:
                continue
            target = tuple(sorted(outputs))
            if target not in indices:
                raise AssertionError("Reached-set shape invariant failed")
            destination = indices[target]
            sign = permutation_parity(outputs,target)
            edges.append((source,name,destination,sign))
            adjacency[source].append((destination,sign))
            adjacency[destination].append((source,sign))
    orientation = {0:0}
    queue = [0]
    for source in queue:
        for destination,sign in adjacency[source]:
            wanted = orientation[source] ^ sign
            if destination in orientation:
                if orientation[destination] != wanted:
                    raise AssertionError("Even-loop invariant contradicted by a primitive edge")
            else:
                orientation[destination] = wanted
                queue.append(destination)
    assert len(orientation) == len(vertices)
    return {'vertices': vertices, 'orientation': [orientation[i] for i in range(len(vertices))],
            'vertex_count': len(vertices), 'edge_count': len(edges),
            'affine_bijection_edges':sum(len(set(basis[name]))==32 for _,name,_,_ in edges),
            'plastic_edges':sum(len(set(basis[name]))==24 for _,name,_,_ in edges),
            'candidate_edges_examined':len(vertices)*sum(len(set(t))>=24 for t in basis.values()),
            'method':'exhaustive finite signed graph over all affine-three-flat complements',
            'vertex_cap':620,'timeout_seconds':None,'enumeration_complete':True,
            'signed_edges_sha256': hashlib.sha256(json.dumps(edges).encode()).hexdigest(),
            'all_edges_verified': True, 'connected': True,
            'proof': 'An injective 24-row prefix starts as the complement of an affine three-flat. Affine bijections preserve this shape; every injective plastic step fills its complete image, also such a complement. All admissible primitive edges satisfy sign=orientation(source) XOR orientation(destination). A path returning to its entry domain therefore has even sign.'}


def data_behavior_group() -> dict[Table, Program]:
    x = sample_program(2,(('toggle',(0,)),))
    swap = sample_program(2,(('xor',(0,1)),('xor',(1,0)),('xor',(0,1))))
    group,_,saturated = closure({'X':x,'S':swap},10,100)
    assert saturated and len(group) == 8
    return group


def behavior_extensions(count: int) -> list[dict[int,Table]]:
    """Every controlled extension; original five selector assignments are fixed."""
    if count not in (6,7,8):
        raise ValueError("This experiment admits six, seven or eight behaviors")
    known = {i:order_family()[i] for i in (0,2,4,6,7)}
    remaining = tuple(sorted(set(data_behavior_group())-set(known.values())))
    return [known | dict(zip(codes,maps,strict=True))
            for codes in combinations((1,3,5),count-5)
            for maps in permutations(remaining,count-5)]


def extension_contract(family: dict[int,Table], workspace: bool = False) -> tuple[Table,Table]:
    domain = tuple(i for i in range(64 if workspace else 32)
                   if (i >> (3 if workspace else 2)) in family)
    required = tuple(((i >> 3)<<3) + 2*family[i >> 3][(i >> 1)&3] if workspace
                     else ((i >> 2)<<2)+family[i >> 2][i&3] for i in domain)
    return domain,required


def subset_trajectory(width: int, domain: Table, word: Sequence[Operation],
                      sampled: dict[Operation,Table], reserved: Sequence[int]) -> list[dict[str,object]]:
    """Full reachable sets, hulls and next-operation ranks, including entry and exit."""
    current = domain
    prefix = tuple(range(1 << width))
    rows = []
    for step in range(len(word)+1):
        reachable = tuple(sorted(set(current)))
        origin = reachable[0]
        pivots: dict[int,int] = {}
        for value in reachable:
            vector = value ^ origin
            while vector:
                bit = vector.bit_length()-1
                if bit in pivots:
                    vector ^= pivots[bit]
                else:
                    pivots[bit] = vector
                    break
        codes = sorted({i >> (width-3) for i in reachable})
        next_table = sampled[word[step]] if step < len(word) else None
        rows.append({'step':step, 'ordered_outputs':current, 'reachable_set':reachable,
                     'cardinality':len(reachable), 'prefix_full_image_size':len(set(prefix)),
                     'inside_prefix_full_image':set(reachable).issubset(set(prefix)),
                     'selector_codes':codes, 'reserved_codes_occupied':sorted(set(codes)&set(reserved)),
                     'fixed_bit_values': [next(iter(values)) if len(values)==1 else None
                         for bit in range(width-1,-1,-1)
                         for values in ({(i >> bit)&1 for i in reachable},)],
                     'affine_hull_size':1 << len(pivots),
                     'next_operation':word[step] if step < len(word) else None,
                     'next_restricted_image_size':len({next_table[i] for i in reachable}) if next_table else None,
                     'next_is_injective':len({next_table[i] for i in reachable})==len(reachable) if next_table else None,
                     'next_fills_global_image':set(next_table[i] for i in reachable)==set(next_table) if next_table else None})
        if next_table is not None:
            current = tuple(next_table[i] for i in current)
            prefix = compose(prefix,next_table)
    return rows


def derived_controlled_toggle(first: int, second: int, target: int, workspace: int = 5) -> tuple[Operation,...]:
    """Recoverable five-call support with W=0 at entry/exit; no runtime primitive."""
    return (('xor',(first,workspace)),('plastic',(first,workspace,second)),
            ('xor',(workspace,target)),('plastic',(first,workspace,second)),('xor',(first,workspace)))


def workspace_completion_executor() -> tuple[Operation,...]:
    """All eight behaviors for the fixed completion 001:Y,011:SXY,101:XY."""
    clear: tuple[Operation,...] = (('evaluate',(0,1,5)),('xor',(0,5)),('xor',(1,5)))
    return (*clear,('xor',(3,4)),*derived_controlled_toggle(1,4,3),('xor',(3,4)),
            ('xor',(0,3)),*derived_controlled_toggle(0,1,3),*derived_controlled_toggle(1,2,3),
            ('xor',(2,4)),*derived_controlled_toggle(0,1,4))


def slack_workspace_experiment() -> dict[str,object]:
    """Finite geometric/parity audit, exact transports, and temporary workspace upper bounds."""
    import time
    started = time.perf_counter()
    operations = role_complete_basis(5)
    raw = sample_basis(5,operations)
    basis,aliases = canonical_basis(raw)
    sampled = {operations[name]:table for name,table in raw.items()}
    certificate = rank24_orientation_certificate(basis)
    group = data_behavior_group()
    b2 = sample_basis(2,two_bit_basis())
    group_rows = [{'table':table,'shortest_X_S_word':word,
                   'shortest_existing_two_bit_words':shortest_solutions(b2,lambda t:t==table,6),
                   'parity':permutation_parity(table,tuple(range(4)))} for table,word in group.items()]
    labels: dict[Table,str] = {(0,1,2,3):'I',(2,3,0,1):'X',(0,2,1,3):'S',
              (1,3,0,2):'S after X',(2,0,3,1):'X after S',
              (1,0,3,2):'Y = toggle B',(3,2,1,0):'XY = complement both',
              (3,1,2,0):'SXY = swap and complement both'}
    for row in group_rows:
        row['name'] = labels[cast(Table,row['table'])]
    group_order = tuple(group)
    group_relations = [[group_order.index(compose(a,b)) for b in group_order] for a in group_order]
    # Search only the three selector coordinates, retaining exact support for transports.
    control_ops = role_complete_basis(3)
    control_basis,_ = canonical_basis(sample_basis(3,control_ops))
    control_basis = {n:t for n,t in control_basis.items() if len(set(t)) >= 6}
    transport_words: dict[tuple[int,str],tuple[Operation,...]] = {}
    transport_records = []
    for code in (1,3,5):
        for direction in ('to_3','from_3'):
            entry = tuple(sorted((0,2,code,4,6,7))) if direction=='to_3' else (0,2,3,4,6,7)
            goal = tuple(3 if i==code else i for i in entry) if direction=='to_3' else tuple(code if i==3 else i for i in entry)
            layers,counts = restricted_frontiers(control_basis,entry,20,25_000)
            hits = [(depth,layer) for depth,layer in enumerate(layers) if bytes(goal) in layer]
            assert hits and not layers[-1] and sum(counts)==20_160
            depth = hits[0][0]
            names = frontier_witness(layers,bytes(goal),depth)
            word = tuple(control_ops[name] for name in names)
            transport_words[code,direction] = word
            transport_records.append({'code':code,'direction':direction,'domain':entry,'required':goal,
                'method':'complete BFS of injective six-row maps on the three-bit selector cube',
                'basis':list(control_basis),'basis_tables':15,'max_length':20,'table_cap':25_000,
                'timeout_seconds':None,'new_at_length':counts,'closure_saturated':True,
                'minimum_transport_length':depth,'word':word,'witness_count':1,
                'witness_enumeration_complete':False})
    cases: dict[str,list[dict[str,object]]] = {}
    live_five = live_six = 0
    for count in (6,7,8):
        rows = []
        for family in behavior_extensions(count):
            domain,required = extension_contract(family)
            affine = affine_extension(domain,required,5)
            assert not affine['exists']
            added = {code:table for code,table in family.items() if code in (1,3,5)}
            row: dict[str,object] = {'family':family,'added':added,'domain':domain,'required':required,
                'unused_states':32-len(domain),'reserved_codes':sorted(set(range(8))-set(family)),
                'affine_extension':affine,'target_parity':permutation_parity(required,domain)}
            if count==6:
                row['initial_injective_nonaffine_calls'] = [n for n,t in basis.items()
                    if not is_affine(t) and len({t[i] for i in domain})==24]
                code = next(iter(added))
                if row['target_parity']:
                    row.update(status='UNSAT proven',proof='rank-24 reached-set orientation invariant: target is odd',word=None)
                else:
                    word = transport_words[code,'to_3'] + order_executor() + transport_words[code,'from_3']
                    actual = sample_program(5,word)
                    assert tuple(actual[i] for i in domain)==required
                    trajectory = subset_trajectory(5,domain,word,sampled,cast(list[int],row['reserved_codes']))
                    assert all(x['cardinality']==24 for x in trajectory)
                    assert all(x['next_fills_global_image'] for x in trajectory
                               if x['next_operation'] and cast(Operation,x['next_operation'])[0]=='plastic')
                    row.update(status='SAT witness found',word=word,word_length=len(word),
                               minimum_length=None,proved_lower_bound=9,exact_shortest_count=None,
                               trajectory=trajectory)
                    with tempfile.TemporaryDirectory() as directory:
                        paths = tuple(Path(directory)/str(i) for i in range(5))
                        for initial,out in zip(domain,required,strict=True):
                            assert execute(states(5)[initial],word,paths)==states(5)[out]
                            live_five += 1
            else:
                row.update(status='UNSAT proven',proof='required rank exceeds every nonbijective primitive image; remaining affine bijections have no affine extension',word=None)
            if count==8:
                row['total_properties'] = table_properties(required)
            rows.append(row)
        cases[str(count)] = rows
    # Complete finite selector permutations using DERIVED gates with explicit runtime support.
    transport_support: dict[str,tuple[Operation,...]] = {}
    transport_tables: dict[str,Table] = {}
    for name,op in role_complete_basis(3).items():
        if op[0] in ('toggle','xor'):
            transport_support[name] = (op,)
            transport_tables[name] = sample_program(3,(op,))
    for target in range(3):
        drivers = tuple(i for i in range(3) if i != target)
        name = f'derived-controlled-toggle{drivers,target}'
        transport_support[name] = derived_controlled_toggle(drivers[0],drivers[1],target)
        transport_tables[name] = tuple(i ^ (1 << (2-target)) if all(i >> (2-d)&1 for d in drivers) else i for i in range(8))
    selector_group,selector_counts,saturated = closure(transport_tables,12,50_000)
    assert saturated and len(selector_group)==40_320
    base = {code:order_family()[code] for code in (0,2,4,6,7)} | {
        1:(1,0,3,2),3:(3,1,2,0),5:(3,2,1,0)}
    core = workspace_completion_executor()
    workspace_words = []
    sampled_six: dict[Operation,Table] = {}
    for family in behavior_extensions(8):
        phi = tuple(next(j for j in range(8) if family[j]==base[i]) for i in range(8))
        inverse = tuple(phi.index(i) for i in range(8))
        before = tuple(op for name in selector_group[inverse] for op in transport_support[name])
        after = tuple(op for name in selector_group[phi] for op in transport_support[name])
        # One internal normalization, then derived transports and the unchanged core.
        word = core[:3] + before + core[3:] + after
        for op in word:
            if op not in sampled_six:
                sampled_six[op] = sample_program(6,(op,))
        domain,required = extension_contract(family,True)
        actual = sample_program(6,word)
        assert actual==required
        canonical = tuple(i for i in domain if i&1==0)
        trajectory = subset_trajectory(6,canonical,word,sampled_six,())
        assert all(x['cardinality']==32 for x in trajectory)
        full_old_w = subset_trajectory(6,domain,word,sampled_six,())
        assert full_old_w[0]['cardinality']==64 and all(x['cardinality']==32 for x in full_old_w[1:])
        with tempfile.TemporaryDirectory() as directory:
            paths = tuple(Path(directory)/str(i) for i in range(6))
            for i,out in zip(domain,required,strict=True):
                assert execute(states(6)[i],word,paths)==states(6)[out]
                live_six += 1
        workspace_words.append({'family':family,'selector_permutation':phi,'inverse':inverse,
            'word':word,'word_length':len(word),'minimum_length':None,'domain':domain,'required':required,
            'canonical_W0_trajectory':trajectory,'both_old_W_values_trajectory':full_old_w,
            'actual_full_table':actual,'temporary_workspace_only':True,'final_W':0})
    seven_workspace = []
    for family in behavior_extensions(7):
        parent = next(row for row in workspace_words if all(cast(dict[int,Table],row['family'])[code]==table for code,table in family.items()))
        domain,required = extension_contract(family,True)
        actual = cast(Table,parent['actual_full_table'])
        assert tuple(actual[i] for i in domain)==required
        canonical = tuple(i for i in domain if not i&1)
        seven_workspace.append({'family':family,'parent_completion':parent['family'],
            'domain':domain,'required':required,'word_length':parent['word_length'],
            'proof':'restriction of a verified complete 64-input executor; each seven-code case uniquely determines its missing completion',
            'trajectory':subset_trajectory(6,canonical,cast(tuple[Operation,...],parent['word']),sampled_six,sorted(set(range(8))-set(family)))})
    root = Path(__file__).resolve().parent
    previous = json.loads((root/'composition_results.json').read_text(encoding='utf-8'))
    return {'baseline_commit':'5e062ae','finite_bound_proof':'If F is injective on D, |D|=|F(D)| <= |Im(F)|=R. Hence N-|D| >= N-R. This is necessary, not sufficient.',
        'primitive_slack':[{'name':name,'operation':operations[name],'aliases':aliases[name],
                           **state_space_slack(table,tuple(range(32)))} for name,table in basis.items()],
        'eight_behavior_group':group_rows,'group_composition_table':group_relations,'group_closure_X_S':{'max_length':10,'table_cap':100,'saturated':True,'size':8},
        'rank24_certificate':certificate,'selector_only_transports':transport_records,
        'extensions':cases,'five_bit_live_rows':live_five,
        'workspace':{'configured_runtime_carriers_added':0,'temporary_research_carriers':1,
            'physical_states':64,'core_word':core,'core_length':len(core),
            'clear_W_support':core[:3],'derived_controlled_toggle_support':derived_controlled_toggle(0,1,3),
            'selector_transport_group':{'size':len(selector_group),'new_at_length':selector_counts,'saturated':True,
                'max_length':12,'table_cap':50_000,'timeout_seconds':None,
                'basis_tables':transport_tables,'basis_runtime_support':transport_support,
                'method':'complete BFS of selector permutation tables, using explicitly derived five-call gates; not a new substrate basis',
                'minimum_runtime_word_lengths_claimed':False,'witness_enumeration_complete':False},
            'eight_completions':workspace_words,'all_eighteen_seven_extensions':seven_workspace,
            'live_rows':live_six,'workspace_state_comparison':[
                {'behaviors':k,'five_bit_unused_states':32-4*k,'six_bit_canonical_unused_states':64-4*k,
                 'canonical_distinctions':4*k,'old_W_admissible_input_states':8*k} for k in (5,6,7,8)]},
        'six_status_counts':{'SAT witness found':sum(row['status']=='SAT witness found' for row in cases['6']),
                             'UNSAT proven':sum(row['status']=='UNSAT proven' for row in cases['6']),
                             'bounded unresolved':0},
        'preserved_previous_sections_sha256':{key:hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()
                                             for key,value in previous.items() if key not in ('scope','slack_workspace')},
        'external_contributions':{'carrier':'five configured capacities, OS files; sixth path is temporary research-only',
            'law':'unchanged runtime primitives; derived gates retain complete support',
            'representation':'harness declares meaningful domains, reserves codes, and declares old W expendable',
            'sequencing':'external finite enumeration and fixed Python call sequences, no endogenous discovery or instruction pointer',
            'environment':'harness initializes values and chooses physical paths and process timing',
            'evaluator':'complete supplied targets, injectivity, exact selector/data/W outputs, parity and linear-algebra checks'},
        'earned':'Within these controlled extensions, three six-behavior encodings reach the eight-state slack bound, six fail by parity; all seven/eight encodings fail without extra capacity and are restored by one expendable research bit.',
        'unearned':['universal slack sufficiency','all-length minimum runtime words','equal cost of physical workspace and reserved codes','endogenous control','stored sequences'],
        'seconds':round(time.perf_counter()-started,3)}


def stored_instruction_target(recoded: bool = False) -> Table:
    """One common X/R alphabet, complete I,A,B,W target; old W is expendable."""
    x = sample_program(2, (("toggle", (0,)),))
    swap = sample_program(2, (("xor", (0, 1)), ("xor", (1, 0)), ("xor", (0, 1))))
    alphabet = (x, compose(x, swap))
    return tuple((i >> 3) * 8 + 2 * alphabet[(i >> 3) ^ int(recoded)][(i >> 1) & 3]
                 for i in range(16))


def stored_sequence_target(workspace: bool = True, recoded: bool = False) -> Table:
    """Derive the target from independent slot meanings, slot zero first."""
    one = stored_instruction_target(recoded)
    alphabet = tuple(tuple((one[8 * instruction + 2 * data] >> 1) & 3
                           for data in range(4)) for instruction in (0, 1))
    width = 5 if workspace else 4
    result = []
    for state in states(width):
        p0, p1, a, b = state[:4]
        data = alphabet[p1][alphabet[p0][2 * a + b]]
        result.append(((2 * p0 + p1) * 4 + data) * (2 if workspace else 1))
    return tuple(result)


def stored_instruction_executor(recoded: bool = False) -> tuple[Operation, ...]:
    """Minimum seven-call four-role decoder; unchanged runtime support."""
    swap = recoded_swap_workspace_program() if recoded else selected_swap_workspace_program()
    return (("toggle", (1,)),) + swap


def stored_slot_executor(slot: int, recoded: bool = False) -> tuple[Operation, ...]:
    """One schema transported to P0 or P1; other slot is untouched."""
    if slot not in (0, 1):
        raise ValueError("This fixed experiment has exactly two slots")
    roles = (slot, 2, 3, 4)
    return tuple((kind, tuple(roles[i] for i in indices))
                 for kind, indices in stored_instruction_executor(recoded))


def stored_sequence_executor(recoded: bool = False) -> tuple[Operation, ...]:
    """External fixed two-position grammar, no state-dependent harness branch."""
    return stored_slot_executor(0, recoded) + stored_slot_executor(1, recoded)


def sequence_trajectory(width: int, domain: Table, word: Sequence[Operation],
                        sampled: dict[Operation, Table]) -> list[dict[str, object]]:
    """The earlier trajectory format plus correct one/two-position program roles."""
    rows = subset_trajectory(width, domain, word, sampled, ())
    count = 2 if width == 5 else 1
    shift = width - count
    for stage in rows:
        reached = cast(Table, stage["reachable_set"])
        outputs = cast(Table, stage["ordered_outputs"])
        following = cast(Operation | None, stage["next_operation"])
        stage["program_coordinates"] = list(range(count))
        stage["program_codes"] = sorted({i >> shift for i in reached})
        stage["selector_codes"] = stage["program_codes"]  # Here the selectors are the one/two instruction positions.
        stage["program_values_preserved"] = all(a >> shift == b >> shift
                                                   for a, b in zip(domain, outputs, strict=True))
        stage["W_fixed_value"] = cast(list[int | None], stage["fixed_bit_values"])[-1]
        stage["next_globally_noninjective"] = (len(set(sampled[following])) < 1 << width
                                                if following is not None else None)
    return rows


def search_stored_sequence() -> dict[str, object]:
    """Bounded external searches, with clean-W relaxation only for lower bounds."""
    import time
    started = time.perf_counter()
    operations = role_complete_basis(4)
    basis, _ = canonical_basis(sample_basis(4, operations))
    initial = tuple(range(0, 16, 2))
    one: dict[str, object] = {}
    for recoded in (False, True):
        target = stored_instruction_target(recoded)
        words, evidence = meet_shortest_programs(basis, initial,
                                                tuple(target[i] for i in initial), 3, 3, 500_000)
        if words:
            raise AssertionError("The retained seven-call decoder lower bound was contradicted")
        one["recoded" if recoded else "native"] = {
            "initial": initial, "required": tuple(target[i] for i in initial),
            "basis": basis, "evidence": evidence, "timeout_seconds": None,
            "proved_absent_through": 6, "witness_enumeration_complete": True,
            "scope": "complete clean-W0 relaxation; excludes <=6 calls for arbitrary old W too"}
    target = stored_sequence_target()
    checks = []
    found: list[tuple[Operation, ...]] = []
    for length in range(8):
        timeout = 15_000 if length < 6 else 45_000 if length == 6 else 90_000
        words, evidence = symbolic_program_search(5, tuple(range(32)), target, length,
            timeout_ms=timeout, wall_seconds=timeout / 1000 + 5, enumerate_all=False)
        checks.append(evidence)
        found.extend(words)
        if words:
            break
    relaxed = []
    for length in (6, 7):
        if any(e["length"] == length and e["status"] == "unsat" for e in checks):
            continue
        if found and min(map(len, found)) <= length:
            break
        clean = tuple(range(0, 32, 2))
        words, evidence = symbolic_program_search(5, clean, tuple(target[i] for i in clean), length,
            timeout_ms=90_000, wall_seconds=95, enumerate_all=False,
            incremental_rows=True, injective_prefixes=True)
        relaxed.append({"words": words, "evidence": evidence})
        for word in words:
            if sample_program(5, word) == target:
                found.append(word)
    return {"one_slot": one, "global": {"target": target, "records": checks, "words": found},
            "relaxed": {"initial": tuple(range(0, 32, 2)),
                        "target": tuple(target[i] for i in range(0, 32, 2)), "records": relaxed},
            "seconds": round(time.perf_counter() - started, 3)}


def stored_sequence_experiment(searches: dict[str, object]) -> dict[str, object]:
    """Ground modular sequence evidence separately from a flat total lookup."""
    import subprocess
    import sys
    root = Path(__file__).resolve().parent
    previous = json.loads((root / "composition_results.json").read_text(encoding="utf-8"))
    alphabet = ((2, 3, 0, 1), (1, 3, 0, 2))
    x = sample_program(2, (("toggle", (0,)),))
    swap = sample_program(2, (("xor", (0, 1)), ("xor", (1, 0)), ("xor", (0, 1))))
    assert x == alphabet[0] and compose(x, swap) == alphabet[1]
    family = {2 * p0 + p1: compose(alphabet[p0], alphabet[p1]) for p0, p1 in states(2)}
    assert len(set(family.values())) == 4
    one_target = stored_instruction_target()
    target = stored_sequence_target()
    modular = stored_sequence_executor()
    global_data = cast(dict[str, object], searches["global"])
    candidates = [tuple((kind, tuple(roles)) for kind, roles in word)
                  for word in cast(list[tuple[Operation, ...]], global_data["words"])]
    roles = (1, 2, 3, 4)
    constructed = (("xor", (0, 1)),) + tuple((kind, tuple(roles[i] for i in indices))
                    for kind, indices in selected_swap_workspace_program()) + (
                    ("xor", (0, 1)), ("xor", (0, 2)), ("xor", (0, 3)))
    assert sample_program(5, constructed) == target
    candidates += [constructed, modular]
    shortest_found = min(candidates, key=lambda word: (len(word), word))
    assert sample_program(5, shortest_found) == target
    checks = cast(list[dict[str, object]], global_data["records"])
    relaxed = cast(dict[str, object], searches["relaxed"])
    negative = {cast(int, e["length"]) for e in checks if e["status"] == "unsat"}
    for row in cast(list[dict[str, object]], relaxed["records"]):
        evidence = cast(dict[str, object], row["evidence"])
        if evidence["status"] == "unsat":
            negative.add(cast(int, evidence["length"]))
    lower = 0
    while lower in negative:
        lower += 1
    minimum = len(shortest_found) if lower == len(shortest_found) else None
    sampled: dict[Operation, Table] = {}
    recoded_target = stored_sequence_target(recoded=True)
    recoded_global = shortest_found + (("toggle", (2,)), ("toggle", (3,)))
    assert sample_program(5, recoded_global) == recoded_target
    words = {"modular": modular, "global": shortest_found,
             "recoded_modular": stored_sequence_executor(True), "recoded_global": recoded_global}
    for word in words.values():
        for op in word:
            if op not in sampled:
                sampled[op] = sample_program(5, (op,))
    trajectories = {name: {
        "canonical_W0": sequence_trajectory(5, tuple(range(0, 32, 2)), word, sampled),
        "both_old_W": sequence_trajectory(5, tuple(range(32)), word, sampled)}
        for name, word in words.items()}
    for traces in trajectories.values():
        assert all(row["cardinality"] == 16 for row in traces["canonical_W0"])
    boundary_rows = []
    for initial in states(5):
        with tempfile.TemporaryDirectory() as directory:
            paths = tuple(Path(directory) / str(i) for i in range(5))
            mid = execute(initial, stored_slot_executor(0), paths)
            # Continue on existing files without resetting program, data or W.
            for op in stored_slot_executor(1):
                apply_operation(op, paths)
            final = tuple(runtime.read_state(path) for path in paths)
        p0, p1, a, b, _ = initial
        expected_mid = alphabet[p0][2 * a + b]
        assert mid == (p0, p1, expected_mid >> 1, expected_mid & 1, 0)
        assert final == states(5)[target[states(5).index(initial)]]
        boundary_rows.append({"initial": initial, "after_slot0": mid, "after_slot1": final})
    remapping_rows = 0
    with tempfile.TemporaryDirectory() as directory:
        physical = tuple(Path(directory) / name for name in (
            ".arxmentis-state", ".arxmentis-state-2", ".arxmentis-memory",
            ".arxmentis-policy", ".arxmentis-policy-1"))
        for paths in permutations(physical):
            for i, initial in enumerate(states(5)):
                assert execute(initial, modular, paths) == states(5)[target[i]]
                remapping_rows += 1
    substitutions = []
    for changed in (0, 1):
        with tempfile.TemporaryDirectory() as directory:
            paths = tuple(Path(directory) / str(i) for i in range(5))
            runtime.write_state(0, paths[0]); runtime.write_state(1, paths[1])
            before_bytes = tuple(path.read_bytes() for path in paths[:2])
            results = []
            for p in ((0, 1), (1, 1) if changed == 0 else (0, 0)):
                if p != (0, 1):
                    runtime.write_state(p[changed], paths[changed])
                    assert paths[1 - changed].read_bytes() == before_bytes[1 - changed]
                for a, b in states(2):
                    runtime.write_state(a, paths[2]); runtime.write_state(b, paths[3])
                    for op in modular:
                        apply_operation(op, paths)
                    output = tuple(runtime.read_state(path) for path in paths)
                    expected = family[2 * p[0] + p[1]][2 * a + b]
                    assert output == (*p, expected >> 1, expected & 1, 0)
                    results.append({"program": p, "data": (a, b), "output": output})
            substitutions.append({"changed_slot": changed, "results": results,
                                  "other_slot_bytes_preserved": True})
    reuse = 0
    with tempfile.TemporaryDirectory() as directory:
        paths = tuple(Path(directory) / str(i) for i in range(5))
        for p0, p1 in states(2):
            runtime.write_state(p0, paths[0]); runtime.write_state(p1, paths[1])
            runtime.write_state(1, paths[4])
            saved = tuple(path.read_bytes() for path in paths[:2])
            for a, b in states(2) * 2:
                runtime.write_state(a, paths[2]); runtime.write_state(b, paths[3])
                for op in modular:
                    apply_operation(op, paths)
                data = family[2 * p0 + p1][2 * a + b]
                assert tuple(runtime.read_state(path) for path in paths) == (p0, p1, data >> 1, data & 1, 0)
                assert tuple(path.read_bytes() for path in paths[:2]) == saved
                reuse += 1
    initialize = "from pathlib import Path; import sys,arxmentis as a; a.write_state(int(sys.argv[1]),Path(sys.argv[3])); a.write_state(int(sys.argv[2]),Path(sys.argv[4]))"
    consume = "from pathlib import Path; import sys,composition_experiments as r; p=tuple(Path(x) for x in sys.argv[1:]); [r.apply_operation(op,p) for op in r.stored_sequence_executor()]"
    initializers = consumers = 0
    with tempfile.TemporaryDirectory() as directory:
        paths = tuple(Path(directory) / str(i) for i in range(5))
        for p0, p1 in states(2):
            subprocess.run([sys.executable, "-B", "-c", initialize, str(p0), str(p1),
                            str(paths[0]), str(paths[1])], cwd=root, check=True, capture_output=True)
            initializers += 1
            runtime.write_state(1, paths[4])
            saved = tuple(path.read_bytes() for path in paths[:2])
            for a, b in states(2) * 2:
                runtime.write_state(a, paths[2]); runtime.write_state(b, paths[3])
                subprocess.run([sys.executable, "-B", "-c", consume, *(str(path) for path in paths)],
                               cwd=root, check=True, capture_output=True)
                data = family[2 * p0 + p1][2 * a + b]
                assert tuple(runtime.read_state(path) for path in paths) == (p0, p1, data >> 1, data & 1, 0)
                assert tuple(path.read_bytes() for path in paths[:2]) == saved
                consumers += 1
    one_sampled = {op: sample_program(4, (op,))
                   for op in set(stored_instruction_executor() + stored_instruction_executor(True))}
    one_traces = {str(recoded): sequence_trajectory(4, tuple(range(0, 16, 2)),
                  stored_instruction_executor(recoded), one_sampled) for recoded in (False, True)}
    no_workspace = {}
    for width, wanted in ((3, tuple((i >> 2) * 4 + alphabet[i >> 2][i & 3] for i in range(8))),
                          (4, stored_sequence_target(False))):
        raw = sample_basis(width, role_complete_basis(width))
        assert len(set(wanted)) == 1 << width and not is_affine(wanted)
        assert all(is_affine(t) for t in raw.values() if len(set(t)) == 1 << width)
        no_workspace[str(width)] = {"target": wanted, "properties": table_properties(wanted),
            "proof": "nonaffine total bijection; every bijective primitive is affine and any rank loss is irreversible"}
    # Position-role transport and a content edit are separately represented.
    sigma = (1, 0, 2, 3, 4)
    reordered = stored_slot_executor(1) + stored_slot_executor(0)
    reversed_table = sample_program(5, reordered)
    assert all(reversed_table[i] == ((i >> 3) * 8 + 2 * family[2 * ((i >> 3) & 1) + (i >> 4)][(i >> 1) & 3])
               for i in range(32))
    return {"alphabet": {"0": x, "1": compose(x, swap), "names": ["X", "R = S after X"]},
        "word_compositions": family, "four_distinct": True, "one_slot_target": one_target,
        "one_slot": {"roles": ["I", "A", "B", "W"], "native_word": stored_instruction_executor(),
            "recoded_word": stored_instruction_executor(True), "minimum_calls": 7,
            "recoded_minimum_calls": 7, "arbitrary_old_W": True, "final_W": 0,
            "zero_initialization_required": False, "search": searches["one_slot"], "trajectories": one_traces},
        "two_slot_target": target, "modular_word": modular, "modular_calls": len(modular),
        "global_word": shortest_found, "global_calls": len(shortest_found),
        "global_minimum_calls": minimum, "global_proved_lower_bound": lower,
        "global_search": global_data, "global_relaxation_search": relaxed,
        "global_shortest_word_count": None, "constructed_ten_call_upper": constructed,
        "properties": table_properties(target), "slot_boundary_rows": boundary_rows,
        "slot_schema_transport": {"roles": [[0, 2, 3, 4], [1, 2, 3, 4]],
            "same_schema": True, "other_slot_untouched": True, "full_cube_rows_each": 32},
        "physical_remapping": {"assignments": 120, "rows": remapping_rows, "word": "modular"},
        "local_substitutions": substitutions,
        "reuse": {"in_process_executions": reuse, "program_written_once_per_word": True,
            "data_only_rewrites_between_runs": True, "separate_initializers": initializers,
            "separate_consumers": consumers, "program_bytes_preserved": True},
        "recoding": {"instruction_mask_one_slot": 8, "instruction_mask_two_slot": 24,
            "one_slot_target": stored_instruction_target(True), "two_slot_target": recoded_target,
            "modular_word": words["recoded_modular"], "global_word": recoded_global,
            "global_calls_upper_bound": len(recoded_global), "global_minimum_calls": None,
            "same_literal_syntax_required": False},
        "position_mapping": {"carrier_role_permutation": sigma,
            "transport": "remap state and executor together; same logical word and data result",
            "contents_edit": "fixed role map, exchange the two stored values; mixed words change order",
            "consume_reversed_word": reordered, "consume_reversed_table": reversed_table,
            "distinction": "reversed consumption and swapped contents agree on data, but preserve different final program bytes"},
        "flat_control": {"id_table": family, "target": target, "exact_same_full_target": True,
            "global_search_shared_by_exact_table_identity": True, "global_calls": len(shortest_found),
            "minimum_calls": minimum, "proved_lower_bound": lower, "dedicated_workspace_bits": 1,
            "properties": table_properties(target), "trajectory": trajectories["global"],
            "local_edit_data_effects_identical": True,
            "interpretation": "no execution-cost or extensional edit advantage over identically assigned flat IDs; modular factorization is independent evidence"},
        "trajectories": trajectories, "no_workspace_all_length_proofs": no_workspace,
        "minimum_dedicated_workspace_bits": 1, "configured_carriers_added": 0,
        "external_grammar": "Exactly two positions, common 0:X/1:R alphabet, consume P0 then P1; retained fixed call words supplied by Python, no endogenous invocation",
        "external_contributions": {"carrier": "five existing capacities and OS persistence",
            "law": "existing hard-coded equations; all effective support recoverable",
            "representation": "common instruction alphabet, two ordered positions, data roles, old W expendable",
            "sequencing": "external search, retained words, fixed two-slot scheduling",
            "environment": "harness initialization, data rewrites, physical paths and process lifetimes",
            "evaluator": "complete composition-derived target, slot-boundary semantics, exact program/W restoration"},
        "earned": "Two persistent positions independently store symbols from one common two-instruction alphabet; an externally supplied fixed executor consumes them in order with repetition, local substitution and reuse.",
        "unearned": ["arbitrary alphabets", "variable length", "program counter", "branches", "loops", "jumps",
            "arbitrary repetition counts", "endogenous program construction", "autonomous invocation",
            "general interpreter", "self modification", "intrinsic sequence semantics from the full target alone"],
        "preserved_previous_sections_sha256": {key: hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
            for key, value in previous.items() if key not in ("scope", "stored_sequence")}}



SEMANTIC_LENGTH_CODES = (0, 2, 4, 5, 6, 7)


def semantic_length_alphabet() -> tuple[Table, Table]:
    """Resample the common instruction meanings from current file operations."""
    x = sample_program(2, (("toggle", (0,)),))
    swap = sample_program(2, (("xor", (0, 1)), ("xor", (1, 0)), ("xor", (0, 1))))
    return x, compose(x, swap)


def semantic_length_family(alphabet: tuple[Table, Table]) -> dict[int, Table]:
    family = {code: (alphabet[(code >> 1) & 1] if code < 4 else
                    compose(alphabet[(code >> 1) & 1], alphabet[code & 1]))
              for code in SEMANTIC_LENGTH_CODES}
    if len(set(family.values())) != 6:
        raise AssertionError("Six composition-derived meanings are not distinct")
    return family


def semantic_length_target(alphabet: tuple[Table, Table]) -> Table:
    """Natural total five-bit semantics; physically preserve ignored P1."""
    return tuple((i & ~3) | (alphabet[(i >> 3) & 1][i & 3] if i < 16 else
                 compose(alphabet[(i >> 3) & 1], alphabet[(i >> 2) & 1])[i & 3])
                 for i in range(32))


def semantic_length_executor(recoding: str = "native") -> tuple[Operation, ...]:
    """Temporary six-role canonical witness with a fixed cut after seven calls.

    Prefix uses the common slot decoder. On canonical suffix entries P1=0
    whenever L=0, so factorized S^P1 X^L is identity for inactive slot 1.
    This is NOT the natural total extension on the reserved program codes.
    """
    if recoding not in ("native", "length", "instructions"):
        raise ValueError("Declare native, length or instruction encoding")
    prefix_roles = (1, 3, 4, 5)
    prefix = tuple((kind, tuple(prefix_roles[i] for i in roles))
                   for kind, roles in stored_instruction_executor(recoding == "instructions"))
    suffix_roles = (0, 2, 3, 4, 5)
    suffix = tuple((kind, tuple(suffix_roles[i] for i in roles))
                   for kind, roles in factorized_executor())
    if recoding != "native":
        changed = 0 if recoding == "length" else 2
        flip: tuple[Operation, ...] = (("toggle", (changed,)),)
        suffix = flip + suffix + flip
    return prefix + suffix


def semantic_length_contract(alphabet: tuple[Table, Table], workspace: bool = False,
                             recoding: str = "native") -> tuple[Table, Table, Table]:
    """Domain, endpoints, exact program/data slot boundary in corresponding row order."""
    if recoding not in ("native", "length", "instructions"):
        raise ValueError("Invalid representation map")
    mask = {"native": 0, "length": 16, "instructions": 12}[recoding]
    total = semantic_length_target(alphabet)
    domain = tuple(4 * code + data for code in SEMANTIC_LENGTH_CODES for data in range(4))
    outputs = tuple(total[i] for i in domain)
    boundary = tuple((i & ~3) | alphabet[(i >> 3) & 1][i & 3] for i in domain)
    if not workspace:
        return (tuple(i ^ mask for i in domain), tuple(i ^ mask for i in outputs),
                tuple(i ^ mask for i in boundary))
    return (tuple(2 * (i ^ mask) + w for i in domain for w in (0, 1)),
            tuple(2 * (i ^ mask) for i in outputs for _ in (0, 1)),
            tuple(2 * (i ^ mask) for i in boundary for _ in (0, 1)))


def semantic_length_cuts(initial: Table, boundary: Table, word: Sequence[Operation],
                         sampled: dict[Operation, Table]) -> list[int]:
    """All genuine fixed cuts, exact first five coordinates; W unconstrained."""
    current = initial
    cuts = []
    for step, op in enumerate(word, 1):
        current = tuple(sampled[op][i] for i in current)
        if step < len(word) and all(a >> 1 == b >> 1 for a, b in zip(current, boundary, strict=True)):
            cuts.append(step)
    return cuts


def search_semantic_length(alphabet: tuple[Table, Table]) -> dict[str, object]:
    """Separate external searches, after the all-length five-role obstruction."""
    initial, required, boundary = semantic_length_contract(alphabet, True)
    result: dict[str, object] = {}
    for name in ("endpoint", "boundary"):
        checks = []
        found = []
        for length in range(8):
            timeout = 5_000 if length < 5 else 20_000
            words, record = symbolic_program_search(6, initial, required, length,
                enumerate_all=False, timeout_ms=timeout, wall_seconds=timeout / 1000 + 1,
                boundary_target=boundary if name == "boundary" else None,
                boundary_coordinates=tuple(range(5)))
            checks.append(record)
            found.extend(words)
            print(f"semantic length {name}: {length} calls {record['status']}", flush=True)
            if words:
                break
        result[name] = {"checks": checks, "words": found,
            "scope": "48 rows, arbitrary old W; boundary search constrains one shared cut, W free at cut",
            "searched_through": checks[-1]["length"], "enumeration_of_all_shortest_words": False}
    return result


def semantic_length_experiment() -> dict[str, object]:
    """Prove five-role failure before temporary-workspace semantic tests."""
    import subprocess
    import sys
    root = Path(__file__).resolve().parent
    previous = json.loads((root / "composition_results.json").read_text(encoding="utf-8"))
    alphabet = semantic_length_alphabet()
    family = semantic_length_family(alphabet)
    total = semantic_length_target(alphabet)
    initial5, target5, boundary5 = semantic_length_contract(alphabet)
    raw = sample_basis(5, role_complete_basis(5))
    basis, _ = canonical_basis(raw)
    certificate = rank24_orientation_certificate(basis)
    assert initial5 in cast(tuple[Table, ...], certificate["vertices"])
    assert len(set(total)) == 32 and not is_affine(total)
    assert all(is_affine(t) for t in raw.values() if len(set(t)) == 32)
    assert permutation_parity(target5, initial5) == 1
    assert permutation_parity(boundary5, initial5) == 1
    # These invariant checks gate the authorized temporary sixth file.
    searches = search_semantic_length(alphabet)
    words = {name: semantic_length_executor(name) for name in ("native", "length", "instructions")}
    sampled = {op: sample_program(6, (op,)) for word in words.values() for op in word}
    full_tables = {name: sample_program(6, word) for name, word in words.items()}
    contracts = {name: semantic_length_contract(alphabet, True, name) for name in words}
    trajectories = {}
    recodings = {}
    for name, word in words.items():
        initial, required, boundary = contracts[name]
        assert tuple(full_tables[name][i] for i in initial) == required
        cuts = semantic_length_cuts(initial, boundary, word, sampled)
        assert 7 in cuts
        clean = tuple(initial[i] for i in range(0, len(initial), 2))
        reserved = sorted(set(range(8)) - {i >> 3 for i in initial})
        traces = subset_trajectory(6, clean, word, sampled, reserved)
        assert all(row["cardinality"] == 24 for row in traces)
        assert all(row["next_is_injective"] for row in traces[:-1])
        if name == "native":
            assert all(not row["reserved_codes_occupied"] for row in traces)
        trajectories[name] = {"canonical_W0": traces,
            "both_old_W": subset_trajectory(6, initial, word, sampled, reserved)}
        recodings[name] = {"domain": initial, "required": required, "boundary": boundary,
            "canonical_program_codes": sorted({i >> 3 for i in initial}), "reserved_program_codes": reserved,
            "word": word, "upper_bound": len(word), "minimum": None, "fixed_cuts": cuts,
            "reserved_codes_visited": sorted({c for row in traces for c in cast(list[int], row["reserved_codes_occupied"])}),
            "five_carrier_impossible": True, "full_extension": table_properties(full_tables[name])}
    boundary_rows = []
    with tempfile.TemporaryDirectory() as directory:
        paths = tuple(Path(directory) / str(i) for i in range(6))
        for name, word in words.items():
            initial, required, boundary = contracts[name]
            for state, output, cut_state in zip(initial, required, boundary, strict=True):
                mid = execute(states(6)[state], word[:7], paths)
                assert mid == states(6)[cut_state]
                for op in word[7:]:
                    apply_operation(op, paths)
                final = tuple(runtime.read_state(p) for p in paths)
                assert final == states(6)[output]
                boundary_rows.append({"encoding": name, "input": state, "cut": mid, "output": final})
    summaries = {}
    for name, value in searches.items():
        record = cast(dict[str, object], value)
        candidates = cast(list[tuple[Operation, ...]], record["words"]) + [words["native"]]
        word = min(candidates, key=lambda w: (len(w), w))
        for op in word:
            if op not in sampled:
                sampled[op] = sample_program(6, (op,))
        actual = sample_program(6, word)
        initial, required, boundary = contracts["native"]
        assert tuple(actual[i] for i in initial) == required
        cuts = semantic_length_cuts(initial, boundary, word, sampled)
        if name == "boundary":
            assert cuts
        negative = {cast(int, c["length"]) for c in cast(list[dict[str, object]], record["checks"])
                    if c["status"] == "unsat"}
        lower = 0
        while lower in negative:
            lower += 1
        summaries[name] = {"word": word, "upper_bound": len(word), "lower_bound": lower,
            "minimum": len(word) if lower == len(word) else None, "fixed_cuts": cuts,
            "unresolved_lengths": [k for k in range(lower, len(word)) if k not in negative],
            "search": record}
    remapping = 0
    with tempfile.TemporaryDirectory() as directory:
        physical = tuple(Path(directory) / name for name in (".arxmentis-state", ".arxmentis-state-2",
            ".arxmentis-memory", ".arxmentis-policy", ".arxmentis-policy-1"))
        workspace = Path(directory) / "W-temporary"
        for assignment in permutations(physical):
            paths = (*assignment, workspace)
            for i in range(0, 48, 2):
                state = contracts["native"][0][i]
                mid = execute(states(6)[state], words["native"][:7], paths)
                assert mid == states(6)[contracts["native"][2][i]]
                for op in words["native"][7:]:
                    apply_operation(op, paths)
                assert tuple(runtime.read_state(p) for p in paths) == states(6)[contracts["native"][1][i]]
                remapping += 1
    interventions = []
    with tempfile.TemporaryDirectory() as directory:
        paths = tuple(Path(directory) / str(i) for i in range(6))
        for first, second, changed in ((0, 4, 0), (2, 6, 0), (4, 5, 2), (6, 7, 2), (4, 6, 1), (5, 7, 1)):
            for data in range(4):
                first_state = states(6)[8 * first + 2 * data]
                before = execute(first_state, words["native"], paths)
                program_bytes = tuple(p.read_bytes() for p in paths[:3])
                runtime.write_state(states(3)[second][changed], paths[changed])
                assert all(paths[j].read_bytes() == program_bytes[j] for j in range(3) if j != changed)
                runtime.write_state(data >> 1, paths[3]); runtime.write_state(data & 1, paths[4])
                for op in words["native"]:
                    apply_operation(op, paths)
                after = tuple(runtime.read_state(p) for p in paths)
                assert before == (*states(3)[first], family[first][data] >> 1, family[first][data] & 1, 0)
                assert after == (*states(3)[second], family[second][data] >> 1, family[second][data] & 1, 0)
                if changed == 0:
                    assert before[3:5] != after[3:5]
                interventions.append({"codes": [first, second], "changed_coordinate": changed,
                    "data": data, "before": before, "after": after, "other_program_bytes_unchanged": True})
    initialize = "from pathlib import Path; import sys,arxmentis as r; [r.write_state(int(v),Path(p)) for v,p in zip(sys.argv[1:4],sys.argv[4:7])]"
    consume = "from pathlib import Path; import sys,composition_experiments as r; p=tuple(Path(s) for s in sys.argv[1:]); [r.apply_operation(op,p) for op in r.semantic_length_executor()]"
    consumers = 0
    with tempfile.TemporaryDirectory() as directory:
        paths = tuple(Path(directory) / str(i) for i in range(6))
        for code in SEMANTIC_LENGTH_CODES:
            subprocess.run([sys.executable, "-B", "-c", initialize, *(str(v) for v in states(3)[code]),
                            *(str(p) for p in paths[:3])], cwd=root, check=True, capture_output=True)
            saved = tuple(p.read_bytes() for p in paths[:3])
            runtime.write_state(1, paths[5])
            for data in tuple(range(4)) * 2:
                runtime.write_state(data >> 1, paths[3]); runtime.write_state(data & 1, paths[4])
                subprocess.run([sys.executable, "-B", "-c", consume, *(str(p) for p in paths)],
                               cwd=root, check=True, capture_output=True)
                assert tuple(p.read_bytes() for p in paths[:3]) == saved
                assert tuple(runtime.read_state(p) for p in paths) == (
                    *states(3)[code], family[code][data] >> 1, family[code][data] & 1, 0)
                consumers += 1
    flat = tuple((4 * code + family[code][data]) for code in SEMANTIC_LENGTH_CODES for data in range(4))
    assert flat == target5
    return {"roles": ["L", "P0", "P1", "A", "B"], "alphabet": alphabet,
        "program_family": family, "six_distinct": True,
        "representation": {"minimum_bits": 3, "codes": 8, "programs": 6,
                           "execution_does_not_follow_from_capacity": True},
        "natural_total": table_properties(total), "canonical_domain": initial5,
        "canonical_target": target5, "canonical_boundary": boundary5,
        "five_carrier": {"endpoint": "impossible at every length", "boundary": "impossible at every length",
            "target_parity": 1, "boundary_parity": 1, "certificate": certificate,
            "raw_basis_calls": len(raw), "unique_basis_tables": len(basis),
            "rank_counts_raw": {str(k): sum(len(set(t)) == k for t in raw.values()) for k in (16, 24, 32)},
            "all_bijective_primitives_affine": True,
            "proof": "total: nonaffine bijection cannot follow rank loss or compose from affine bijections; canonical: odd permutation contradicts complete even-loop orientation certificate",
            "geometry": "Every 24-row viable prefix is an affine-three-flat complement; plastic fills its global 24-state image, copy/evaluate rank16 cannot preserve24. No five-role witness exists, including a witness staying in canonical codes."},
        "temporary_workspace": {"configured_added": 0, "temporary_bits": 1, "old_W_arbitrary": True,
            "final_W": 0, "minimum_extra_binary_capacity": 1, "native_word": words["native"],
            "native_cut": 7, "native_upper_bound": 14, "searches": summaries,
            "scope": "canonical48 physical rows quotient to24 required program/data distinctions; not natural total semantics on reserved codes",
            "physical_remapping_assignments": 120, "physical_remapping_rows": remapping,
            "cut_rows": boundary_rows, "trajectories": trajectories,
            "reserved_codes_visited_native": [],
            "global_extension_differs_from_natural_on_reserved": True},
        "interventions": interventions,
        "reuse": {"initializer_processes": 6, "consumer_processes": consumers,
            "executions_per_program": 8, "data_only_rewrites": True, "program_bytes_preserved": True},
        "recodings": recodings, "length_mask_five": 16, "instruction_mask_five": 12,
        "flat_control": {"canonical_target": flat, "identical_endpoint_target": True,
            "five_carrier_impossible": True, "temporary_endpoint_search_shared_by_table_identity": True,
            "boundary_constraint_additional": True, "no_cost_advantage_claimed": True},
        "earned": "With one temporary extra binary capacity, persistent state represents instruction content and whether slot1 is active; a fixed external word realizes common slot0 semantics at one cut and conditionally slot1 afterward. Five configured capacities cannot realize this canonical target.",
        "external_contributions": {"carrier": "five existing roles plus temporary W, filesystem/process persistence",
            "law": "unchanged hard-coded toggle/XOR/copy/plastic/evaluation equations",
            "representation": "max two slots; common X/R alphabet; P1=0 canonical when L=0; logical role assignments and recoding maps",
            "sequencing": "external search/construction and retained word; slot0 first, slot1 second; fixed14 calls regardless length; no endogenous invocation",
            "environment": "program initialization, data rewrites, physical paths, process scheduling",
            "evaluator": "composition-derived target, all-input shared cut, exact program restoration, intervention criteria"},
        "next_boundary": "persistent execution-state distinction identifying the active stored position; not implemented",
        "preserved_previous_sections_sha256": {key: hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
            for key, value in previous.items() if key not in ("scope", "semantic_length")}}

def run_experiments() -> dict[str, object]:
    b2 = sample_basis(2, two_bit_basis())
    b3_ops = three_bit_basis()
    b3 = sample_basis(3, b3_ops)
    c2, n2, saturated2 = closure(b2, 8)
    c3, n3, saturated3 = closure(b3, 4)
    gate_program = ("xor(d,t)", "plastic(d,t,s)")
    gate = program_table(gate_program, b3)
    gate_expected = tuple(states(3).index((d, t if s == 0 else d, s))
                          for d, t, s in states(3))
    if gate != gate_expected:
        raise AssertionError({"gated_write_actual": table_rows(gate, 3)})
    gate_ops = tuple(b3_ops[name] for name in gate_program)
    if sample_program(3, gate_ops) != gate:
        raise AssertionError("Composed table differs from runtime execution")
    role_checks = role_remapping_check(gate_ops, gate)
    recoded_gate = transport(gate)
    recoding_counts = {"invariant": 0, "found_noninvariant": 0, "absent_at_bound": 0}
    for table in c3:
        recoded = transport(table)
        category = ("invariant" if table == recoded else
                    "found_noninvariant" if recoded in c3 else "absent_at_bound")
        recoding_counts[category] += 1
    adapt_basis: dict[str, Operation] = {
        "plastic(d,t,p)": ("plastic", (0, 1, 3)),
        "evaluate(d,t,m)": ("evaluate", (0, 1, 2)), "xor(m,p)": ("xor", (2, 3)),
    }
    adapt_tables = sample_basis(4, adapt_basis)
    adapt_actual = sample_program(4, (("adapt", (0, 1, 2, 3)),))
    adapt_shortest = shortest_solutions(adapt_tables, lambda t: t == adapt_actual, 3)
    if not adapt_shortest:
        raise AssertionError("Adapt did not reduce over the declared audit basis")
    predict_basis: dict[str, Operation] = {
        "evaluate(d,t,m)": ("evaluate", (0, 1, 2)),
        "xor(t,m)": ("xor", (1, 2)), "toggle(m)": ("toggle", (2,)),
    }
    predict_tables = sample_basis(3, predict_basis)
    predict_actual = sample_program(3, (("predict", (0, 2)),))
    predict_shortest = shortest_solutions(predict_tables, lambda t: t == predict_actual, 3)
    if not predict_shortest:
        raise AssertionError("Prediction state map did not reduce")
    context_actual = sample_program(5, (("context", (0, 1, 2, 3, 4)),))
    context_lower = contextual_lower_table()
    if context_actual != context_lower:
        raise AssertionError("Context protocol did not reduce with external branch")
    # Instance: 10 -> 01. Its criterion has no operation sequence.
    instance = shortest_solutions(b2, lambda table: table[2] == 1, 4)
    swap = tuple(states(2).index((b, a)) for a, b in states(2))
    class_solutions = shortest_solutions(b2, lambda table: table == swap, 4)
    solution_rows = [{
        "program": program, "table": program_table(program, b2),
        "swap_class_successes": [state for i, state in enumerate(states(2))
                                 if program_table(program, b2)[i] == swap[i]],
    } for program in instance]
    with tempfile.TemporaryDirectory() as directory:
        physical = tuple(Path(directory) / name for name in ("A", "B"))
        for paths in permutations(physical):
            for state in states(2):
                for program in class_solutions:
                    operations = tuple(two_bit_basis()[name] for name in program)
                    if execute(state, operations, paths) != tuple(reversed(state)):
                        raise AssertionError("Swap reuse failed under physical remapping")
    phi = ("toggle(d)", "toggle(t)", "toggle(s)")
    conjugation_verified = all(
        program_table(phi + witness + phi, b3) == transport(table)
        for table, witness in c3.items()
    )
    copy_audit_ops: dict[str, Operation] = {
        "evaluate(d,t,s)": ("evaluate", (0, 1, 2)),
        "xor(s,t)": ("xor", (2, 1)), "xor(d,s)": ("xor", (0, 2)),
    }
    copy_shortest = shortest_solutions(sample_basis(3, copy_audit_ops),
                                      lambda table: table == b3["copy(d,t,s)"], 3)
    evaluate_audit_ops: dict[str, Operation] = {
        "copy(d,t,s)": ("copy", (0, 1, 2)), "xor(d,t)": ("xor", (0, 1)),
        "xor(s,t)": ("xor", (2, 1)), "xor(d,s)": ("xor", (0, 2)),
    }
    evaluate_shortest = shortest_solutions(sample_basis(3, evaluate_audit_ops),
                                          lambda table: table == b3["evaluate(d,t,s)"], 4)
    if not copy_shortest or not evaluate_shortest:
        raise AssertionError("Copy/evaluation audit reduction failed")
    instance_replay_rows = 0
    transported_instance_same_program: list[Program] = []
    with tempfile.TemporaryDirectory() as directory:
        physical = tuple(Path(directory) / name for name in ("A", "B"))
        for program in instance:
            table = program_table(program, b2)
            if table[1] == 2:  # Complemented start 01 -> complemented goal 10.
                transported_instance_same_program.append(program)
            conjugated = ("toggle(a)", "toggle(b)") + program + ("toggle(a)", "toggle(b)")
            if program_table(conjugated, b2) != transport(table):
                raise AssertionError("Instance transport support mismatch")
            for paths in permutations(physical):
                for i, state in enumerate(states(2)):
                    ops = tuple(two_bit_basis()[name] for name in program)
                    if execute(state, ops, paths) != states(2)[table[i]]:
                        raise AssertionError("Instance physical remapping failed")
                    ops = tuple(two_bit_basis()[name] for name in conjugated)
                    if execute(state, ops, paths) != states(2)[transport(table)[i]]:
                        raise AssertionError("Instance recoded runtime replay failed")
                    instance_replay_rows += 2
    primitive_recoding = {name: {
        "invariant": transport(table) == table,
        "transported_table": transport(table),
        "shortest_support_in_b3": c3.get(transport(table)),
    } for name, table in b3.items()}
    obstruction = all(len({states(3)[table[i]][0] ^ state[0]
                           for i, state in enumerate(states(3))}) == 1
                      for table in b3.values())
    examples = {
        "gated_write": gate, "recoded_gated_write": recoded_gate,
        "double_copy": program_table(("copy(d,t,s)",) * 2, b3),
        "feedback_then_selection": program_table(
            ("evaluate(d,t,s)", "plastic(d,t,s)"), b3),
    }
    root = Path(__file__).resolve().parent
    hashes = {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
              for name in ("arxmentis.py", "test_arxmentis.py",
                           "composition_experiments.py", "test_composition_experiments.py")}
    result_path = root / "composition_results.json"
    retained_factorized = (json.loads(result_path.read_text(encoding="utf-8")).get("factorized_selection")
                           if result_path.exists() else None)
    return {
        "semantic_length": (json.loads(result_path.read_text(encoding="utf-8")).get("semantic_length")
                            if result_path.exists() else None),
        "stored_sequence": (json.loads(result_path.read_text(encoding="utf-8")).get("stored_sequence")
                            if result_path.exists() else None),
        "factorized_selection": retained_factorized,
        "slack_workspace": (json.loads(result_path.read_text(encoding="utf-8")).get("slack_workspace")
                            if result_path.exists() else None),
        "persistent_order": (json.loads(result_path.read_text(encoding="utf-8")).get("persistent_order")
                             if result_path.exists() else None),
        "mechanism_reification": mechanism_reification_experiment(c3),
        "scope": {"state_identity": "full value tuples; distinct existing valid files",
                  "excluded": ["aliasing", "file existence", "write traces", "stdout", "crashes"],
                  "table_cap": 50_000, "source_sha256": hashes},
        "two_bit": {"basis": b2, "new_at_length": n2, "unique_total": len(c2),
                    "saturated": saturated2,
                    "closure": [{"table": t, "shortest_witness": p} for t, p in c2.items()]},
        "three_bit": {
            "basis": b3, "new_at_length": n3, "unique_total": len(c3),
            "saturated": saturated3, "max_length": 4,
            "closure": [{"table": t, "shortest_witness": p} for t, p in c3.items()],
            "examples": {name: {"table": t, "shortest_witness": c3.get(t),
                                "rows": table_rows(t, 3)} for name, t in examples.items()},
            "all_length_unreachable_example": {
                "desired": "d'=t with t,s unchanged", "basis_obstruction_verified": obstruction,
                "proof": "Every generator has d'=d XOR a constant; composition preserves this.",
                "scope": "fixed-role B3 only; role-remapped existing functions can write d"}},
        "basis_reducibility": {
            "memory_equals_role_remapped_xor": b3["memory(t,s)"] == sample_program(3, (("xor", (2, 1)),)),
            "copy_shortest_over_declared_audit_basis": copy_shortest,
            "evaluation_shortest_over_declared_audit_basis": evaluate_shortest,
            "affine_candidates": {name: is_affine(table) for name, table in b3.items()},
            "plastic_irreducibility": "All other candidate maps are affine; affine maps are closed under composition; plastic is nonaffine.",
            "scope": "distinct-file value maps with corresponding arbitrary role assignments; no host conditional branching",
        },
        "gated_write": {"passed": True, "physical_permutation_rows": role_checks,
                        "all_shortest_over_b3": shortest_solutions(b3, lambda t: t == gate, 2)},
        "recoding": {"primitive_candidates": primitive_recoding,
                     "b3_closure_counts": recoding_counts,
                     "all_transports_have_existing_support_by_length_10": conjugation_verified,
                     "bounded_absence_is_not_full_closure_absence": True,
                     "gated_same_program_invariant": gate == recoded_gate,
                     "gated_transported_shortest": c3.get(recoded_gate),
                     "b2_transport_complete": all(transport(t) in c2 for t in c2)},
        "high_level": {
            "adapt": {"rows": 16, "shortest_over_declared_audit_basis": adapt_shortest},
            "predict_next": {"rows": 8, "shortest_over_declared_audit_basis": predict_shortest,
                             "interpretation": "Q=1-D1 is a programmer-supplied alternating model"},
            "adapt_context": {"rows": 32, "lower_protocol_matches": context_actual == context_lower,
                              "external_branch": "choose active policy path from d",
                              "straight_line_reduction": "not established"}},
        "problem_search": {
            "start": [1, 0], "goal": [0, 1], "basis": list(b2),
            "all_shortest_instance_solutions": solution_rows,
            "behavioral_classes": len({program_table(p, b2) for p in instance}),
            "instance_remap_and_transport_runtime_rows": instance_replay_rows,
            "same_instance_programs_solve_complemented_instance": transported_instance_same_program,
            "class_criterion": "swap every state in {0,1}^2",
            "all_shortest_class_solutions": class_solutions, "class_table": swap,
            "class_physical_remapping_rows": 2 * 4 * len(class_solutions),
            "same_class_program_complement_invariant": transport(swap) == swap,
            "agent_status": "external meta-tool search/replay; no endogenous program retention"},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--selector-search", action="store_true",
                        help="Recompute the bounded expensive two-selector searches; ordinary runs retain their certificate")
    parser.add_argument("--order-search", action="store_true",
                        help="Recompute bounded partial-domain order searches and runtime replay")
    parser.add_argument("--slack-experiment", action="store_true",
                        help="Recompute the finite slack/parity classification and temporary workspace witnesses")
    parser.add_argument("--sequence-search", action="store_true",
                        help="Recompute bounded fixed-length stored-sequence searches and runtime evidence")
    parser.add_argument("--length-experiment", action="store_true",
                        help="Recompute stored semantic length proof, separate searches and actual-file evidence")
    args = parser.parse_args()
    if args.length_experiment:
        # Append evidence without recomputing or changing any earlier section.
        result = json.loads(Path(__file__).with_name("composition_results.json").read_text(encoding="utf-8"))
        result["semantic_length"] = semantic_length_experiment()
    else:
        result = run_experiments()
    if args.selector_search:
        result['factorized_selection'] = search_factorized_selection()
    if args.order_search:
        result['persistent_order'] = search_persistent_order()
    if args.slack_experiment:
        result['slack_workspace'] = slack_workspace_experiment()
    if args.sequence_search:
        result["stored_sequence"] = stored_sequence_experiment(search_stored_sequence())
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
