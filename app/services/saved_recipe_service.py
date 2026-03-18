from typing import Dict, Iterable

from app.repositories.recipe_repository import RecipeRepository
from app.repositories.saved_recipe_repository import SavedRecipeRepository


class SavedRecipeService:
    def __init__(self) -> None:
        self.recipe_repo = RecipeRepository()
        self.repo = SavedRecipeRepository()

    def count_saved(self) -> int:
        return self.repo.count_all()

    def is_saved(self, recipe_id: str) -> bool:
        return self.repo.is_saved(recipe_id)

    def saved_map(self, recipe_ids: Iterable[str]) -> Dict[str, bool]:
        ids = list(dict.fromkeys(recipe_ids))
        saved_ids = self.repo.list_saved_ids(ids)
        return {recipe_id: recipe_id in saved_ids for recipe_id in ids}

    def toggle(self, recipe_id: str) -> bool:
        recipe = self.recipe_repo.get_recipe(recipe_id)
        if recipe is None:
            raise ValueError(f"Recipe not found: {recipe_id}")
        if self.repo.is_saved(recipe_id):
            self.repo.unsave(recipe_id)
            return False
        self.repo.save(recipe_id)
        return True
