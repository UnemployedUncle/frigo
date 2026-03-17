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
WEEKDAY_MAP = {"월": 0, "화": 1, "수": 2, "목": 3, "금": 4, "토": 5, "일": 6}
KOREAN_NUMBER_MAP = {
    "한": 1.0,
    "두": 2.0,
    "세": 3.0,
    "네": 4.0,
    "다섯": 5.0,
    "여섯": 6.0,
    "일곱": 7.0,
    "여덟": 8.0,
    "아홉": 9.0,
    "열": 10.0,
}
QUANTITY_RE = re.compile(
    r"(?P<qty>\d+(?:\.\d+)?)\s*(?P<unit>kg|g|ml|l|개|봉지|모|대|공기|큰술|작은술|쪽|줄기|팩|bag|bags|pack|packs|can|cans|bottle|bottles|carton|cartons)?",
    re.IGNORECASE,
)
KOREAN_QUANTITY_RE = re.compile(
    r"(?P<qty>한|두|세|네|다섯|여섯|일곱|여덟|아홉|열)\s*(?P<unit>개|봉지|모|대|공기|큰술|작은술|쪽|줄기|팩)"
)
MONTH_DAY_RE = re.compile(r"(?P<month>\d{1,2})월\s*(?P<day>\d{1,2})일")
NEXT_WEEKDAY_RE = re.compile(r"다음\s*주\s*(?P<weekday>[월화수목금토일])요일?")
THIS_WEEKEND_RE = re.compile(r"이번\s*주말")
UUID_LIKE_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)
RELATIVE_DATE_TOKEN_RE = re.compile(r"(오늘|내일|모레|이번\s*주말|다음\s*주\s*[월화수목금토일])")


def _normalize_name(value: str) -> str:
    return re.sub(r"\s+", "", value.strip().lower())


def _parse_date(chunk: str) -> Optional[date]:
    today = date.today()
    for pattern, resolver in DATE_PATTERNS:
        if pattern.search(chunk):
            return resolver(today)
    weekend_match = THIS_WEEKEND_RE.search(chunk)
    if weekend_match:
        if today.weekday() <= 5:
            return today + timedelta(days=(5 - today.weekday()))
        return today
    next_weekday = NEXT_WEEKDAY_RE.search(chunk)
    if next_weekday:
        target_weekday = WEEKDAY_MAP[next_weekday.group("weekday")]
        days_until = (target_weekday - today.weekday()) % 7
        return today + timedelta(days=days_until + 7)
    month_day = MONTH_DAY_RE.search(chunk)
    if month_day:
        parsed = date(today.year, int(month_day.group("month")), int(month_day.group("day")))
        if parsed < today:
            return date(today.year + 1, int(month_day.group("month")), int(month_day.group("day")))
        return parsed
    return None


def _strip_date_tokens(value: str) -> str:
    stripped = value
    for token in ["오늘", "내일", "모레", "까지"]:
        stripped = stripped.replace(token, "")
    stripped = THIS_WEEKEND_RE.sub("", stripped)
    stripped = NEXT_WEEKDAY_RE.sub("", stripped)
    stripped = MONTH_DAY_RE.sub("", stripped)
    return stripped


def _parse_quantity(chunk: str) -> tuple[Optional[float], Optional[str], Optional[str]]:
    korean_match = KOREAN_QUANTITY_RE.search(chunk)
    if korean_match:
        return (
            KOREAN_NUMBER_MAP[korean_match.group("qty")],
            korean_match.group("unit"),
            korean_match.group(0),
        )

    numeric_match = QUANTITY_RE.search(chunk)
    if numeric_match:
        unit = numeric_match.group("unit")
        return float(numeric_match.group("qty")), unit, numeric_match.group(0)
    return None, None, None


def _clean_name(chunk: str, matched_quantity: Optional[str]) -> str:
    cleaned = chunk
    if matched_quantity:
        cleaned = cleaned.replace(matched_quantity, "", 1)
    cleaned = _strip_date_tokens(cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,")
    return cleaned


def _sanitize_llm_item(item: FridgeParsedItem) -> FridgeParsedItem:
    return FridgeParsedItem(
        name=item.name.strip(),
        normalized_name=_normalize_name(item.name),
        quantity=item.quantity,
        unit=item.unit,
        expiry_date=item.expiry_date,
    )


def _is_suspicious_llm_response(raw_text: str, items: List[FridgeParsedItem]) -> bool:
    if not items:
        return True
    raw_normalized = _normalize_name(raw_text)
    relative_date_requested = bool(RELATIVE_DATE_TOKEN_RE.search(raw_text))
    today = date.today()
    for item in items:
        name = item.name.strip()
        if not name or UUID_LIKE_RE.match(name):
            return True
        if item.normalized_name != _normalize_name(name):
            return True
        if len(name) >= 2 and _normalize_name(name) not in raw_normalized:
            token_parts = [part for part in re.split(r"[^a-zA-Z0-9가-힣]+", name) if part]
            if token_parts and not any(_normalize_name(part) in raw_normalized for part in token_parts):
                return True
        if relative_date_requested and item.expiry_date is not None and item.expiry_date < today:
            return True
    return False


def _fallback_parse(raw_text: str) -> FridgeParseResponse:
    items: List[FridgeParsedItem] = []
    for raw_chunk in [chunk.strip() for chunk in raw_text.split(",") if chunk.strip()]:
        expiry_date = _parse_date(raw_chunk)
        quantity, unit, matched_quantity = _parse_quantity(_strip_date_tokens(raw_chunk))
        name = _clean_name(raw_chunk, matched_quantity)
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
                sanitized_items = [_sanitize_llm_item(item) for item in response.items]
                if not _is_suspicious_llm_response(raw_text, sanitized_items):
                    return {"items": [item.model_dump() for item in sanitized_items]}
        fallback = _fallback_parse(raw_text)
        return {"items": [item.model_dump() for item in fallback.items]}

    def parse(self, raw_text: str) -> FridgeParseResponse:
        result = self.graph.invoke({"raw_text": raw_text})
        return FridgeParseResponse(items=[FridgeParsedItem(**item) for item in result["items"]])
