from collections import defaultdict
from typing import List

from app.openrouter import structured_client
from app.schemas import ShoppingItemAgentModel, ShoppingListAgentResponse


def _fallback_shopping(recipe: dict, fridge_items: List[dict]) -> ShoppingListAgentResponse:
    fridge_map = defaultdict(list)
    for item in fridge_items:
        fridge_map[item["normalized_name"]].append(item)

    shopping_items: List[ShoppingItemAgentModel] = []
    for ingredient in recipe["required_ingredients"]:
        name = ingredient["name"]
        normalized = name.replace(" ", "").lower()
        current_quantity = None
        unit = ingredient.get("unit")
        reason = "missing"
        must_buy = True
        current_matches = fridge_map.get(normalized, [])
        if current_matches:
            current_quantity = sum((match.get("quantity") or 0) for match in current_matches)
            if ingredient.get("quantity") is not None and current_quantity > 0:
                if current_quantity <= ingredient["quantity"] / 2:
                    reason = "half_or_less"
                    must_buy = True
                elif current_quantity < ingredient["quantity"]:
                    reason = "insufficient"
                    must_buy = True
                else:
                    continue
            else:
                reason = "insufficient"
        shopping_items.append(
            ShoppingItemAgentModel(
                name=name,
                required_quantity=ingredient.get("quantity"),
                current_quantity=current_quantity,
                unit=unit,
                reason=reason,
                must_buy=must_buy,
            )
        )
    return ShoppingListAgentResponse(items=shopping_items)


class ShoppingAgent:
    def __init__(self) -> None:
        self.system_prompt = (
            "You compare recipe ingredients and fridge inventory and return a shopping list JSON that matches the schema."
        )

    def build(
        self,
        recipe: dict,
        fridge_items: List[dict],
        *,
        force_fallback: bool = False,
    ) -> ShoppingListAgentResponse:
        if force_fallback:
            return _fallback_shopping(recipe, fridge_items)
        if structured_client.enabled:
            response = structured_client.generate(
                schema_name="shopping_agent_response",
                response_model=ShoppingListAgentResponse,
                system_prompt=self.system_prompt,
                user_prompt=f"Recipe: {recipe}\nFridge items: {fridge_items}",
            )
            if response is not None:
                return response
        return _fallback_shopping(recipe, fridge_items)
