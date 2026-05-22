"""
MentoriaConecta - Rotas Principais
"""
from flask import Blueprint, render_template, session, redirect, url_for
from app.utils.supabase_client import get_supabase

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Landing page pública."""
    sb = get_supabase()
    # Estatísticas para a home
    try:
        mentores = sb.table("usuarios").select("id", count="exact").eq("tipo", "mentor").eq("ativo", True).execute()
        alunos = sb.table("usuarios").select("id", count="exact").eq("tipo", "aluno").eq("ativo", True).execute()
        sessoes = sb.table("sessoes").select("id", count="exact").eq("status", "realizada").execute()
        stats = {
            "mentores": mentores.count or 0,
            "alunos": alunos.count or 0,
            "sessoes": sessoes.count or 0,
        }
    except Exception:
        stats = {"mentores": 0, "alunos": 0, "sessoes": 0}

    usuario_logado = session.get("usuario")
    return render_template("index.html", stats=stats, usuario=usuario_logado)


@main_bp.route("/dashboard")
def dashboard():
    """Redireciona para dashboard correto conforme tipo de usuário."""
    usuario = session.get("usuario")
    if not usuario:
        return redirect(url_for("auth.login"))
    tipo = usuario.get("tipo")
    if tipo == "admin":
        return redirect(url_for("admin.dashboard"))
    elif tipo == "mentor":
        return redirect(url_for("mentor.dashboard"))
    else:
        return redirect(url_for("aluno.dashboard"))
