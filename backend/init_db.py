"""Create tables and seed — run from backend/: python init_db.py"""

from app.database import Base, engine
from seed import run_seed

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    run_seed()
    print("Database initialized.")
