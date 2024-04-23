# Handle Supabase connetion
from supabase import Client, create_client
from .config import url, key

_url = url
_key = key

def create_supabase_client():
    supabase: Client = create_client(_url, _key)
    return supabase