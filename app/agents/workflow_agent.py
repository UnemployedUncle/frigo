from typing import Dict, List, TypedDict

from langgraph.graph import END, StateGraph


class WorkflowState(TypedDict, total=False):
    steps: List[Dict]
    validated_steps: List[Dict]


class WorkflowAgent:
    def __init__(self) -> None:
        graph = StateGraph(WorkflowState)
        graph.add_node("validate", self._validate_node)
        graph.set_entry_point("validate")
        graph.add_edge("validate", END)
        self.graph = graph.compile()

    def _validate_node(self, state: WorkflowState) -> WorkflowState:
        validated = sorted(state["steps"], key=lambda step: step["step_number"])
        return {"validated_steps": validated}

    def build(self, steps: List[Dict]) -> List[Dict]:
        result = self.graph.invoke({"steps": steps})
        return result["validated_steps"]
