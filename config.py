"""
MentoriaConecta - Configurações do Sistema
Plataforma de Mentorias para Alunos de Baixa Renda
ODS 4 - Educação de Qualidade
"""
import os
from datetime import timedelta

class Config:
    # ============================================================
    #  SUPABASE - Cole suas chaves aqui
    # ============================================================
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "COLE_SUA_SUPABASE_URL_AQUI")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "COLE_SUA_SUPABASE_ANON_KEY_AQUI")
    SUPABASE_SECRET = os.environ.get("SUPABASE_SECRET", "COLE_SUA_SUPABASE_SERVICE_ROLE_KEY_AQUI")

    # ============================================================
    #  JWT - Autenticação
    # ============================================================
    SECRET_KEY = os.environ.get("SECRET_KEY", "mentoria-conecta-secret-key-2025")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-mentoria-secret-2025")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)

    # ============================================================
    #  Flask
    # ============================================================
    DEBUG = os.environ.get("FLASK_DEBUG", "True") == "True"
    FLASK_ENV = os.environ.get("FLASK_ENV", "development")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
