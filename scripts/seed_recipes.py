import json
import random
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from psycopg import connect

from app.config import settings


def normalize_terms(values):
    return list(dict.fromkeys(value.replace(" ", "").lower() for value in values if value))


def strip_nul_bytes(value):
    if isinstance(value, str):
        return value.replace("\x00", "")
    if isinstance(value, list):
        return [strip_nul_bytes(item) for item in value]
    if isinstance(value, dict):
        return {key: strip_nul_bytes(item) for key, item in value.items()}
    return value


def iter_jsonl(path: Path):
    with path.open(encoding="utf-8") as handle:
        for raw in handle:
            if raw.strip():
                yield strip_nul_bytes(json.loads(raw))


def build_demo_fridge_items(today: date):
    demo_items = [
        {"name": "chicken", "quantity": 1.0, "unit": "pack", "days_left": 2},
        {"name": "broccoli", "quantity": 1.0, "unit": "bag", "days_left": 1},
        {"name": "onion", "quantity": 1.0, "unit": None, "days_left": 3},
        {"name": "egg", "quantity": 2.0, "unit": None, "days_left": 2},
        {"name": "chicken broth", "quantity": 1.0, "unit": "can", "days_left": 6},
        {"name": "sour cream", "quantity": 1.0, "unit": "carton", "days_left": 7},
        {"name": "soy sauce", "quantity": 1.0, "unit": "bottle", "days_left": 90},
        {"name": "garlic", "quantity": 1.0, "unit": "bulb", "days_left": 20},
        {"name": "shrimp", "quantity": 1.0, "unit": "bag", "days_left": 2},
    ]
    rows = []
    for item in demo_items:
        expiry_date = today + timedelta(days=item["days_left"])
        rows.append(
            {
                "id": str(uuid4()),
                "name": item["name"],
                "normalized_name": item["name"].replace(" ", "").lower(),
                "quantity": item["quantity"],
                "unit": item["unit"],
                "expiry_date": expiry_date,
                "days_left": item["days_left"],
            }
        )
    return rows


def build_demo_sessions(sampled_rows):
    today = date.today()
    sessions = []
    day_offsets = [1, 3, 5, 6]
    for recipe, offset in zip(sampled_rows, day_offsets):
        completed_at = datetime.combine(today - timedelta(days=offset), time(hour=19 - offset % 3), tzinfo=timezone.utc)
        sessions.append(
            {
                "id": str(uuid4()),
                "recipe_id": recipe["id"],
                "completed_at": completed_at,
                "actual_seconds": 20 + (offset * 3),
            }
        )
    sessions.sort(key=lambda row: row["completed_at"], reverse=True)
    return sessions


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1] / "data"
    recipes_path = base_dir / "recipes.jsonl"
    workflow_steps_path = base_dir / "workflow_steps.jsonl"
    if not recipes_path.exists():
        raise FileNotFoundError(
            "data/recipes.jsonl not found. Seed data is kept local; place local seed files under data/ before running seed."
        )
    if not workflow_steps_path.exists():
        raise FileNotFoundError(
            "data/workflow_steps.jsonl not found. Generate local workflow step seed before running seed."
        )
    demo_fridge_items = build_demo_fridge_items(date.today())
    rng = random.Random(20260317)
    sampled_recipes = []
    recipe_count = 0

    with connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM recipe_search_terms")
            cur.execute("DELETE FROM workflow_steps")
            cur.execute("DELETE FROM recipe_search_plans")
            cur.execute("DELETE FROM shopping_list_runs")
            cur.execute("DELETE FROM cooking_sessions")
            cur.execute("DELETE FROM fridge_items")
            cur.execute("DELETE FROM fridge_input_logs")
            cur.execute("DELETE FROM recipes")
            with cur.copy(
                """
                COPY recipes (
                    id, title, cuisine, summary, servings,
                    primary_ingredients, required_ingredients, optional_ingredients,
                    search_keywords, workflow_file
                ) FROM STDIN
                """
            ) as copy:
                for row in iter_jsonl(recipes_path):
                    recipe_count += 1
                    if len(sampled_recipes) < 4:
                        sampled_recipes.append({"id": row["id"]})
                    else:
                        replace_at = rng.randint(1, recipe_count)
                        if replace_at <= 4:
                            sampled_recipes[replace_at - 1] = {"id": row["id"]}
                    copy.write_row(
                        (
                            row["id"],
                            row["title"],
                            row["cuisine"],
                            row["summary"],
                            row["servings"],
                            json.dumps(row["primary_ingredients"]),
                            json.dumps(row["required_ingredients"]),
                            json.dumps(row["optional_ingredients"]),
                            json.dumps(row["search_keywords"]),
                            row.get("workflow_file") or f"db://workflow_steps/{row['id']}",
                        )
                    )
            with cur.copy(
                """
                COPY workflow_steps (
                    recipe_id, step_number, title, description, ingredients, tool, estimated_seconds, estimated_minutes
                ) FROM STDIN
                """
            ) as copy:
                for row in iter_jsonl(workflow_steps_path):
                    copy.write_row(
                        (
                            row["recipe_id"],
                            row["step_number"],
                            row["title"],
                            row["description"],
                            json.dumps(row["ingredients"]),
                            row["tool"],
                            row["estimated_seconds"],
                            row.get("estimated_minutes"),
                        )
                    )
            cur.execute(
                """
                INSERT INTO recipe_search_terms (recipe_id, term, term_weight)
                WITH search_term_rows AS (
                    SELECT
                        r.id AS recipe_id,
                        REPLACE(LOWER(keyword.term), ' ', '') AS term,
                        CASE
                            WHEN REPLACE(LOWER(keyword.term), ' ', '') = ANY(primary_terms.terms) THEN 2
                            ELSE 1
                        END AS term_weight
                    FROM recipes r
                    CROSS JOIN LATERAL jsonb_array_elements_text(r.search_keywords) AS keyword(term)
                    CROSS JOIN LATERAL (
                        SELECT ARRAY_AGG(REPLACE(LOWER(primary_term), ' ', '')) AS terms
                        FROM jsonb_array_elements_text(r.primary_ingredients) AS primary_term
                    ) AS primary_terms
                )
                SELECT
                    recipe_id,
                    term,
                    MAX(term_weight) AS term_weight
                FROM search_term_rows
                WHERE term <> ''
                GROUP BY recipe_id, term
                ON CONFLICT (recipe_id, term) DO UPDATE SET
                    term_weight = EXCLUDED.term_weight
                """
            )
            for item in demo_fridge_items:
                cur.execute(
                    """
                    INSERT INTO fridge_items (
                        id, name, normalized_name, quantity, unit,
                        expiry_date, days_left, source_text_id
                    ) VALUES (%(id)s, %(name)s, %(normalized_name)s, %(quantity)s, %(unit)s, %(expiry_date)s, %(days_left)s, NULL)
                    """,
                    item,
                )
            demo_sessions = build_demo_sessions(sampled_recipes)
            for session in demo_sessions:
                cur.execute(
                    """
                    INSERT INTO cooking_sessions (id, recipe_id, completed_at, actual_seconds)
                    VALUES (%(id)s, %(recipe_id)s, %(completed_at)s, %(actual_seconds)s)
                    """,
                    session,
                )
        conn.commit()
    print(
        f"Seeded {recipe_count} recipe(s), workflow steps from {workflow_steps_path.name}, "
        f"{len(demo_fridge_items)} fridge item(s), {len(demo_sessions)} completion record(s)."
    )


if __name__ == "__main__":
    main()
