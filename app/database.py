"""
Database Configuration and Connection using SQLAlchemy
Uses SQLite by default (stored at data/crop_doctor.db)
Easily switchable to PostgreSQL by updating DATABASE_URL
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database path in project data folder
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "crop_doctor.db"

# Connection URL: uses environment variable if available, else local SQLite
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH.as_posix()}")

# Render PostgreSQL URL compatibility (postgres:// -> postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# create_engine connects to database
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """
    FastAPI dependency that yields a database session per request
    and automatically closes it when request completes (similar to PHP PDO lifecycle).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
