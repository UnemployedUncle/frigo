from typing import Any, Dict, List, Optional

from app.db import get_connection


class RecipeRepository:
    def list_recipes(self) -> List[Dict[str, Any]]:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM recipes ORDER BY title")
            return cur.fetchall()

    def get_recipe(self, recipe_id: str) -> Optional[Dict[str, Any]]:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM recipes WHERE id = %s", (recipe_id,))
            return cur.fetchone()
