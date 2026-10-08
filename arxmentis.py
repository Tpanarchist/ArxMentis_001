from __future__ import annotations

import argparse
from pathlib import Path

STATE_FILE = Path(__file__).resolve().parent / ".arxmentis-state"


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Read or change ArxMentis' persistent bit.")
    parser.add_argument("action", choices=("read", "toggle"))
    parser.add_argument("--state-file", type=Path, default=STATE_FILE)
    args = parser.parse_args()

    if args.action == "read":
        print(read_state(args.state_file))
    else:
        previous, current = toggle_state(args.state_file)
        print(f"{previous} -> {current}")


if __name__ == "__main__":
    main()
