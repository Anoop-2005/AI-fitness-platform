"""
All configuration in one place, loaded from environment variables.
Copy .env.example to .env and fill these in.
"""
import os
from dotenv import load_dotenv

load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")


USDA_API_KEY = os.getenv("USDA_API_KEY", "DEMO_KEY")  
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

SYNC_SECRET = os.getenv("SYNC_SECRET", "change-me")
