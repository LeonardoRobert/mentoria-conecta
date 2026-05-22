"""
MentoriaConecta - Rotas de Sessões e Feedbacks
Agendamento, confirmação, avaliação
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from app.utils.supabase_client import get_supabase

sessao_bp = Blueprint("sessao", __name__)


def _get_usuario_session():
    return session.get("usuario")


@sessao_bp.route("/agendar/<mentoria_id>", methods=["GET", "POST"])
def agendar(mentoria_id):
    """Agenda uma nova sessão dentro de uma mentoria."""
    usuario = _get_usuario_session()
    if not usuario:
        return redirect(url_for("auth.login"))

    sb = get_supabase()

    if request.method == "POST":
        dados = request.form
        nova_sessao = {
            "mentoria_id": mentoria_id,
            "data_hora": dados["data_hora"],
            "duracao_minutos": int(dados.get("duracao_minutos", 60)),
            "formato": dados.get("formato", "online"),
            "link_reuniao": dados.get("link_reuniao", ""),
            "local": dados.get("local", ""),
            "notas": dados.get("notas", ""),
            "status": "agendada",
        }
        sb.table("sessoes").insert(nova_sessao).execute()
        flash("Sessão agendada com sucesso!", "sucesso")
        return redirect(url_for("main.dashboard"))

    mentoria = (sb.table("mentorias")
                .select("*, mentor:mentor_id(nome), aluno:aluno_id(nome)")
                .eq("id", mentoria_id)
                .single()
                .execute()).data

    return render_template("sessions/agendar.html", usuario=usuario, mentoria=mentoria)


@sessao_bp.route("/feedback/<sessao_id>", methods=["GET", "POST"])
def feedback(sessao_id):
    """Registra feedback após uma sessão."""
    usuario = _get_usuario_session()
    if not usuario:
        return redirect(url_for("auth.login"))

    sb = get_supabase()

    if request.method == "POST":
        dados = request.form
        avaliado_id = dados.get("avaliado_id")
        sb.table("feedbacks").insert({
            "sessao_id": sessao_id,
            "avaliador_id": usuario["id"],
            "avaliado_id": avaliado_id,
            "nota": int(dados["nota"]),
            "comentario": dados.get("comentario", ""),
        }).execute()
        sb.table("sessoes").update({"status": "realizada"}).eq("id", sessao_id).execute()
        flash("Feedback registrado! Obrigado.", "sucesso")
        return redirect(url_for("main.dashboard"))

    sessao = (sb.table("sessoes")
              .select("*, mentoria:mentoria_id(mentor_id, aluno_id, mentor:mentor_id(nome), aluno:aluno_id(nome))")
              .eq("id", sessao_id)
              .single()
              .execute()).data

    return render_template("sessions/feedback.html", usuario=usuario, sessao=sessao)


@sessao_bp.route("/cancelar/<sessao_id>", methods=["POST"])
def cancelar(sessao_id):
    """Cancela uma sessão agendada."""
    usuario = _get_usuario_session()
    if not usuario:
        return jsonify({"erro": "Não autenticado"}), 401

    sb = get_supabase()
    sb.table("sessoes").update({"status": "cancelada"}).eq("id", sessao_id).execute()
    flash("Sessão cancelada.", "aviso")
    return redirect(url_for("main.dashboard"))


# ── API ────────────────────────────────────────────────────────

@sessao_bp.route("/api/proximas")
def api_proximas():
    usuario = _get_usuario_session()
    if not usuario:
        return jsonify({"erro": "Não autenticado"}), 401

    sb = get_supabase()
    resp = (sb.table("sessoes")
            .select("*")
            .eq("status", "agendada")
            .order("data_hora")
            .limit(10)
            .execute())
    return jsonify(resp.data or [])
