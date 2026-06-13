from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# For local development and easy testing, we will use an SQLite database file.
# Because SQLAlchemy abstracts everything, swapping this out for production 
# PostgreSQL requires changing just this single URL string later!
DATABASE_URL = "sqlite:///./failsafe.db"

# 1. Create the engine that talks to our database file
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# 2. Create a Session Local factory (each request to the API gets its own database connection session)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Create a Base class that our tables will inherit from
Base = declarative_base()

# Dependency to get a fresh database session for a web request, and close it when done
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()