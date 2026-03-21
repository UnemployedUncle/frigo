from datetime import date
from typing import Any, Dict, List

from app.db import get_connection


class FridgeRepository:
    def insert_input_log(self, log_id: str, raw_text: str, parsed_json: str) -> None:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO fridge_input_logs (id, raw_text, parsed_json)
                VALUES (%s, %s, %s::jsonb)
                """,
                (log_id, raw_text, parsed_json),
            )
            conn.commit()

    def insert_items(self, items: List[Dict[str, Any]]) -> None:
        with get_connection() as conn, conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO fridge_items (
                    id, name, normalized_name, quantity, unit,
                    expiry_date, days_left, source_text_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    (
                        item["id"],
                        item["name"],
                        item["normalized_name"],
                        item["quantity"],
                        item["unit"],
                        item["expiry_date"],
                        item["days_left"],
                        item["source_text_id"],
                    )
                    for item in items
                ],
            )
            conn.commit()

    def list_items(self) -> List[Dict[str, Any]]:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM fridge_items
                ORDER BY expiry_date NULLS LAST, created_at DESC
                """
            )
            return cur.fetchall()

    def update_item(self, item_id: str, payload: Dict[str, Any]) -> None:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE fridge_items
                SET name = %s,
                    normalized_name = %s,
                    quantity = %s,
                    unit = %s,
                    expiry_date = %s,
                    days_left = %s,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (
                    payload["name"],
                    payload["normalized_name"],
                    payload["quantity"],
                    payload["unit"],
                    payload["expiry_date"],
                    payload["days_left"],
                    item_id,
                ),
            )
            conn.commit()

    def delete_item(self, item_id: str) -> None:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM fridge_items WHERE id = %s", (item_id,))
            conn.commit()
