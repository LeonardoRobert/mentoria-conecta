"""
MentoriaConecta - Rotas do Mentor
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from app.utils.supabase_client import get_supabase

mentor_bp = Blueprint("mentor", __name__)

def _u():
    return session.get("usuario")


@mentor_bp.route("/dashboard")
def dashboard():
    usuario = _u()
    if not usuario:
        return redirect(url_for("auth.login"))

    sb = get_supabase()
    mentor_id = usuario["id"]

    mentorias = (sb.table("mentorias")
                 .select("*, aluno:aluno_id(nome, email)")
                 .eq("mentor_id", mentor_id)
                 .execute()).data or []

    # Sessões futuras com contagem de inscritos
    ids_mentorias = [m["id"] for m in mentorias if m["status"] == "ativa"]
    sessoes = []
    for mid in ids_mentorias:
        ss = (sb.table("sessoes").select("*").eq("mentoria_id", mid).eq("status", "agendada").execute()).data or []
        for s in ss:
            count = (sb.table("inscricoes_sessao").select("id", count="exact").eq("sessao_id", s["id"]).neq("status","cancelado").execute()).count or 0
            s["inscritos"] = count
            s["vagas_livres"] = (s.get("vagas_total") or 10) - count
            sessoes.append(s)
    sessoes.sort(key=lambda x: x["data_hora"])

    feedbacks = (sb.table("feedbacks").select("nota").eq("avaliado_id", mentor_id).execute()).data or []
    media = round(sum(f["nota"] for f in feedbacks) / len(feedbacks), 1) if feedbacks else 0

    return render_template("dashboard/mentor_dashboard.html",
        usuario=usuario, mentorias=mentorias, sessoes=sessoes[:5],
        stats={"total_sessoes": len(sessoes), "media_avaliacao": media})


@mentor_bp.route("/aceitar/<mentoria_id>", methods=["POST"])
def aceitar_mentoria(mentoria_id):
    usuario = _u()
    if not usuario:
        return redirect(url_for("auth.login"))
    sb = get_supabase()
    sb.table("mentorias").update({"status": "ativa"}).eq("id", mentoria_id).eq("mentor_id", usuario["id"]).execute()
    flash("Mentoria aceita com sucesso!", "sucesso")
    return redirect(url_for("mentor.dashboard"))


@mentor_bp.route("/rejeitar/<mentoria_id>", methods=["POST"])
def rejeitar_mentoria(mentoria_id):
    usuario = _u()
    if not usuario:
        return redirect(url_for("auth.login"))
    sb = get_supabase()
    sb.table("mentorias").update({"status": "cancelada"}).eq("id", mentoria_id).eq("mentor_id", usuario["id"]).execute()
    flash("Solicitação recusada.", "aviso")
    return redirect(url_for("mentor.dashboard"))


@mentor_bp.route("/perfil", methods=["GET", "POST"])
def perfil():
    usuario = _u()
    if not usuario:
        return redirect(url_for("auth.login"))
    sb = get_supabase()
    mentor_id = usuario["id"]

    if request.method == "POST":
        dados = request.form
        sb.table("usuarios").update({
            "nome": dados.get("nome"),
            "telefone": dados.get("telefone"),
            "cidade": dados.get("cidade"),
            "estado": dados.get("estado"),
            "bio": dados.get("bio"),
        }).eq("id", mentor_id).execute()

        habs = request.form.getlist("habilidades")
        sb.table("usuario_habilidades").delete().eq("usuario_id", mentor_id).execute()
        for hid in habs:
            sb.table("usuario_habilidades").insert({"usuario_id": mentor_id, "habilidade_id": int(hid), "nivel": "intermediario"}).execute()

        session["usuario"]["nome"] = dados.get("nome")
        flash("Perfil atualizado!", "sucesso")
        return redirect(url_for("mentor.perfil"))

    mentor = sb.table("usuarios").select("*").eq("id", mentor_id).single().execute().data
    habilidades_all = sb.table("habilidades").select("*").order("categoria").execute().data or []
    ids_mentor = {h["habilidade_id"] for h in (sb.table("usuario_habilidades").select("habilidade_id").eq("usuario_id", mentor_id).execute()).data or []}

    return render_template("mentors/perfil.html", usuario=usuario, mentor=mentor, habilidades_all=habilidades_all, ids_mentor=ids_mentor)


@mentor_bp.route("/")
def lista():
    sb = get_supabase()
    try:
        mentores = sb.table("vw_ranking_mentores").select("*").execute().data or []
    except Exception:
        mentores = sb.table("usuarios").select("id,nome,bio,cidade,estado").eq("tipo","mentor").eq("ativo",True).execute().data or []
    usuario = _u()
    return render_template("mentors/lista.html", mentores=mentores, usuario=usuario)
