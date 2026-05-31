"""Create tables and seed — run from backend/: python init_db.py"""

from app.database import Base, engine
from migrate_recipe_catalog import migrate
from seed import run_full_seed

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    migrate()
    run_full_seed()
    print("Database initialized.")