import json
import sys
from pathlib import Path


REQUIRED_FIELDS = {"recipe_id", "step_number", "title", "description", "ingredients", "tool", "estimated_minutes"}


def validate_file(path: Path) -> None:
    steps = []
    for raw in path.read_text().splitlines():
        if not raw.strip():
            continue
        row = json.loads(raw)
        missing = REQUIRED_FIELDS - row.keys()
        if missing:
            raise ValueError(f"{path.name}: missing fields {sorted(missing)}")
        steps.append(row["step_number"])
    if steps != sorted(steps):
        raise ValueError(f"{path.name}: step_number must be sorted")
    if steps and steps[0] != 1:
        raise ValueError(f"{path.name}: first step_number must be 1")


def validate_directory(directory: Path) -> int:
    if not directory.exists():
        raise FileNotFoundError(f"Workflow directory not found: {directory}")
    files = sorted(directory.glob("*.jsonl"))
    if not files:
        raise FileNotFoundError(f"No workflow files found in: {directory}")
    for file in files:
        validate_file(file)
    return len(files)


def main() -> None:
    if len(sys.argv) > 1:
        workflow_dir = Path(sys.argv[1]).resolve()
    else:
        workflow_dir = Path(__file__).resolve().parents[1] / "data" / "workflows"
    count = validate_directory(workflow_dir)
    print(f"Validated {count} workflow file(s).")


if __name__ == "__main__":
    main()
