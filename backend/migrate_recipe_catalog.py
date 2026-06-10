"""One-shot migration for existing recipe_catalog tables.

Run from backend/: python migrate_recipe_catalog.py
"""

from sqlalchemy import inspect, text

from app.database import engine


def column_names(table: str) -> set[str]:
    insp = inspect(engine)
    return {c["name"] for c in insp.get_columns(table)}


def migrate() -> None:
    insp = inspect(engine)
    if "recipe_catalog" not in insp.get_table_names():
        print("recipe_catalog table not found, skipping migration")
        return

    cols = column_names("recipe_catalog")

    with engine.begin() as conn:
        if "recipe_url" in cols and "external_url" not in cols:
            conn.execute(text("ALTER TABLE recipe_catalog RENAME COLUMN recipe_url TO external_url"))
            cols.remove("recipe_url")
            cols.add("external_url")

        if "external_url" in cols:
            conn.execute(text("ALTER TABLE recipe_catalog ALTER COLUMN external_url DROP NOT NULL"))

        if "display_name" not in cols:
            conn.execute(text("ALTER TABLE recipe_catalog ADD COLUMN display_name VARCHAR(255)"))

        if "ingredients" not in cols:
            conn.execute(
                text("ALTER TABLE recipe_catalog ADD COLUMN ingredients JSONB NOT NULL DEFAULT '[]'::jsonb")
            )

        if "instructions" not in cols:
            conn.execute(text("ALTER TABLE recipe_catalog ADD COLUMN instructions TEXT NOT NULL DEFAULT ''"))

        if "image_path" not in cols:
            conn.execute(text("ALTER TABLE recipe_catalog ADD COLUMN image_path VARCHAR(512)"))

        if "updated_at" not in cols:
            conn.execute(
                text(
                    "ALTER TABLE recipe_catalog ADD COLUMN updated_at TIMESTAMP "
                    "NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')"
                )
            )

    print("recipe_catalog migration complete.")


if __name__ == "__main__":
    migrate()
