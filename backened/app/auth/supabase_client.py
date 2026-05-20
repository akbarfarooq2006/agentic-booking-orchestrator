"""
Supabase Client Initialization.

Initializes the Supabase python client using credentials from the environment.
This client is used to communicate with Supabase Auth.
"""

from supabase import create_client, Client
from app.auth.config import auth_settings

def get_supabase_client() -> Client:
    """Returns an authenticated Supabase client instance."""
    url: str = auth_settings.SUPABASE_URL
    key: str = auth_settings.SUPABASE_ANON_KEY
    
    if not url or not key:
        # In a real scenario, this would raise an error, but for the hackathon
        # we might want to allow the app to start up before env vars are fully set.
        print("WARNING: Supabase URL or Anon Key is missing. Supabase client will fail.")
        
    return create_client(url, key)

# Singleton instance
supabase: Client = get_supabase_client()
