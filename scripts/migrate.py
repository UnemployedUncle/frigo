from pathlib import Path

from psycopg import connect

from app.config import settings


def main() -> None:
    migration_dir = Path(__file__).resolve().parents[1] / "migrations"
    files = sorted(migration_dir.glob("*.sql"))
    with connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            for file in files:
                cur.execute(file.read_text())
        conn.commit()
    print(f"Applied {len(files)} migration(s).")


if __name__ == "__main__":
    main()
