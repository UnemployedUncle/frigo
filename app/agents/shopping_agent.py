from collections import defaultdict
from typing import Dict, List, TypedDict

from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, StateGraph

from app.openrouter import structured_client
from app.schemas import ShoppingItemAgentModel, ShoppingListAgentResponse


class ShoppingState(TypedDict, total=False):
    recipe: dict
    fridge_items: List[dict]
    items: List[Dict]


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
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You compare recipe ingredients and fridge inventory and return a shopping list JSON that matches the schema.",
                ),
                ("human", "Recipe: {recipe}\nFridge items: {fridge_items}"),
            ]
        )
        graph = StateGraph(ShoppingState)
        graph.add_node("build", self._build_node)
        graph.set_entry_point("build")
        graph.add_edge("build", END)
        self.graph = graph.compile()

    def _build_node(self, state: ShoppingState) -> ShoppingState:
        recipe = state["recipe"]
        fridge_items = state["fridge_items"]
        if structured_client.enabled:
            prompt_value = self.prompt.invoke({"recipe": recipe, "fridge_items": fridge_items})
            response = structured_client.generate(
                schema_name="shopping_agent_response",
                response_model=ShoppingListAgentResponse,
                system_prompt=prompt_value.messages[0].content,
                user_prompt=prompt_value.messages[1].content,
            )
            if response is not None:
                return {"items": [item.model_dump() for item in response.items]}
        fallback = _fallback_shopping(recipe, fridge_items)
        return {"items": [item.model_dump() for item in fallback.items]}

    def build(self, recipe: dict, fridge_items: List[dict]) -> ShoppingListAgentResponse:
        result = self.graph.invoke({"recipe": recipe, "fridge_items": fridge_items})
        return ShoppingListAgentResponse(items=[ShoppingItemAgentModel(**item) for item in result["items"]])
