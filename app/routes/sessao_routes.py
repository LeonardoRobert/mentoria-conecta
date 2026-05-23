"""
MentoriaConecta - Rotas de Sessões
Mentor cria sessões com vagas; aluno se inscreve
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from app.utils.supabase_client import get_supabase

sessao_bp = Blueprint("sessao", __name__)

def _usuario():
    return session.get("usuario")


# ── MENTOR: criar sessão com vagas ────────────────────────────

@sessao_bp.route("/criar/<mentoria_id>", methods=["GET", "POST"])
def criar(mentoria_id):
    usuario = _usuario()
    if not usuario or usuario["tipo"] != "mentor":
        return redirect(url_for("auth.login"))

    sb = get_supabase()

    if request.method == "POST":
        d = request.form
        nova = {
            "mentoria_id": mentoria_id,
            "tema": d.get("tema", ""),
            "data_hora": d["data_hora"],
            "duracao_minutos": int(d.get("duracao_minutos", 60)),
            "vagas_total": int(d.get("vagas_total", 10)),
            "formato": d.get("formato", "online"),
            "link_reuniao": d.get("link_reuniao", ""),
            "local": d.get("local", ""),
            "notas": d.get("notas", ""),
            "status": "agendada",
        }
        sb.table("sessoes").insert(nova).execute()
        flash("Sessão criada com sucesso!", "sucesso")
        return redirect(url_for("mentor.dashboard"))

    mentoria = (sb.table("mentorias")
                .select("*, aluno:aluno_id(nome)")
                .eq("id", mentoria_id)
                .single().execute()).data

    return render_template("sessions/criar.html", usuario=usuario, mentoria=mentoria)


# ── MENTOR: minhas sessões ────────────────────────────────────

@sessao_bp.route("/minhas")
def minhas_sessoes():
    usuario = _usuario()
    if not usuario:
        return redirect(url_for("auth.login"))

    sb = get_supabase()

    if usuario["tipo"] == "mentor":
        # Busca mentorias do mentor para pegar sessões
        mentorias = (sb.table("mentorias")
                     .select("id")
                     .eq("mentor_id", usuario["id"])
                     .eq("status", "ativa")
                     .execute()).data or []
        ids = [m["id"] for m in mentorias]

        sessoes = []
        for mid in ids:
            s = (sb.table("sessoes")
                 .select("*")
                 .eq("mentoria_id", mid)
                 .order("data_hora")
                 .execute()).data or []
            for sess in s:
                # Conta inscritos
                inscritos = (sb.table("inscricoes_sessao")
                             .select("id", count="exact")
                             .eq("sessao_id", sess["id"])
                             .neq("status", "cancelado")
                             .execute()).count or 0
                sess["inscritos"] = inscritos
                sess["vagas_livres"] = sess.get("vagas_total", 10) - inscritos
                sessoes.append(sess)

        return render_template("sessions/mentor_sessoes.html", usuario=usuario, sessoes=sessoes)

    else:
        # Aluno: sessões em que está inscrito
        inscrições = (sb.table("inscricoes_sessao")
                      .select("*, sessao:sessao_id(*)")
                      .eq("aluno_id", usuario["id"])
                      .neq("status", "cancelado")
                      .execute()).data or []
        return render_template("sessions/aluno_sessoes.html", usuario=usuario, inscricoes=inscrições)


# ── ALUNO: inscrever-se em sessão ────────────────────────────

@sessao_bp.route("/inscrever/<sessao_id>", methods=["POST"])
def inscrever(sessao_id):
    usuario = _usuario()
    if not usuario or usuario["tipo"] != "aluno":
        flash("Apenas alunos podem se inscrever.", "erro")
        return redirect(url_for("main.dashboard"))

    sb = get_supabase()
    aluno_id = usuario["id"]

    # Verifica se já está inscrito
    existe = (sb.table("inscricoes_sessao")
              .select("id")
              .eq("sessao_id", sessao_id)
              .eq("aluno_id", aluno_id)
              .execute()).data

    if existe:
        flash("Você já está inscrito nesta sessão.", "aviso")
        return redirect(url_for("aluno.dashboard"))

    # Verifica vagas
    sessao = (sb.table("sessoes").select("*").eq("id", sessao_id).single().execute()).data
    inscritos = (sb.table("inscricoes_sessao")
                 .select("id", count="exact")
                 .eq("sessao_id", sessao_id)
                 .neq("status", "cancelado")
                 .execute()).count or 0

    if inscritos >= (sessao.get("vagas_total") or 10):
        flash("Esta sessão não possui mais vagas disponíveis.", "erro")
        return redirect(url_for("aluno.dashboard"))

    sb.table("inscricoes_sessao").insert({
        "sessao_id": sessao_id,
        "aluno_id": aluno_id,
        "status": "inscrito",
    }).execute()

    flash("Inscrição realizada! Até a sessão.", "sucesso")
    return redirect(url_for("aluno.dashboard"))


# ── ALUNO: cancelar inscrição ─────────────────────────────────

@sessao_bp.route("/cancelar-inscricao/<sessao_id>", methods=["POST"])
def cancelar_inscricao(sessao_id):
    usuario = _usuario()
    if not usuario:
        return redirect(url_for("auth.login"))

    sb = get_supabase()
    sb.table("inscricoes_sessao").update({"status": "cancelado"}).eq("sessao_id", sessao_id).eq("aluno_id", usuario["id"]).execute()
    flash("Inscrição cancelada.", "aviso")
    return redirect(url_for("sessao.minhas_sessoes"))


# ── MENTOR: cancelar sessão ───────────────────────────────────

@sessao_bp.route("/cancelar/<sessao_id>", methods=["POST"])
def cancelar(sessao_id):
    usuario = _usuario()
    if not usuario:
        return redirect(url_for("auth.login"))

    sb = get_supabase()
    sb.table("sessoes").update({"status": "cancelada"}).eq("id", sessao_id).execute()
    flash("Sessão cancelada.", "aviso")
    return redirect(url_for("sessao.minhas_sessoes"))


# ── FEEDBACK ──────────────────────────────────────────────────

@sessao_bp.route("/feedback/<sessao_id>", methods=["GET", "POST"])
def feedback(sessao_id):
    usuario = _usuario()
    if not usuario:
        return redirect(url_for("auth.login"))

    sb = get_supabase()

    if request.method == "POST":
        d = request.form
        sb.table("feedbacks").insert({
            "sessao_id": sessao_id,
            "avaliador_id": usuario["id"],
            "avaliado_id": d.get("avaliado_id"),
            "nota": int(d["nota"]),
            "comentario": d.get("comentario", ""),
        }).execute()
        flash("Avaliação registrada. Obrigado!", "sucesso")
        return redirect(url_for("main.dashboard"))

    sessao = (sb.table("sessoes")
              .select("*, mentoria:mentoria_id(mentor_id, aluno_id, mentor:mentor_id(nome), aluno:aluno_id(nome))")
              .eq("id", sessao_id).single().execute()).data

    return render_template("sessions/feedback.html", usuario=usuario, sessao=sessao)
