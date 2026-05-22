"""
MentoriaConecta - Rotas Administrativas
Dashboard, relatórios, gestão de usuários
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from app.utils.supabase_client import get_supabase

admin_bp = Blueprint("admin", __name__)


def _requer_admin():
    u = session.get("usuario")
    if not u or u.get("tipo") != "admin":
        return False
    return True


@admin_bp.route("/dashboard")
def dashboard():
    if not _requer_admin():
        return redirect(url_for("auth.login"))

    sb = get_supabase()
    usuario = session.get("usuario")

    # Estatísticas gerais
    total_mentores = (sb.table("usuarios").select("id", count="exact").eq("tipo", "mentor").execute()).count or 0
    total_alunos = (sb.table("usuarios").select("id", count="exact").eq("tipo", "aluno").execute()).count or 0
    total_mentorias = (sb.table("mentorias").select("id", count="exact").execute()).count or 0
    total_sessoes = (sb.table("sessoes").select("id", count="exact").eq("status", "realizada").execute()).count or 0

    # Mentorias recentes
    recentes = (sb.table("mentorias")
                .select("*, mentor:mentor_id(nome), aluno:aluno_id(nome)")
                .order("criado_em", desc=True)
                .limit(10)
                .execute()).data or []

    # Todos os usuários
    usuarios = (sb.table("usuarios")
                .select("id, nome, email, tipo, ativo, criado_em")
                .order("criado_em", desc=True)
                .execute()).data or []

    return render_template(
        "dashboard/admin_dashboard.html",
        usuario=usuario,
        stats={
            "mentores": total_mentores,
            "alunos": total_alunos,
            "mentorias": total_mentorias,
            "sessoes": total_sessoes,
        },
        mentorias_recentes=recentes,
        usuarios=usuarios,
    )


@admin_bp.route("/usuarios/<usuario_id>/toggle-ativo", methods=["POST"])
def toggle_ativo(usuario_id):
    if not _requer_admin():
        return jsonify({"erro": "Acesso negado"}), 403

    sb = get_supabase()
    atual = sb.table("usuarios").select("ativo").eq("id", usuario_id).single().execute().data
    novo_estado = not atual["ativo"]
    sb.table("usuarios").update({"ativo": novo_estado}).eq("id", usuario_id).execute()
    flash(f"Usuário {'ativado' if novo_estado else 'desativado'}.", "sucesso")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/mentorias/<mentoria_id>/aceitar", methods=["POST"])
def aceitar_mentoria(mentoria_id):
    if not _requer_admin():
        return jsonify({"erro": "Acesso negado"}), 403

    sb = get_supabase()
    sb.table("mentorias").update({"status": "ativa"}).eq("id", mentoria_id).execute()
    flash("Mentoria ativada.", "sucesso")
    return redirect(url_for("admin.dashboard"))


# ── API de Relatórios ─────────────────────────────────────────

@admin_bp.route("/api/relatorio")
def api_relatorio():
    """Dados do dashboard em JSON para gráficos."""
    if not _requer_admin():
        return jsonify({"erro": "Acesso negado"}), 403

    sb = get_supabase()

    # Mentorias por status
    mentorias_status = {}
    for status in ("pendente", "ativa", "concluida", "cancelada"):
        c = (sb.table("mentorias").select("id", count="exact").eq("status", status).execute()).count or 0
        mentorias_status[status] = c

    # Top mentores por avaliação
    top_mentores = sb.table("vw_ranking_mentores").select("nome, media_avaliacao, total_sessoes").limit(5).execute().data or []

    return jsonify({
        "mentorias_por_status": mentorias_status,
        "top_mentores": top_mentores,
    })
