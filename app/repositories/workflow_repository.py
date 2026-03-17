from typing import Any, Dict, List

from app.db import get_connection


class WorkflowRepository:
    def list_steps(self, recipe_id: str) -> List[Dict[str, Any]]:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT recipe_id, step_number, title, description, ingredients, tool, estimated_seconds, estimated_minutes
                FROM workflow_steps
                WHERE recipe_id = %s
                ORDER BY step_number
                """,
                (recipe_id,),
            )
            return cur.fetchall()
