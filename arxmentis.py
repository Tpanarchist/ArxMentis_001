from __future__ import annotations

import argparse
from pathlib import Path

STATE_FILE = Path(__file__).resolve().parent / ".arxmentis-state"
SECOND_STATE_FILE = Path(__file__).resolve().parent / ".arxmentis-state-2"
MEMORY_STATE_FILE = Path(__file__).resolve().parent / ".arxmentis-memory"
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


def plastic_transition(
    driver_path: Path,
    target_path: Path,
    memory_path: Path = MEMORY_STATE_FILE,
) -> tuple[int, int]:
    if read_state(memory_path) == 0:
        return dependent_transition(driver_path, target_path)
    return copy_transition(driver_path, target_path, memory_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read or change ArxMentis' persistent distinctions."
    )
    parser.add_argument(
        "action",
        choices=(
            "read",
            "read-memory",
            "toggle",
            "step",
            "copy",
            "memory-step",
            "plastic-step",
        ),
    )
    parser.add_argument("--distinction", type=int, choices=(1, 2), default=1)
    parser.add_argument("--state-file", type=Path)
    parser.add_argument("--memory-file", type=Path)
    args = parser.parse_args()
    target_path = args.state_file or DISTINCTION_STATE_FILES[args.distinction]

    if args.action == "read":
        print(read_state(target_path))
    elif args.action == "read-memory":
        print(read_state(args.memory_file or MEMORY_STATE_FILE))
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
