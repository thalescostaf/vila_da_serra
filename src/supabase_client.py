# src/supabase_client.py
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Carrega variáveis do .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SCHEMA = "vila_da_serra"

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Defina SUPABASE_URL e SUPABASE_KEY no arquivo .env")

_supabase: Client | None = None

def get_client() -> Client:
    global _supabase
    if _supabase is None:
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase

supabase = get_client()

def ensure_postgrest_auth() -> bool:
    """
    Garante que o PostgREST esteja usando o token da sessão atual.
    Chame após login e no início de cada página.
    Retorna True se um token válido foi aplicado, False caso contrário.
    """
    try:
        session = supabase.auth.get_session()
        token = getattr(session, "access_token", None)
        if token:
            supabase.postgrest.auth(token)
            return True
        # Sem sessão: limpa o header para evitar 'resquícios' de sessões antigas
        supabase.postgrest.auth(None)
    except Exception:
        # Em caso de qualquer erro, não quebra a app
        pass
    return False

def table(name: str):
    # Builder já apontado para o schema vila_da_serra
    return supabase.postgrest.schema(SCHEMA).from_(name)
