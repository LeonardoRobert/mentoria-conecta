"""
MentoriaConecta - Rotas do Aluno
"""
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from app.utils.auth import recomendar_mentores
from app.utils.supabase_client import get_supabase

aluno_bp = Blueprint("aluno", __name__)

def _u():
    return session.get("usuario")


@aluno_bp.route("/dashboard")
def dashboard():
    usuario = _u()
    if not usuario:
        return redirect(url_for("auth.login"))

    sb = get_supabase()
    aluno_id = usuario["id"]

    mentorias = (sb.table("mentorias")
                 .select("*, mentor:mentor_id(nome, email, bio, foto_url)")
                 .eq("aluno_id", aluno_id)
                 .execute()).data or []

    # Sessões disponíveis dos mentores ativos
    sessoes_disponiveis = []
    ids_inscritos = set()

    ativos = [m for m in mentorias if m["status"] == "ativa"]
    for m in ativos:
        ss = (sb.table("sessoes").select("*").eq("mentoria_id", m["id"]).eq("status","agendada").execute()).data or []
        for s in ss:
            count = (sb.table("inscricoes_sessao").select("id", count="exact").eq("sessao_id", s["id"]).neq("status","cancelado").execute()).count or 0
            s["inscritos"] = count
            s["vagas_livres"] = (s.get("vagas_total") or 10) - count
            s["mentor_nome"] = m["mentor"]["nome"] if m.get("mentor") else "—"
            s["mentoria_id"] = m["id"]
            # Verifica se já está inscrito
            insc = (sb.table("inscricoes_sessao").select("id").eq("sessao_id", s["id"]).eq("aluno_id", aluno_id).execute()).data
            s["ja_inscrito"] = bool(insc)
            if insc:
                ids_inscritos.add(s["id"])
            sessoes_disponiveis.append(s)

    sessoes_disponiveis.sort(key=lambda x: x["data_hora"])

    # Recomendações apenas se não tem mentor ativo
    recomendacoes = []
    if not ativos:
        try:
            recomendacoes = recomendar_mentores(aluno_id, limite=3)
        except Exception:
            recomendacoes = []

    # IDs de mentores já solicitados
    ids_solicitados = {m["mentor_id"] for m in mentorias}

    return render_template("dashboard/aluno_dashboard.html",
        usuario=usuario,
        mentorias=mentorias,
        sessoes_disponiveis=sessoes_disponiveis,
        recomendacoes=recomendacoes,
        ids_solicitados=ids_solicitados,
        stats={"total_mentorias": len(ativos), "total_sessoes": len(ids_inscritos)})


@aluno_bp.route("/solicitar-mentoria/<mentor_id>", methods=["POST"])
def solicitar_mentoria(mentor_id):
    usuario = _u()
    if not usuario or usuario["tipo"] != "aluno":
        return redirect(url_for("auth.login"))

    sb = get_supabase()
    aluno_id = usuario["id"]

    existe = (sb.table("mentorias").select("id").eq("mentor_id", mentor_id).eq("aluno_id", aluno_id).execute()).data
    if existe:
        flash("Você já possui uma solicitação com este mentor.", "aviso")
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


@aluno_bp.route("/encontrar-mentor")
def encontrar_mentor():
    usuario = _u()
    if not usuario:
        return redirect(url_for("auth.login"))

    sb = get_supabase()
    aluno_id = usuario["id"]

    try:
        mentores = recomendar_mentores(aluno_id, limite=10)
    except Exception:
        mentores = sb.table("usuarios").select("id,nome,bio,cidade,estado").eq("tipo","mentor").eq("ativo",True).execute().data or []
        for m in mentores:
            m["compatibilidade"] = 0
            m["score"] = 0

    ids_solicitados = {m["mentor_id"] for m in (sb.table("mentorias").select("mentor_id").eq("aluno_id", aluno_id).execute()).data or []}

    return render_template("students/encontrar_mentor.html",
        usuario=usuario, mentores=mentores, ids_solicitados=ids_solicitados)


@aluno_bp.route("/perfil", methods=["GET", "POST"])
def perfil():
    usuario = _u()
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

        habs = request.form.getlist("habilidades")
        sb.table("usuario_habilidades").delete().eq("usuario_id", aluno_id).execute()
        for hid in habs:
            sb.table("usuario_habilidades").insert({"usuario_id": aluno_id, "habilidade_id": int(hid), "nivel": "basico"}).execute()

        session["usuario"]["nome"] = dados.get("nome")
        flash("Perfil atualizado!", "sucesso")
        return redirect(url_for("aluno.perfil"))

    aluno = sb.table("usuarios").select("*").eq("id", aluno_id).single().execute().data
    habilidades_all = sb.table("habilidades").select("*").order("categoria").execute().data or []
    ids_aluno = {h["habilidade_id"] for h in (sb.table("usuario_habilidades").select("habilidade_id").eq("usuario_id", aluno_id).execute()).data or []}

    return render_template("students/perfil.html", usuario=usuario, aluno=aluno, habilidades_all=habilidades_all, ids_aluno=ids_aluno)
