from typing import Any, Dict, List, Tuple
from uuid import uuid4

from app.agents.recipe_agent import RecipeSearchAgent
from app.repositories.recipe_repository import RecipeRepository
from app.repositories.search_plan_repository import SearchPlanRepository


class RecipeService:
    CANDIDATE_LIMIT = 500

    def __init__(self) -> None:
        self.agent = RecipeSearchAgent()
        self.recipe_repo = RecipeRepository()
        self.plan_repo = SearchPlanRepository()

    def _normalize_names(self, values: List[str]) -> List[str]:
        return list(dict.fromkeys(value.replace(" ", "").lower() for value in values if value))

    def _match_recipes(
        self,
        selected_ingredients: List[str],
        min_overlap: int,
    ) -> List[Tuple[str, int]]:
        normalized_targets = self._normalize_names(selected_ingredients)
        rows = self.recipe_repo.search_candidate_recipe_ids(normalized_targets, min_overlap, self.CANDIDATE_LIMIT)
        return [(row["id"], row["overlap_count"]) for row in rows]

    def _urgent_bonus(self, recipe: Dict[str, Any], fridge_items: List[Dict[str, Any]]) -> int:
        keyword_names = set(self._normalize_names(recipe["search_keywords"]))
        bonus = 0
        for item in fridge_items:
            if item["normalized_name"] in keyword_names and item.get("days_left") is not None and item["days_left"] <= 3:
                bonus += 20
        return bonus

    def _score_recipe(self, recipe: Dict[str, Any], fridge_items: List[Dict[str, Any]], overlap_count: int) -> int:
        return (overlap_count * 100) + self._urgent_bonus(recipe, fridge_items)

    def _candidate_counts(self, fridge_item_count: int) -> List[int]:
        counts = [count for count in [5, 4, 3] if fridge_item_count >= count]
        if counts:
            return counts
        if fridge_item_count > 0:
            return [fridge_item_count]
        return []

    def recommend(
        self,
        fridge_items: List[Dict[str, Any]],
        *,
        limit: int = 5,
        force_fallback: bool = False,
        minimum_overlap: int | None = None,
        persist_plan: bool = True,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        if not fridge_items:
            return [], []

        counts_to_try = self._candidate_counts(len(fridge_items))
        plan_steps: List[Dict[str, Any]] = []
        matched_recipes: List[Tuple[str, int]] = []
        best_matches: List[Tuple[str, int]] = []
        attempt_no = 1

        while counts_to_try:
            count = counts_to_try.pop(0)
            selection = self.agent.build_selection(fridge_items, count, force_fallback=force_fallback)
            min_overlap = minimum_overlap if minimum_overlap is not None else (1 if len(fridge_items) == 1 else 2)
            matches = self._match_recipes(selection.selected_ingredients, min_overlap)

            next_step = None
            if count == 5 and len(matches) >= 10 and len(fridge_items) >= 6:
                counts_to_try.insert(0, 6)
                next_step = "결과가 많아 6개 조합으로 재검색"
            elif len(matches) == 0 and counts_to_try:
                next_step = f"결과가 없어 {counts_to_try[0]}개 조합으로 fallback"

            step = {
                "id": str(uuid4()),
                "attempt_no": attempt_no,
                "selected_ingredients": selection.selected_ingredients,
                "query_text": selection.query_text,
                "reason": selection.reason,
                "result_count": len(matches),
                "next_step": next_step,
            }
            if persist_plan:
                self.plan_repo.insert_plan_step(step)
            plan_steps.append(step)
            attempt_no += 1

            if matches:
                best_matches = matches
            if matches and count == 5 and len(matches) >= 10 and len(fridge_items) >= 6:
                continue
            if matches:
                matched_recipes = matches
                break

        if not matched_recipes:
            matched_recipes = best_matches

        candidate_ids = [recipe_id for recipe_id, _ in matched_recipes]
        recipes = self.recipe_repo.get_recipes_by_ids(candidate_ids)
        recipes_by_id = {recipe["id"]: recipe for recipe in recipes}
        ranked = sorted(
            [item for item in matched_recipes if item[0] in recipes_by_id],
            key=lambda item: self._score_recipe(recipes_by_id[item[0]], fridge_items, item[1]),
            reverse=True,
        )
        return plan_steps, [recipes_by_id[recipe_id] for recipe_id, _ in ranked[:limit]]
