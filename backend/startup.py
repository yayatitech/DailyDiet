"""Lightweight startup: create tables + migrate schema (no destructive seed)."""

from app.database import Base, engine
from migrate_recipe_catalog import migrate


def run_startup() -> None:
    Base.metadata.create_all(bind=engine)
    migrate()


if __name__ == "__main__":
    run_startup()
    print("Startup complete (tables + migration).")
