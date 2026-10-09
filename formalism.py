from __future__ import annotations

from dataclasses import dataclass
from itertools import product


@dataclass(frozen=True)
class CapabilitySpec:
    """A capability claim with its causal assistance made explicit."""

    name: str
    claim: str
    endogenous: tuple[str, ...]
    exogenous: tuple[str, ...]
    evaluator: tuple[str, ...]


def bits_required(state_count: int) -> int:
    """Return the minimum number of binary distinctions needed for state_count states."""
    if state_count < 1:
        raise ValueError("state_count must be positive")
    return (state_count - 1).bit_length()


def can_retain_binary_past(memory_state_count: int) -> bool:
    """Whether memory_state_count states can preserve either value of one lost bit.

    We exhaustively search every encoder from {0,1} to the candidate memory states
    and every decoder from candidate memory state back to {0,1}.
    """
    if memory_state_count < 1:
        raise ValueError("memory_state_count must be positive")

    histories = (0, 1)
    for encoder in product(range(memory_state_count), repeat=len(histories)):
        for decoder in product((0, 1), repeat=memory_state_count):
            if all(decoder[encoder[history]] == history for history in histories):
                return True
    return False


def minimum_states_for_binary_past() -> int:
    """Smallest state count that can retain one binary past distinction."""
    for state_count in range(1, 3):
        if can_retain_binary_past(state_count):
            return state_count
    raise AssertionError("search bound should contain a solution")


def all_binary_context_mappings(context_count: int) -> tuple[tuple[int, ...], ...]:
    """All functions from context_count binary-indexed contexts to binary actions."""
    if context_count < 1:
        raise ValueError("context_count must be positive")
    return tuple(product((0, 1), repeat=context_count))


def can_represent_all_binary_context_mappings(
    memory_state_count: int,
    *,
    context_count: int = 2,
) -> bool:
    """Whether persistent state can encode every binary action mapping over contexts.

    A learned mapping is encoded into one persistent controller state. Later, a
    queried context and that state must recover the correct binary action. The
    search is exhaustive over all encoders and decoders.
    """
    if memory_state_count < 1:
        raise ValueError("memory_state_count must be positive")

    mappings = all_binary_context_mappings(context_count)
    mapping_count = len(mappings)

    for encoder in product(range(memory_state_count), repeat=mapping_count):
        for decoder_flat in product(
            (0, 1),
            repeat=memory_state_count * context_count,
        ):
            def decode(state: int, context: int) -> int:
                return decoder_flat[state * context_count + context]

            if all(
                decode(encoder[mapping_index], context) == mapping[context]
                for mapping_index, mapping in enumerate(mappings)
                for context in range(context_count)
            ):
                return True
    return False


def minimum_states_for_all_binary_context_mappings(
    *,
    context_count: int = 2,
) -> int:
    """Smallest persistent state space able to encode all binary context policies."""
    mapping_count = len(all_binary_context_mappings(context_count))
    for state_count in range(1, mapping_count + 1):
        if can_represent_all_binary_context_mappings(
            state_count,
            context_count=context_count,
        ):
            return state_count
    raise AssertionError("search bound should contain a solution")
