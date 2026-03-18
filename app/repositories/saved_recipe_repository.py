from typing import Dict, Iterable, List, Set

from app.db import get_connection


class SavedRecipeRepository:
    def count_all(self) -> int:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT COUNT(*)::int AS saved_count FROM saved_recipes")
            row = cur.fetchone()
            return row["saved_count"] if row else 0

    def is_saved(self, recipe_id: str) -> bool:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1 FROM saved_recipes WHERE recipe_id = %s", (recipe_id,))
            return cur.fetchone() is not None

    def list_saved_ids(self, recipe_ids: Iterable[str]) -> Set[str]:
        ids = list(dict.fromkeys(recipe_ids))
        if not ids:
            return set()
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT recipe_id FROM saved_recipes WHERE recipe_id = ANY(%s)",
                (ids,),
            )
            return {row["recipe_id"] for row in cur.fetchall()}

    def save(self, recipe_id: str) -> None:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO saved_recipes (recipe_id)
                VALUES (%s)
                ON CONFLICT (recipe_id)
                DO UPDATE SET saved_at = NOW()
                """,
                (recipe_id,),
            )
            conn.commit()

    def unsave(self, recipe_id: str) -> None:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM saved_recipes WHERE recipe_id = %s", (recipe_id,))
            conn.commit()
