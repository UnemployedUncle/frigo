import json
from pathlib import Path
from typing import Any, Dict, List

from app.agents.workflow_agent import WorkflowAgent
from app.repositories.recipe_repository import RecipeRepository


class WorkflowService:
    def __init__(self) -> None:
        self.recipe_repo = RecipeRepository()
        self.agent = WorkflowAgent()

    def get_workflow(self, recipe_id: str) -> Dict[str, Any]:
        recipe = self.recipe_repo.get_recipe(recipe_id)
        if recipe is None:
            raise ValueError(f"Recipe not found: {recipe_id}")
        workflow_file = Path(recipe["workflow_file"])
        lines = [json.loads(line) for line in workflow_file.read_text().splitlines() if line.strip()]
        validated_steps = self.agent.build(lines)
        return {"recipe": recipe, "steps": validated_steps}
