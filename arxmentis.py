from __future__ import annotations

import argparse
from pathlib import Path

STATE_FILE = Path(__file__).resolve().parent / ".arxmentis-state"
SECOND_STATE_FILE = Path(__file__).resolve().parent / ".arxmentis-state-2"
MEMORY_STATE_FILE = Path(__file__).resolve().parent / ".arxmentis-memory"
POLICY_STATE_FILE = Path(__file__).resolve().parent / ".arxmentis-policy"
DISTINCTION_STATE_FILES = {
    1: STATE_FILE,
    2: SECOND_STATE_FILE,
}


def read_state(path: Path = STATE_FILE) -> int:
    if not path.exists():
        return 0

    value = path.read_text(encoding="ascii").strip()
    if value not in {"0", "1"}:
        raise ValueError(f"Invalid persistent state in {path}: expected 0 or 1")
    return int(value)


def write_state(value: int, path: Path = STATE_FILE) -> None:
    if type(value) is not int or value not in (0, 1):
        raise ValueError("Persistent state must be 0 or 1")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{value}\n", encoding="ascii")


def toggle_state(path: Path = STATE_FILE) -> tuple[int, int]:
    previous = read_state(path)
    current = 1 - previous
    write_state(current, path)
    return previous, current


def dependent_transition(driver_path: Path, target_path: Path) -> tuple[int, int]:
    driver = read_state(driver_path)
    previous = read_state(target_path)
    current = driver ^ previous
    write_state(current, target_path)
    return previous, current


def copy_transition(
    driver_path: Path,
    target_path: Path,
    memory_path: Path = MEMORY_STATE_FILE,
) -> tuple[int, int]:
    driver = read_state(driver_path)
    previous = read_state(target_path)
    write_state(previous, memory_path)
    write_state(driver, target_path)
    return previous, driver


def memory_dependent_transition(
    target_path: Path,
    memory_path: Path = MEMORY_STATE_FILE,
) -> tuple[int, int]:
    memory = read_state(memory_path)
    previous = read_state(target_path)
    current = previous ^ memory
    write_state(current, target_path)
    return previous, current


def evaluate_criterion(
    first_path: Path,
    second_path: Path,
    memory_path: Path = MEMORY_STATE_FILE,
) -> tuple[bool, int]:
    mismatch = read_state(first_path) ^ read_state(second_path)
    write_state(mismatch, memory_path)
    return mismatch == 0, mismatch


def plastic_transition(
    driver_path: Path,
    target_path: Path,
    memory_path: Path = MEMORY_STATE_FILE,
) -> tuple[int, int]:
    driver = read_state(driver_path)
    previous = read_state(target_path)
    selector = read_state(memory_path)
    current = driver ^ previous if selector == 0 else driver
    write_state(current, target_path)
    return previous, current


def adaptive_transition(
    driver_path: Path,
    target_path: Path,
    memory_path: Path = MEMORY_STATE_FILE,
    policy_path: Path = POLICY_STATE_FILE,
) -> tuple[int, int, int, int, int]:
    policy = read_state(policy_path)
    driver = read_state(driver_path)
    previous = read_state(target_path)
    current = driver ^ previous if policy == 0 else driver
    write_state(current, target_path)

    _, error = evaluate_criterion(driver_path, target_path, memory_path)
    updated_policy = policy if error == 0 else 1 - policy
    write_state(updated_policy, policy_path)
    return previous, current, error, policy, updated_policy


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read or change ArxMentis' persistent distinctions."
    )
    parser.add_argument(
        "action",
        choices=(
            "read",
            "read-memory",
            "evaluate",
            "toggle",
            "step",
            "copy",
            "memory-step",
            "plastic-step",
            "read-policy",
            "toggle-policy",
            "adapt",
        ),
    )
    parser.add_argument("--distinction", type=int, choices=(1, 2), default=1)
    parser.add_argument("--state-file", type=Path)
    parser.add_argument("--memory-file", type=Path)
    parser.add_argument("--policy-file", type=Path)
    args = parser.parse_args()
    target_path = args.state_file or DISTINCTION_STATE_FILES[args.distinction]
    policy_path = args.policy_file or POLICY_STATE_FILE

    if args.action == "read":
        print(read_state(target_path))
    elif args.action == "read-memory":
        print(read_state(args.memory_file or MEMORY_STATE_FILE))
    elif args.action == "read-policy":
        print(read_state(policy_path))
    elif args.action == "toggle-policy":
        previous, current = toggle_state(policy_path)
        print(f"{previous} -> {current}")
    elif args.action == "evaluate":
        satisfied, mismatch = evaluate_criterion(
            DISTINCTION_STATE_FILES[1],
            DISTINCTION_STATE_FILES[2],
            args.memory_file or MEMORY_STATE_FILE,
        )
        result = "satisfied" if satisfied else "not satisfied"
        print(f"criterion {result}; M={mismatch}")
    elif args.action == "toggle":
        previous, current = toggle_state(target_path)
        print(f"{previous} -> {current}")
    elif args.action == "step":
        driver_distinction = 3 - args.distinction
        driver_path = DISTINCTION_STATE_FILES[driver_distinction]
        previous, current = dependent_transition(driver_path, target_path)
        print(f"D{args.distinction}: {previous} -> {current}")
    elif args.action == "memory-step":
        previous, current = memory_dependent_transition(
            target_path,
            args.memory_file or MEMORY_STATE_FILE,
        )
        print(f"D{args.distinction}: {previous} -> {current}")
    elif args.action == "plastic-step":
        driver_distinction = 3 - args.distinction
        driver_path = DISTINCTION_STATE_FILES[driver_distinction]
        previous, current = plastic_transition(
            driver_path,
            target_path,
            args.memory_file or MEMORY_STATE_FILE,
        )
        print(f"D{args.distinction}: {previous} -> {current}")
    elif args.action == "adapt":
        driver_distinction = 3 - args.distinction
        driver_path = DISTINCTION_STATE_FILES[driver_distinction]
        previous, current, error, policy, updated_policy = adaptive_transition(
            driver_path,
            target_path,
            args.memory_file or MEMORY_STATE_FILE,
            policy_path,
        )
        result = "satisfied" if error == 0 else "not satisfied"
        print(
            f"D{args.distinction}: {previous} -> {current}; "
            f"criterion {result}; P={policy} -> {updated_policy}"
        )
    else:
        driver_distinction = 3 - args.distinction
        driver_path = DISTINCTION_STATE_FILES[driver_distinction]
        previous, current = copy_transition(
            driver_path,
            target_path,
            args.memory_file or MEMORY_STATE_FILE,
        )
        print(f"D{args.distinction}: {previous} -> {current}")


if __name__ == "__main__":
    main()
