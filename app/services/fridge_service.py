import json
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.agents.fridge_agent import FridgeAgent
from app.repositories.fridge_repository import FridgeRepository


@dataclass
class ParseResult:
    source_text_id: str
    items: List[Dict[str, Any]]


class FridgeService:
    def __init__(self) -> None:
        self.agent = FridgeAgent()
        self.repo = FridgeRepository()

    def _days_left(self, expiry_date: Optional[date]) -> Optional[int]:
        if expiry_date is None:
            return None
        return (expiry_date - date.today()).days

    def parse_and_store(self, raw_text: str) -> ParseResult:
        parsed = self.agent.parse(raw_text)
        source_text_id = str(uuid4())
        parsed_items: List[Dict[str, Any]] = []
        for item in parsed.items:
            parsed_items.append(
                {
                    "id": str(uuid4()),
                    "name": item.name,
                    "normalized_name": item.normalized_name,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "expiry_date": item.expiry_date,
                    "days_left": self._days_left(item.expiry_date),
                    "source_text_id": source_text_id,
                }
            )
        self.repo.insert_input_log(source_text_id, raw_text, json.dumps({"items": [item.model_dump(mode="json") for item in parsed.items]}))
        if parsed_items:
            self.repo.insert_items(parsed_items)
        return ParseResult(source_text_id=source_text_id, items=parsed_items)

    def list_items(self) -> List[Dict[str, Any]]:
        return self.repo.list_items()

    def load_selected_items(self, item_ids: List[str]) -> List[Dict[str, Any]]:
        fridge_items = self.list_items()
        if not fridge_items:
            raise ValueError("냉장고에 저장된 재료가 없습니다.")

        if len(fridge_items) < 5:
            return fridge_items

        unique_ids = list(dict.fromkeys(item_ids))
        if len(unique_ids) != 5:
            raise ValueError("재료를 정확히 5개 선택해주세요.")

        by_id = {item["id"]: item for item in fridge_items}
        selected_items = [by_id[item_id] for item_id in unique_ids if item_id in by_id]
        if len(selected_items) != 5:
            raise ValueError("선택한 재료를 다시 확인해주세요.")
        return selected_items

    def update_item(self, item_id: str, payload: Dict[str, Any]) -> None:
        expiry_date = payload.get("expiry_date")
        payload["normalized_name"] = payload["name"].replace(" ", "").lower()
        payload["days_left"] = self._days_left(expiry_date)
        self.repo.update_item(item_id, payload)

    def delete_item(self, item_id: str) -> None:
        self.repo.delete_item(item_id)
