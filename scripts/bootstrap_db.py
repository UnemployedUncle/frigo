from psycopg import connect

from app.config import settings
from scripts.migrate import main as migrate_main
from scripts.seed_recipes import main as seed_main
from scripts.validate_workflows import main as validate_main


def database_has_seed_data(database_url: str) -> bool:
    with connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    EXISTS (SELECT 1 FROM recipes LIMIT 1),
                    EXISTS (SELECT 1 FROM workflow_steps LIMIT 1)
                """
            )
            recipes_exist, workflow_steps_exist = cur.fetchone()
    return bool(recipes_exist and workflow_steps_exist)


def bootstrap_database(database_url: str = settings.database_url) -> bool:
    migrate_main()
    seeded = False
    if not database_has_seed_data(database_url):
        seed_main()
        seeded = True
    validate_main()
    return seeded


def main() -> None:
    seeded = bootstrap_database()
    print("Database seeded during bootstrap." if seeded else "Existing seed data detected; skipping reseed.")


if __name__ == "__main__":
    main()
