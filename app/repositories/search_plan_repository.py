import json
from typing import Any, Dict

from app.db import get_connection


class SearchPlanRepository:
    def insert_plan_step(self, payload: Dict[str, Any]) -> None:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO recipe_search_plans (
                    id, attempt_no, selected_ingredients, query_text,
                    reason, result_count, next_step
                ) VALUES (%s, %s, %s::jsonb, %s, %s, %s, %s)
                """,
                (
                    payload["id"],
                    payload["attempt_no"],
                    json.dumps(payload["selected_ingredients"]),
                    payload["query_text"],
                    payload["reason"],
                    payload["result_count"],
                    payload["next_step"],
                ),
            )
            conn.commit()
