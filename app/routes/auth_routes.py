"""
MentoriaConecta - Rotas de Autenticação
Login, Registro e Logout com JWT
"""
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, flash
from app.utils.auth import hash_senha, verificar_senha, gerar_token, decodificar_token
from app.utils.supabase_client import get_supabase

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Login com email e senha. Gera token JWT e salva na sessão."""
    if request.method == "GET":
        return render_template("auth/login.html")

    dados = request.form if request.form else request.get_json()
    email = dados.get("email", "").strip().lower()
    senha = dados.get("senha", "")

    if not email or not senha:
        flash("Preencha email e senha.", "erro")
        return render_template("auth/login.html", erro="Preencha email e senha.")

    sb = get_supabase()
    resp = sb.table("usuarios").select("*").eq("email", email).eq("ativo", True).execute()

    if not resp.data:
        flash("Credenciais inválidas.", "erro")
        return render_template("auth/login.html", erro="Email ou senha incorretos.")

    usuario = resp.data[0]

    if not verificar_senha(senha, usuario["senha_hash"]):
        flash("Credenciais inválidas.", "erro")
        return render_template("auth/login.html", erro="Email ou senha incorretos.")

    token = gerar_token(usuario["id"], usuario["tipo"])

    # Salva na sessão Flask (para navegação por páginas)
    session["token"] = token
    session["usuario"] = {
        "id": usuario["id"],
        "nome": usuario["nome"],
        "email": usuario["email"],
        "tipo": usuario["tipo"],
        "foto_url": usuario.get("foto_url"),
    }

    return redirect(url_for("main.dashboard"))


@auth_bp.route("/registro", methods=["GET", "POST"])
def registro():
    """Cadastro de novo usuário (mentor ou aluno)."""
    sb = get_supabase()

    if request.method == "GET":
        habilidades = sb.table("habilidades").select("*").order("categoria").execute().data or []
        return render_template("auth/registro.html", habilidades=habilidades)

    dados = request.form if request.form else request.get_json()
    campos_obrigatorios = ["nome", "email", "senha", "tipo"]
    for campo in campos_obrigatorios:
        if not dados.get(campo):
            habilidades = sb.table("habilidades").select("*").order("categoria").execute().data or []
            return render_template("auth/registro.html", erro=f"Campo '{campo}' obrigatório.", habilidades=habilidades)

    tipo = dados["tipo"]
    if tipo not in ("mentor", "aluno"):
        habilidades = sb.table("habilidades").select("*").order("categoria").execute().data or []
        return render_template("auth/registro.html", erro="Tipo deve ser 'mentor' ou 'aluno'.", habilidades=habilidades)

    email = dados["email"].strip().lower()
    sb = get_supabase()

    # Verifica duplicidade
    existe = sb.table("usuarios").select("id").eq("email", email).execute()
    if existe.data:
        return render_template("auth/registro.html", erro="Email já cadastrado.")

    novo_usuario = {
        "nome": dados["nome"].strip(),
        "email": email,
        "senha_hash": hash_senha(dados["senha"]),
        "tipo": tipo,
        "telefone": dados.get("telefone", ""),
        "cidade": dados.get("cidade", ""),
        "estado": dados.get("estado", ""),
        "bio": dados.get("bio", ""),
    }

    resp = sb.table("usuarios").insert(novo_usuario).execute()
    if not resp.data:
        habilidades = sb.table("habilidades").select("*").order("categoria").execute().data or []
        return render_template("auth/registro.html", erro="Erro ao criar conta. Tente novamente.", habilidades=habilidades)

    # Salva habilidades selecionadas no cadastro
    novo_id = resp.data[0]["id"]
    habilidades_ids = request.form.getlist("habilidades")
    nivel = "intermediario" if tipo == "mentor" else "basico"
    for hid in habilidades_ids:
        try:
            sb.table("usuario_habilidades").insert({
                "usuario_id": novo_id,
                "habilidade_id": int(hid),
                "nivel": nivel,
            }).execute()
        except Exception:
            pass

    flash("Conta criada com sucesso! Faça login.", "sucesso")
    return redirect(url_for("auth.login"))


@auth_bp.route("/logout")
def logout():
    """Remove sessão do usuário."""
    session.clear()
    flash("Até logo!", "sucesso")
    return redirect(url_for("main.index"))


# ── API Endpoints (para uso com fetch/axios) ──────────────────

@auth_bp.route("/api/login", methods=["POST"])
def api_login():
    """Endpoint REST para login. Retorna token JWT em JSON."""
    dados = request.get_json()
    email = dados.get("email", "").strip().lower()
    senha = dados.get("senha", "")

    sb = get_supabase()
    resp = sb.table("usuarios").select("*").eq("email", email).eq("ativo", True).execute()

    if not resp.data or not verificar_senha(senha, resp.data[0]["senha_hash"]):
        return jsonify({"erro": "Credenciais inválidas"}), 401

    usuario = resp.data[0]
    token = gerar_token(usuario["id"], usuario["tipo"])
    return jsonify({"token": token, "tipo": usuario["tipo"], "nome": usuario["nome"]}), 200


@auth_bp.route("/api/verificar", methods=["GET"])
def api_verificar():
    """Verifica validade de um token JWT."""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    dados = decodificar_token(token)
    if not dados:
        return jsonify({"valido": False}), 401
    return jsonify({"valido": True, "usuario_id": dados["sub"], "tipo": dados["tipo"]}), 200
