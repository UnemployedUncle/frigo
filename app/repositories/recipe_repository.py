from typing import Any, Dict, List, Optional

from app.db import get_connection


class RecipeRepository:
    def list_random_recipes(self, limit: int) -> List[Dict[str, Any]]:
        if limit <= 0:
            return []

        collected: Dict[str, Dict[str, Any]] = {}
        sample_percents = [0.5, 2.0, 10.0, 100.0]

        with get_connection() as conn, conn.cursor() as cur:
            for percent in sample_percents:
                remaining = limit - len(collected)
                if remaining <= 0:
                    break
                cur.execute(
                    """
                    SELECT *
                    FROM recipes TABLESAMPLE SYSTEM (%s)
                    LIMIT %s
                    """,
                    (percent, remaining * 4),
                )
                for row in cur.fetchall():
                    collected.setdefault(row["id"], row)
                    if len(collected) >= limit:
                        break

            remaining = limit - len(collected)
            if remaining > 0:
                excluded_ids = list(collected.keys())
                if excluded_ids:
                    cur.execute(
                        """
                        SELECT *
                        FROM recipes
                        WHERE NOT (id = ANY(%s))
                        ORDER BY id
                        LIMIT %s
                        """,
                        (excluded_ids, remaining),
                    )
                else:
                    cur.execute(
                        """
                        SELECT *
                        FROM recipes
                        ORDER BY id
                        LIMIT %s
                        """,
                        (remaining,),
                    )
                for row in cur.fetchall():
                    collected.setdefault(row["id"], row)
                    if len(collected) >= limit:
                        break

        return list(collected.values())[:limit]

    def search_candidate_recipe_ids(self, terms: List[str], min_overlap: int, limit: int) -> List[Dict[str, Any]]:
        if not terms:
            return []
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT recipe_id AS id, COUNT(DISTINCT term) AS overlap_count
                FROM recipe_search_terms
                WHERE term = ANY(%s)
                GROUP BY recipe_id
                HAVING COUNT(DISTINCT term) >= %s
                ORDER BY overlap_count DESC, recipe_id ASC
                LIMIT %s
                """,
                (terms, min_overlap, limit),
            )
            return cur.fetchall()

    def get_recipes_by_ids(self, recipe_ids: List[str]) -> List[Dict[str, Any]]:
        if not recipe_ids:
            return []
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM recipes WHERE id = ANY(%s)", (recipe_ids,))
            rows = cur.fetchall()
        rows_by_id = {row["id"]: row for row in rows}
        return [rows_by_id[recipe_id] for recipe_id in recipe_ids if recipe_id in rows_by_id]

    def get_recipe(self, recipe_id: str) -> Optional[Dict[str, Any]]:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM recipes WHERE id = %s", (recipe_id,))
            return cur.fetchone()
