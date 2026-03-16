from typing import Any, Dict, List
from uuid import uuid4

from app.agents.shopping_agent import ShoppingAgent
from app.repositories.recipe_repository import RecipeRepository
from app.repositories.shopping_repository import ShoppingRepository


class ShoppingService:
    def __init__(self) -> None:
        self.agent = ShoppingAgent()
        self.recipe_repo = RecipeRepository()
        self.repo = ShoppingRepository()

    def build_for_recipe(self, recipe_id: str, fridge_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        recipe = self.recipe_repo.get_recipe(recipe_id)
        if recipe is None:
            raise ValueError(f"Recipe not found: {recipe_id}")

        response = self.agent.build(recipe, fridge_items)
        payload = {
            "id": str(uuid4()),
            "recipe_id": recipe_id,
            "shopping_items": [item.model_dump() for item in response.items],
        }
        self.repo.insert_run(payload)
        return payload
