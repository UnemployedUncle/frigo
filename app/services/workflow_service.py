from typing import Any, Dict, List

from app.repositories.recipe_repository import RecipeRepository
from app.repositories.workflow_repository import WorkflowRepository


class WorkflowService:
    def __init__(self) -> None:
        self.recipe_repo = RecipeRepository()
        self.workflow_repo = WorkflowRepository()

    def get_workflow(self, recipe_id: str) -> Dict[str, Any]:
        recipe = self.recipe_repo.get_recipe(recipe_id)
        if recipe is None:
            raise ValueError(f"Recipe not found: {recipe_id}")
        lines = self.workflow_repo.list_steps(recipe_id)
        if not lines:
            raise ValueError(f"Workflow not found: {recipe_id}")
        for line in lines:
            if "estimated_seconds" not in line:
                line["estimated_seconds"] = max(1, min(10, int(line.get("estimated_minutes", 5))))
        validated_steps = sorted(lines, key=lambda step: step["step_number"])
        return {"recipe": recipe, "steps": validated_steps}
