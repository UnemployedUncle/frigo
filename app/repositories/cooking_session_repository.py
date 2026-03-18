from datetime import date, datetime
from typing import Any, Dict, List

from app.db import get_connection


class CookingSessionRepository:
    def count_all(self) -> int:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT COUNT(*)::int AS completion_count FROM cooking_sessions")
            row = cur.fetchone()
            return row["completion_count"] if row else 0

    def counts_by_date(self, start_date: date) -> List[Dict[str, Any]]:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT completed_at::date AS completed_date, COUNT(*)::int AS completion_count
                FROM cooking_sessions
                WHERE completed_at::date >= %s
                GROUP BY completed_at::date
                ORDER BY completed_date
                """,
                (start_date,),
            )
            return cur.fetchall()

    def list_recent(self, limit: int) -> List[Dict[str, Any]]:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    cs.id,
                    cs.recipe_id,
                    cs.completed_at,
                    cs.actual_seconds,
                    r.title,
                    r.summary,
                    r.primary_ingredients
                FROM cooking_sessions cs
                JOIN recipes r ON r.id = cs.recipe_id
                ORDER BY cs.completed_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            return cur.fetchall()

    def insert_session(self, session_id: str, recipe_id: str, completed_at: datetime, actual_seconds: int) -> None:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO cooking_sessions (id, recipe_id, completed_at, actual_seconds)
                VALUES (%s, %s, %s, %s)
                """,
                (session_id, recipe_id, completed_at, actual_seconds),
            )
            conn.commit()
