# backend/config.py
"""
Central configuration for FAILSAFE.
All secrets come from .env — this file itself is safe to commit.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # Reads .env file and loads it into os.environ

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Fail loudly if critical secrets are missing
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set. Check your .env file.")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY is not set. Check your .env file.")