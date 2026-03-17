from typing import List

from app.openrouter import structured_client
from app.schemas import RecipeSearchAgentResponse, RecipeSearchSelection


def _fallback_selection(fridge_items: List[dict], desired_count: int) -> RecipeSearchAgentResponse:
    def sort_key(item: dict) -> tuple:
        days_left = item.get("days_left")
        quantity = item.get("quantity") or 0
        return (days_left is None, days_left if days_left is not None else 9999, -quantity, item["name"])

    selected = [item["name"] for item in sorted(fridge_items, key=sort_key)[:desired_count]]
    reason = "임박 재료와 수량이 충분한 재료를 우선 선택한 기본 검색 계획"
    return RecipeSearchAgentResponse(
        plan_steps=[
            RecipeSearchSelection(
                selected_ingredients=selected,
                query_text=" ".join(selected),
                reason=reason,
            )
        ]
    )


class RecipeSearchAgent:
    def __init__(self) -> None:
        self.system_prompt = "You create a recipe search plan from fridge items. Return only JSON matching the schema."

    def _select(self, fridge_items: List[dict], desired_count: int) -> RecipeSearchSelection:
        if structured_client.enabled:
            response = structured_client.generate(
                schema_name="recipe_search_agent_response",
                response_model=RecipeSearchAgentResponse,
                system_prompt=self.system_prompt,
                user_prompt=f"Desired ingredient count: {desired_count}\nFridge items: {fridge_items}",
            )
            if response is not None:
                return response.plan_steps[0]
        fallback = _fallback_selection(fridge_items, desired_count)
        return fallback.plan_steps[0]

    def build_selection(
        self,
        fridge_items: List[dict],
        desired_count: int,
        force_fallback: bool = False,
    ) -> RecipeSearchSelection:
        if force_fallback:
            fallback = _fallback_selection(fridge_items, desired_count)
            return fallback.plan_steps[0]
        return self._select(fridge_items, desired_count)
