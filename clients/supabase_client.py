"""Supabase client — service role (backend) and anon (read-only)."""

from functools import lru_cache

from supabase import create_client, Client

from app.config import get_settings


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Service-role Supabase client (full read/write access)."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


@lru_cache(maxsize=1)
def get_supabase_anon_client() -> Client:
    """Anon-key Supabase client (read-only, matches frontend access)."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_anon_key)
