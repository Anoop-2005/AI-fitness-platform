"""
All configuration in one place, loaded from environment variables.
Copy .env.example to .env and fill these in.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Supabase Postgres connection string. In the Supabase dashboard:
# Project Settings -> Database -> Connection string -> URI (use the
# "Session pooler" one for a simple beginner setup).
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Project Settings -> API -> Project URL (e.g. https://xxxxx.supabase.co).
# Used to build the JWKS URL that verifies login tokens — see auth.py.
SUPABASE_URL = os.getenv("SUPABASE_URL", "")

# Optional. Only needed if your project still uses the legacy HS256 shared
# secret instead of the newer asymmetric (ES256) signing keys — Project
# Settings -> JWT Keys -> "Legacy JWT Secret". Leave blank if you're on a
# project created after October 2025; JWKS verification alone handles it.
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")

# Free API keys — see backend/.env.example for where to get each one.
USDA_API_KEY = os.getenv("USDA_API_KEY", "DEMO_KEY")  # DEMO_KEY works but is heavily rate-limited
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# A shared secret only you know, used to protect the /api/sync endpoints
# (these should only ever be called by you/a cron job, never the frontend).
SYNC_SECRET = os.getenv("SYNC_SECRET", "change-me")
