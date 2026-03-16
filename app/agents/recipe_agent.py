from typing import Dict, List, TypedDict

from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, StateGraph

from app.openrouter import structured_client
from app.schemas import RecipeSearchAgentResponse, RecipeSearchSelection


class RecipeState(TypedDict, total=False):
    fridge_items: List[dict]
    desired_count: int
    plan_steps: List[Dict]


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
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You create a recipe search plan from fridge items. Return only JSON matching the schema.",
                ),
                ("human", "Desired ingredient count: {desired_count}\nFridge items: {fridge_items}"),
            ]
        )
        graph = StateGraph(RecipeState)
        graph.add_node("select", self._select_node)
        graph.set_entry_point("select")
        graph.add_edge("select", END)
        self.graph = graph.compile()

    def _select_node(self, state: RecipeState) -> RecipeState:
        fridge_items = state["fridge_items"]
        desired_count = state["desired_count"]
        if structured_client.enabled:
            prompt_value = self.prompt.invoke({"desired_count": desired_count, "fridge_items": fridge_items})
            response = structured_client.generate(
                schema_name="recipe_search_agent_response",
                response_model=RecipeSearchAgentResponse,
                system_prompt=prompt_value.messages[0].content,
                user_prompt=prompt_value.messages[1].content,
            )
            if response is not None:
                return {"plan_steps": [step.model_dump() for step in response.plan_steps]}
        fallback = _fallback_selection(fridge_items, desired_count)
        return {"plan_steps": [step.model_dump() for step in fallback.plan_steps]}

    def build_selection(self, fridge_items: List[dict], desired_count: int) -> RecipeSearchSelection:
        result = self.graph.invoke({"fridge_items": fridge_items, "desired_count": desired_count})
        return RecipeSearchSelection(**result["plan_steps"][0])
