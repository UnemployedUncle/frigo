from dataclasses import asdict
from typing import Any, Dict, List, Tuple
from uuid import uuid4

from app.agents.recipe_agent import RecipeSearchAgent
from app.repositories.recipe_repository import RecipeRepository
from app.repositories.search_plan_repository import SearchPlanRepository


class RecipeService:
    def __init__(self) -> None:
        self.agent = RecipeSearchAgent()
        self.recipe_repo = RecipeRepository()
        self.plan_repo = SearchPlanRepository()

    def _recipe_ingredient_names(self, recipe: Dict[str, Any]) -> List[str]:
        names = [name.replace(" ", "").lower() for name in recipe["primary_ingredients"]]
        names.extend(item["name"].replace(" ", "").lower() for item in recipe["required_ingredients"])
        return list(dict.fromkeys(names))

    def _match_recipes(self, recipes: List[Dict[str, Any]], selected_ingredients: List[str]) -> List[Dict[str, Any]]:
        normalized_targets = [name.replace(" ", "").lower() for name in selected_ingredients]
        matches = []
        for recipe in recipes:
            names = self._recipe_ingredient_names(recipe)
            if all(target in names for target in normalized_targets):
                matches.append(recipe)
        return matches

    def _score_recipe(self, recipe: Dict[str, Any], fridge_items: List[Dict[str, Any]]) -> int:
        fridge_map = {item["normalized_name"]: item for item in fridge_items}
        score = 0
        for name in self._recipe_ingredient_names(recipe):
            if name in fridge_map:
                score += 10
                if fridge_map[name].get("days_left") is not None and fridge_map[name]["days_left"] <= 3:
                    score += 20
        return score

    def recommend(self, fridge_items: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        recipes = self.recipe_repo.list_recipes()
        if not fridge_items:
            return [], []

        counts_to_try = [5]
        plan_steps: List[Dict[str, Any]] = []
        matched_recipes: List[Dict[str, Any]] = []
        attempt_no = 1

        while counts_to_try:
            count = counts_to_try.pop(0)
            if len(fridge_items) < count:
                continue

            selection = self.agent.build_selection(fridge_items, count)
            matches = self._match_recipes(recipes, selection.selected_ingredients)

            next_step = None
            if count == 5 and len(matches) >= 10 and len(fridge_items) >= 6:
                counts_to_try.insert(0, 6)
                next_step = "결과가 많아 6개 조합으로 재검색"
            elif len(matches) == 0 and count == 5:
                counts_to_try.append(4)
                next_step = "결과가 없어 4개 조합으로 fallback"
            elif len(matches) == 0 and count == 4:
                counts_to_try.append(3)
                next_step = "결과가 없어 3개 조합으로 fallback"

            step = {
                "id": str(uuid4()),
                "attempt_no": attempt_no,
                "selected_ingredients": selection.selected_ingredients,
                "query_text": selection.query_text,
                "reason": selection.reason,
                "result_count": len(matches),
                "next_step": next_step,
            }
            self.plan_repo.insert_plan_step(step)
            plan_steps.append(step)
            attempt_no += 1

            if matches and count == 5 and len(matches) >= 10 and len(fridge_items) >= 6:
                continue
            if matches:
                matched_recipes = matches
                break

        ranked = sorted(matched_recipes, key=lambda recipe: self._score_recipe(recipe, fridge_items), reverse=True)
        return plan_steps, ranked[:5]
