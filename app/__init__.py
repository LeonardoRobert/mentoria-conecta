"""
MentoriaConecta - Factory do Flask App
"""
from flask import Flask
from config import config
from dotenv import load_dotenv
import os

load_dotenv()


def create_app(config_name: str = "default") -> Flask:
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(config[config_name])
    app.secret_key = app.config["SECRET_KEY"]

    # ── Blueprints ──────────────────────────────────────────
    from app.routes.auth_routes import auth_bp
    from app.routes.mentor_routes import mentor_bp
    from app.routes.aluno_routes import aluno_bp
    from app.routes.sessao_routes import sessao_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.main_routes import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(mentor_bp, url_prefix="/mentores")
    app.register_blueprint(aluno_bp, url_prefix="/alunos")
    app.register_blueprint(sessao_bp, url_prefix="/sessoes")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    return app
