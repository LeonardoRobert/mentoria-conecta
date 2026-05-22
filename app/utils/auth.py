"""
MentoriaConecta - Autenticação JWT
Login, registro, proteção de rotas e hash de senhas
"""
from functools import wraps
from datetime import datetime, timezone, timedelta
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request, jsonify, session
from config import Config
from app.utils.supabase_client import get_supabase


# ──────────────────────────────────────────────────────────────
# Senhas
# ──────────────────────────────────────────────────────────────

def hash_senha(senha: str) -> str:
    return generate_password_hash(senha)


def verificar_senha(senha: str, hash: str) -> bool:
    return check_password_hash(hash, senha)


# ──────────────────────────────────────────────────────────────
# JWT
# ──────────────────────────────────────────────────────────────

def gerar_token(usuario_id: str, tipo: str) -> str:
    """Gera um token JWT com 8h de validade."""
    payload = {
        "sub": usuario_id,
        "tipo": tipo,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=8),
    }
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm="HS256")


def decodificar_token(token: str) -> dict | None:
    """Decodifica e valida um token JWT."""
    try:
        return jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ──────────────────────────────────────────────────────────────
# Decoradores de proteção de rota
# ──────────────────────────────────────────────────────────────

def login_required(f):
    """Protege rotas que exigem login. Lê token da session ou header."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = session.get("token") or request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return jsonify({"erro": "Token não fornecido"}), 401
        dados = decodificar_token(token)
        if not dados:
            return jsonify({"erro": "Token inválido ou expirado"}), 401
        request.usuario_id = dados["sub"]
        request.usuario_tipo = dados["tipo"]
        return f(*args, **kwargs)
    return decorated


def apenas_mentor(f):
    """Restringe rota apenas para mentores."""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if request.usuario_tipo not in ("mentor", "admin"):
            return jsonify({"erro": "Acesso negado"}), 403
        return f(*args, **kwargs)
    return decorated


def apenas_admin(f):
    """Restringe rota apenas para admins."""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if request.usuario_tipo != "admin":
            return jsonify({"erro": "Acesso negado"}), 403
        return f(*args, **kwargs)
    return decorated


# ──────────────────────────────────────────────────────────────
# Algoritmo de Recomendação (Matemática Discreta / Grafos)
# Pontuação de compatibilidade mentor ↔ aluno
# ──────────────────────────────────────────────────────────────

def calcular_compatibilidade(habilidades_mentor: list, habilidades_aluno: list) -> float:
    """
    Calcula índice de compatibilidade usando Coeficiente de Jaccard.
    J(A,B) = |A ∩ B| / |A ∪ B|
    Retorna valor entre 0 (nenhuma compatibilidade) e 1 (compatibilidade total).
    """
    set_mentor = set(habilidades_mentor)
    set_aluno = set(habilidades_aluno)

    intersecao = set_mentor & set_aluno
    uniao = set_mentor | set_aluno

    if not uniao:
        return 0.0

    jaccard = len(intersecao) / len(uniao)
    return round(jaccard * 100, 1)  # Retorna em percentual


def recomendar_mentores(aluno_id: str, limite: int = 5) -> list:
    """
    Recomenda mentores mais compatíveis para um aluno.
    Usa: Coeficiente de Jaccard + média de avaliações + quantidade de sessões.
    """
    sb = get_supabase()

    # Habilidades do aluno
    resp_aluno = (sb.table("usuario_habilidades")
                  .select("habilidade_id")
                  .eq("usuario_id", aluno_id)
                  .execute())
    ids_aluno = [r["habilidade_id"] for r in (resp_aluno.data or [])]

    # Todos os mentores ativos com suas habilidades e avaliações
    resp_mentores = (sb.table("vw_ranking_mentores")
                     .select("*")
                     .execute())

    resultados = []
    for mentor in (resp_mentores.data or []):
        resp_hab = (sb.table("usuario_habilidades")
                    .select("habilidade_id")
                    .eq("usuario_id", mentor["id"])
                    .execute())
        ids_mentor = [r["habilidade_id"] for r in (resp_hab.data or [])]

        compatibilidade = calcular_compatibilidade(ids_mentor, ids_aluno)
        media = float(mentor.get("media_avaliacao") or 0)
        sessoes = int(mentor.get("total_sessoes") or 0)

        # Score final: 60% compatibilidade + 30% avaliação + 10% experiência (máx 30 sessões)
        score = (compatibilidade * 0.6) + (media * 20 * 0.3) + (min(sessoes, 30) / 30 * 100 * 0.1)

        resultados.append({**mentor, "compatibilidade": compatibilidade, "score": round(score, 1)})

    resultados.sort(key=lambda x: x["score"], reverse=True)
    return resultados[:limite]
