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
from itertools import permutations, product
from pathlib import Path

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
    return {
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
    args = parser.parse_args()
    rendered = json.dumps(run_experiments(), indent=2) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
