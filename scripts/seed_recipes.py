import json
from pathlib import Path

from psycopg import connect

from app.config import settings


def normalize_terms(values):
    return list(dict.fromkeys(value.replace(" ", "").lower() for value in values if value))


def main() -> None:
    data_path = Path(__file__).resolve().parents[1] / "data" / "recipes.jsonl"
    if not data_path.exists():
        raise FileNotFoundError(
            "data/recipes.jsonl not found. Seed data is kept local; place local seed files under data/ before running seed."
        )
    rows = [json.loads(line) for line in data_path.read_text().splitlines() if line.strip()]

    with connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM recipe_search_terms")
            cur.execute("DELETE FROM shopping_list_runs")
            cur.execute("DELETE FROM recipes")
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
                primary_terms = set(normalize_terms(row["primary_ingredients"]))
                for term in normalize_terms(row["search_keywords"]):
                    cur.execute(
                        """
                        INSERT INTO recipe_search_terms (recipe_id, term, term_weight)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (recipe_id, term) DO UPDATE SET
                            term_weight = EXCLUDED.term_weight
                        """,
                        (row["id"], term, 2 if term in primary_terms else 1),
                    )
        conn.commit()
    print(f"Seeded {len(rows)} recipe(s).")


if __name__ == "__main__":
    main()
