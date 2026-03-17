import json
import sys
from pathlib import Path


REQUIRED_FIELDS = {"recipe_id", "step_number", "title", "description", "ingredients", "tool", "estimated_seconds"}


def validate_legacy_file(path: Path) -> None:
    steps = []
    for raw in path.read_text().splitlines():
        if not raw.strip():
            continue
        row = json.loads(raw)
        missing = REQUIRED_FIELDS - row.keys()
        if missing:
            raise ValueError(f"{path.name}: missing fields {sorted(missing)}")
        if not 1 <= int(row["estimated_seconds"]) <= 10:
            raise ValueError(f"{path.name}: estimated_seconds must be between 1 and 10")
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
        validate_legacy_file(file)
    return len(files)


def validate_workflow_steps_file(path: Path) -> int:
    if not path.exists():
        raise FileNotFoundError(f"Workflow steps file not found: {path}")
    recipe_count = 0
    current_recipe_id = None
    last_step_number = 0
    with path.open(encoding="utf-8") as handle:
        for raw in handle:
            if not raw.strip():
                continue
            row = json.loads(raw)
            missing = REQUIRED_FIELDS - row.keys()
            if missing:
                raise ValueError(f"{path.name}: missing fields {sorted(missing)}")
            if not 1 <= int(row["estimated_seconds"]) <= 10:
                raise ValueError(f"{path.name}: estimated_seconds must be between 1 and 10")
            recipe_id = row["recipe_id"]
            step_number = int(row["step_number"])
            if recipe_id != current_recipe_id:
                recipe_count += 1
                current_recipe_id = recipe_id
                last_step_number = 0
                if step_number != 1:
                    raise ValueError(f"{path.name}: first step_number for {recipe_id} must be 1")
            if step_number <= last_step_number:
                raise ValueError(f"{path.name}: step_number must increase for {recipe_id}")
            last_step_number = step_number
    if recipe_count == 0:
        raise ValueError(f"{path.name}: no workflow rows found")
    return recipe_count


def main() -> None:
    if len(sys.argv) > 1:
        workflow_path = Path(sys.argv[1]).resolve()
    else:
        base_dir = Path(__file__).resolve().parents[1] / "data"
        workflow_path = base_dir / "workflow_steps.jsonl"
    if workflow_path.is_dir():
        count = validate_directory(workflow_path)
        print(f"Validated {count} workflow file(s).")
    else:
        count = validate_workflow_steps_file(workflow_path)
        print(f"Validated workflows for {count} recipe(s).")


if __name__ == "__main__":
    main()
