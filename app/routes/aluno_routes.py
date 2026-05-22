"""
MentoriaConecta - Rotas do Aluno
Dashboard, recomendações, solicitação de mentoria
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from app.utils.auth import recomendar_mentores
from app.utils.supabase_client import get_supabase

aluno_bp = Blueprint("aluno", __name__)


def _get_usuario_session():
    return session.get("usuario")


@aluno_bp.route("/dashboard")
def dashboard():
    usuario = _get_usuario_session()
    if not usuario:
        return redirect(url_for("auth.login"))

    sb = get_supabase()
    aluno_id = usuario["id"]

    # Minhas mentorias
    mentorias = (sb.table("mentorias")
                 .select("*, mentor:mentor_id(nome, email, foto_url, bio)")
                 .eq("aluno_id", aluno_id)
                 .execute()).data or []

    # Próximas sessões
    sessoes = (sb.table("sessoes")
               .select("*, mentoria:mentoria_id(mentor_id)")
               .eq("status", "agendada")
               .order("data_hora")
               .limit(5)
               .execute()).data or []

    # Recomendações
    try:
        recomendacoes = recomendar_mentores(aluno_id, limite=3)
    except Exception:
        recomendacoes = []

    return render_template(
        "dashboard/aluno_dashboard.html",
        usuario=usuario,
        mentorias=mentorias,
        sessoes=sessoes,
        recomendacoes=recomendacoes,
        stats={"total_mentorias": len(mentorias), "total_sessoes": len(sessoes)},
    )


@aluno_bp.route("/solicitar-mentoria/<mentor_id>", methods=["POST"])
def solicitar_mentoria(mentor_id):
    """Aluno solicita mentoria com um mentor."""
    usuario = _get_usuario_session()
    if not usuario or usuario["tipo"] != "aluno":
        return redirect(url_for("auth.login"))

    sb = get_supabase()
    aluno_id = usuario["id"]

    # Verifica se já existe
    existe = (sb.table("mentorias")
              .select("id")
              .eq("mentor_id", mentor_id)
              .eq("aluno_id", aluno_id)
              .execute()).data

    if existe:
        flash("Você já possui ou solicitou mentoria com este mentor.", "aviso")
        return redirect(url_for("aluno.dashboard"))

    sb.table("mentorias").insert({
        "mentor_id": mentor_id,
        "aluno_id": aluno_id,
        "area_foco": request.form.get("area_foco", ""),
        "objetivo": request.form.get("objetivo", ""),
        "status": "pendente",
    }).execute()

    flash("Solicitação enviada! Aguarde o mentor aceitar.", "sucesso")
    return redirect(url_for("aluno.dashboard"))


@aluno_bp.route("/recomendacoes")
def recomendacoes():
    """Página de mentores recomendados para o aluno."""
    usuario = _get_usuario_session()
    if not usuario:
        return redirect(url_for("auth.login"))

    try:
        mentores = recomendar_mentores(usuario["id"], limite=10)
    except Exception:
        mentores = []

    return render_template("students/recomendacoes.html", usuario=usuario, mentores=mentores)


@aluno_bp.route("/perfil", methods=["GET", "POST"])
def perfil():
    usuario = _get_usuario_session()
    if not usuario:
        return redirect(url_for("auth.login"))

    sb = get_supabase()
    aluno_id = usuario["id"]

    if request.method == "POST":
        dados = request.form
        sb.table("usuarios").update({
            "nome": dados.get("nome"),
            "telefone": dados.get("telefone"),
            "cidade": dados.get("cidade"),
            "estado": dados.get("estado"),
            "bio": dados.get("bio"),
        }).eq("id", aluno_id).execute()

        # Habilidades que busca
        habilidades_ids = request.form.getlist("habilidades")
        sb.table("usuario_habilidades").delete().eq("usuario_id", aluno_id).execute()
        for hid in habilidades_ids:
            sb.table("usuario_habilidades").insert({
                "usuario_id": aluno_id,
                "habilidade_id": int(hid),
                "nivel": "basico"
            }).execute()

        session["usuario"]["nome"] = dados.get("nome")
        flash("Perfil atualizado!", "sucesso")
        return redirect(url_for("aluno.perfil"))

    aluno = sb.table("usuarios").select("*").eq("id", aluno_id).single().execute().data
    habilidades_all = sb.table("habilidades").select("*").order("categoria").execute().data or []
    habilidades_aluno = (sb.table("usuario_habilidades")
                         .select("habilidade_id")
                         .eq("usuario_id", aluno_id)
                         .execute()).data or []
    ids_aluno = {h["habilidade_id"] for h in habilidades_aluno}

    return render_template("students/perfil.html",
                           usuario=usuario, aluno=aluno,
                           habilidades_all=habilidades_all, ids_aluno=ids_aluno)


# ── API ────────────────────────────────────────────────────────

@aluno_bp.route("/api/recomendacoes")
def api_recomendacoes():
    usuario = _get_usuario_session()
    if not usuario:
        return jsonify({"erro": "Não autenticado"}), 401
    mentores = recomendar_mentores(usuario["id"])
    return jsonify(mentores)
