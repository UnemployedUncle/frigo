import json
from typing import Any, Dict

from app.db import get_connection


class ShoppingRepository:
    def insert_run(self, payload: Dict[str, Any]) -> None:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO shopping_list_runs (id, recipe_id, shopping_items)
                VALUES (%s, %s, %s::jsonb)
                """,
                (
                    payload["id"],
                    payload["recipe_id"],
                    json.dumps(payload["shopping_items"]),
                ),
            )
            conn.commit()
