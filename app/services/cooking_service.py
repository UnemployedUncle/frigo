from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List
from uuid import uuid4

from app.repositories.cooking_session_repository import CookingSessionRepository


class CookingService:
    def __init__(self) -> None:
        self.repo = CookingSessionRepository()

    def completion_grass(self, days: int = 14) -> List[Dict[str, Any]]:
        today = date.today()
        start_date = today - timedelta(days=days - 1)
        rows = self.repo.counts_by_date(start_date)
        counts = {row["completed_date"]: row["completion_count"] for row in rows}
        grass = []
        for offset in range(days):
            current_date = start_date + timedelta(days=offset)
            grass.append(
                {
                    "date": current_date,
                    "count": counts.get(current_date, 0),
                    "label": current_date.strftime("%a"),
                    "iso_date": current_date.isoformat(),
                }
            )
        return grass

    def home_summary_counts(self) -> Dict[str, int]:
        return {"completed_count": self.repo.count_all()}

    def complete_recipe(self, recipe_id: str, actual_seconds: int) -> None:
        self.repo.insert_session(
            session_id=str(uuid4()),
            recipe_id=recipe_id,
            completed_at=datetime.now(timezone.utc),
            actual_seconds=actual_seconds,
        )
