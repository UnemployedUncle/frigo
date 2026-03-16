import json
from pathlib import Path

from psycopg import connect

from app.config import settings


def main() -> None:
    data_path = Path(__file__).resolve().parents[1] / "data" / "recipes.jsonl"
    rows = [json.loads(line) for line in data_path.read_text().splitlines() if line.strip()]

    with connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            for row in rows:
                cur.execute(
                    """
                    INSERT INTO recipes (
                        id, title, cuisine, summary, servings,
                        primary_ingredients, required_ingredients, optional_ingredients,
                        search_keywords, workflow_file
                    ) VALUES (
                        %(id)s, %(title)s, %(cuisine)s, %(summary)s, %(servings)s,
                        %(primary_ingredients)s::jsonb, %(required_ingredients)s::jsonb,
                        %(optional_ingredients)s::jsonb, %(search_keywords)s::jsonb,
                        %(workflow_file)s
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        title = EXCLUDED.title,
                        cuisine = EXCLUDED.cuisine,
                        summary = EXCLUDED.summary,
                        servings = EXCLUDED.servings,
                        primary_ingredients = EXCLUDED.primary_ingredients,
                        required_ingredients = EXCLUDED.required_ingredients,
                        optional_ingredients = EXCLUDED.optional_ingredients,
                        search_keywords = EXCLUDED.search_keywords,
                        workflow_file = EXCLUDED.workflow_file,
                        updated_at = NOW()
                    """,
                    {
                        **row,
                        "primary_ingredients": json.dumps(row["primary_ingredients"]),
                        "required_ingredients": json.dumps(row["required_ingredients"]),
                        "optional_ingredients": json.dumps(row["optional_ingredients"]),
                        "search_keywords": json.dumps(row["search_keywords"]),
                    },
                )
        conn.commit()
    print(f"Seeded {len(rows)} recipe(s).")


if __name__ == "__main__":
    main()
