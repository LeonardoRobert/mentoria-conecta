"""
MentoriaConecta - Rotas do Mentor
Dashboard, perfil, alunos vinculados, disponibilidade
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from app.utils.auth import login_required
from app.utils.supabase_client import get_supabase

mentor_bp = Blueprint("mentor", __name__)


def _get_usuario_session():
    return session.get("usuario")


@mentor_bp.route("/dashboard")
def dashboard():
    usuario = _get_usuario_session()
    if not usuario:
        return redirect(url_for("auth.login"))

    sb = get_supabase()
    mentor_id = usuario["id"]

    # Mentorias ativas
    mentorias = (sb.table("mentorias")
                 .select("*, aluno:aluno_id(nome, email, foto_url)")
                 .eq("mentor_id", mentor_id)
                 .execute()).data or []

    # Próximas sessões
    sessoes = (sb.table("sessoes")
               .select("*, mentoria:mentoria_id(aluno_id)")
               .eq("status", "agendada")
               .order("data_hora")
               .limit(5)
               .execute()).data or []

    # Estatísticas
    total_sessoes = (sb.table("sessoes")
                     .select("id", count="exact")
                     .execute()).count or 0

    feedbacks = (sb.table("feedbacks")
                 .select("nota")
                 .eq("avaliado_id", mentor_id)
                 .execute()).data or []
    media = round(sum(f["nota"] for f in feedbacks) / len(feedbacks), 1) if feedbacks else 0

    return render_template(
        "dashboard/mentor_dashboard.html",
        usuario=usuario,
        mentorias=mentorias,
        sessoes=sessoes,
        stats={"total_mentorias": len(mentorias), "total_sessoes": total_sessoes, "media_avaliacao": media},
    )


@mentor_bp.route("/perfil", methods=["GET", "POST"])
def perfil():
    usuario = _get_usuario_session()
    if not usuario:
        return redirect(url_for("auth.login"))

    sb = get_supabase()
    mentor_id = usuario["id"]

    if request.method == "POST":
        dados = request.form
        atualizacao = {
            "nome": dados.get("nome"),
            "telefone": dados.get("telefone"),
            "cidade": dados.get("cidade"),
            "estado": dados.get("estado"),
            "bio": dados.get("bio"),
        }
        sb.table("usuarios").update(atualizacao).eq("id", mentor_id).execute()

        # Atualiza habilidades
        habilidades_ids = request.form.getlist("habilidades")
        sb.table("usuario_habilidades").delete().eq("usuario_id", mentor_id).execute()
        for hid in habilidades_ids:
            sb.table("usuario_habilidades").insert({
                "usuario_id": mentor_id,
                "habilidade_id": int(hid),
                "nivel": "intermediario"
            }).execute()

        session["usuario"]["nome"] = dados.get("nome")
        flash("Perfil atualizado!", "sucesso")
        return redirect(url_for("mentor.perfil"))

    mentor = sb.table("usuarios").select("*").eq("id", mentor_id).single().execute().data
    habilidades_all = sb.table("habilidades").select("*").order("categoria").execute().data or []
    habilidades_mentor = (sb.table("usuario_habilidades")
                          .select("habilidade_id")
                          .eq("usuario_id", mentor_id)
                          .execute()).data or []
    ids_mentor = {h["habilidade_id"] for h in habilidades_mentor}

    return render_template("mentors/perfil.html",
                           usuario=usuario,
                           mentor=mentor,
                           habilidades_all=habilidades_all,
                           ids_mentor=ids_mentor)


@mentor_bp.route("/")
def lista():
    """Lista pública de mentores."""
    sb = get_supabase()
    mentores = sb.table("vw_ranking_mentores").select("*").execute().data or []
    habilidades = sb.table("habilidades").select("*").execute().data or []
    usuario = _get_usuario_session()
    return render_template("mentors/lista.html", mentores=mentores, habilidades=habilidades, usuario=usuario)


# ── Aceitar / Rejeitar solicitações ───────────────────────────

@mentor_bp.route("/aceitar/<mentoria_id>", methods=["POST"])
def aceitar_mentoria(mentoria_id):
    usuario = _get_usuario_session()
    if not usuario:
        return redirect(url_for("auth.login"))

    sb = get_supabase()
    # Garante que a mentoria pertence a este mentor
    sb.table("mentorias").update({"status": "ativa"}).eq("id", mentoria_id).eq("mentor_id", usuario["id"]).execute()
    flash("Mentoria aceita! Agora você pode agendar sessões.", "sucesso")
    return redirect(url_for("mentor.dashboard"))


@mentor_bp.route("/rejeitar/<mentoria_id>", methods=["POST"])
def rejeitar_mentoria(mentoria_id):
    usuario = _get_usuario_session()
    if not usuario:
        return redirect(url_for("auth.login"))

    sb = get_supabase()
    sb.table("mentorias").update({"status": "cancelada"}).eq("id", mentoria_id).eq("mentor_id", usuario["id"]).execute()
    flash("Solicitação recusada.", "aviso")
    return redirect(url_for("mentor.dashboard"))


# ── API Endpoints ──────────────────────────────────────────────

@mentor_bp.route("/api/minhas-mentorias")
def api_mentorias():
    usuario = _get_usuario_session()
    if not usuario:
        return jsonify({"erro": "Não autenticado"}), 401

    sb = get_supabase()
    resp = (sb.table("mentorias")
            .select("*, aluno:aluno_id(nome, email)")
            .eq("mentor_id", usuario["id"])
            .execute())
    return jsonify(resp.data or [])
