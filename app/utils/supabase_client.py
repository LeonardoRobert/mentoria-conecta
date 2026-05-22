"""
MentoriaConecta - Conexão com Supabase
Centraliza o cliente Supabase para uso em toda a aplicação
"""
from supabase import create_client, Client
from config import Config

_supabase_client: Client | None = None


def get_supabase() -> Client:
    """Retorna o cliente Supabase (singleton)."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    return _supabase_client


def get_supabase_admin() -> Client:
    """
    Retorna cliente Supabase com service_role (acesso total).
    Use apenas em operações administrativas no servidor.
    """
    return create_client(Config.SUPABASE_URL, Config.SUPABASE_SECRET)
