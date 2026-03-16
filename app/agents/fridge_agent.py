import re
from datetime import date, timedelta
from typing import Dict, List, Optional, TypedDict

from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, StateGraph

from app.openrouter import structured_client
from app.schemas import FridgeParseResponse, FridgeParsedItem


class FridgeState(TypedDict, total=False):
    raw_text: str
    items: List[Dict]


DATE_PATTERNS = [
    (re.compile(r"오늘"), lambda today: today),
    (re.compile(r"내일"), lambda today: today + timedelta(days=1)),
    (re.compile(r"모레"), lambda today: today + timedelta(days=2)),
]
QUANTITY_RE = re.compile(r"(?P<qty>\d+(?:\.\d+)?)\s*(?P<unit>kg|g|ml|l|개|봉지|모|대|공기|큰술|작은술|쪽|줄기|팩)?")
MONTH_DAY_RE = re.compile(r"(?P<month>\d{1,2})월\s*(?P<day>\d{1,2})일")


def _normalize_name(value: str) -> str:
    return re.sub(r"\s+", "", value.strip().lower())


def _parse_date(chunk: str) -> Optional[date]:
    today = date.today()
    for pattern, resolver in DATE_PATTERNS:
        if pattern.search(chunk):
            return resolver(today)
    month_day = MONTH_DAY_RE.search(chunk)
    if month_day:
        parsed = date(today.year, int(month_day.group("month")), int(month_day.group("day")))
        if parsed < today:
            return date(today.year + 1, int(month_day.group("month")), int(month_day.group("day")))
        return parsed
    return None


def _fallback_parse(raw_text: str) -> FridgeParseResponse:
    items: List[FridgeParsedItem] = []
    for raw_chunk in [chunk.strip() for chunk in raw_text.split(",") if chunk.strip()]:
        expiry_date = _parse_date(raw_chunk)
        quantity = None
        unit = None
        quantity_match = QUANTITY_RE.search(raw_chunk)
        if quantity_match:
            quantity = float(quantity_match.group("qty"))
            unit = quantity_match.group("unit")

        cleaned = raw_chunk
        if quantity_match:
            cleaned = cleaned.replace(quantity_match.group(0), "")
        for token in ["오늘", "내일", "모레", "까지"]:
            cleaned = cleaned.replace(token, "")
        cleaned = MONTH_DAY_RE.sub("", cleaned)
        name = cleaned.strip()
        if not name:
            continue
        items.append(
            FridgeParsedItem(
                name=name,
                normalized_name=_normalize_name(name),
                quantity=quantity,
                unit=unit,
                expiry_date=expiry_date,
            )
        )
    return FridgeParseResponse(items=items)


class FridgeAgent:
    def __init__(self) -> None:
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You parse Korean grocery text into structured fridge items. Return only JSON that matches the schema.",
                ),
                ("human", "{raw_text}"),
            ]
        )
        graph = StateGraph(FridgeState)
        graph.add_node("parse", self._parse_node)
        graph.set_entry_point("parse")
        graph.add_edge("parse", END)
        self.graph = graph.compile()

    def _parse_node(self, state: FridgeState) -> FridgeState:
        raw_text = state["raw_text"]
        if structured_client.enabled:
            prompt_value = self.prompt.invoke({"raw_text": raw_text})
            response = structured_client.generate(
                schema_name="fridge_parse_response",
                response_model=FridgeParseResponse,
                system_prompt=prompt_value.messages[0].content,
                user_prompt=prompt_value.messages[1].content,
            )
            if response is not None:
                return {"items": [item.model_dump() for item in response.items]}
        fallback = _fallback_parse(raw_text)
        return {"items": [item.model_dump() for item in fallback.items]}

    def parse(self, raw_text: str) -> FridgeParseResponse:
        result = self.graph.invoke({"raw_text": raw_text})
        return FridgeParseResponse(items=[FridgeParsedItem(**item) for item in result["items"]])
