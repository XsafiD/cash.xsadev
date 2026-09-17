"""app.py — Application factory + error handler + CLI."""
import os

import click
from flask import Flask, jsonify, render_template, request

from config import Config


def _wants_json() -> bool:
    """Heuristik request mengharapkan JSON (API client) vs HTML (browser)."""
    best = request.accept_mimetypes.best_match(["application/json", "text/html"])
    return (
        best == "application/json"
        and request.accept_mimetypes[best] > request.accept_mimetypes["text/html"]
    )


def _register_error_handlers(app: Flask) -> None:
    """Error handler global — dual response JSON/HTML."""

    @app.errorhandler(404)
    def not_found(err):
        if _wants_json():
            return jsonify(status="error", error="not_found",
                           message="Resource tidak ditemukan"), 404
        return render_template("error.html", error_code=404,
                               error_title="Halaman Tidak Ditemukan",
                               error_message="Maaf, halaman tidak tersedia."), 404

    @app.errorhandler(403)
    def forbidden(err):
        if _wants_json():
            return jsonify(status="error", error="forbidden",
                           message="Akses ditolak"), 403
        return render_template("error.html", error_code=403,
                               error_title="Akses Ditolak",
                               error_message="Anda tidak punya izin."), 403

    @app.errorhandler(413)
    def too_large(err):
        if _wants_json():
            return jsonify(status="error", error="payload_too_large",
                           message="Upload melebihi batas"), 413
        return render_template("error.html", error_code=413,
                               error_title="File Terlalu Besar",
                               error_message="Ukuran melebihi batas upload."), 413

    @app.errorhandler(500)
    def server_error(err):
        app.logger.exception("Internal server error: %s", err)
        if _wants_json():
            return jsonify(status="error", error="internal_error",
                           message="Server error"), 500
        return render_template("error.html", error_code=500,
                               error_title="Kesalahan Server",
                               error_message="Terjadi kesalahan internal."), 500


def _register_template_filters(app: Flask) -> None:
    @app.template_filter("rupiah")
    def rupiah(value) -> str:
        """Format angka → 'Rp 1.234.567'."""
        try:
            amount = float(value or 0)
        except (TypeError, ValueError):
            amount = 0.0
        return "Rp {:,.0f}".format(amount).replace(",", ".")


def _register_cli(app: Flask) -> None:
    @app.cli.command("seed-owner")
    def seed_owner():
        """Buat akun owner awal dari OWNER_USERNAME/OWNER_PASSWORD."""
        from services.auth_service import AuthService

        username = os.environ.get("OWNER_USERNAME", "owner")
        password = os.environ.get("OWNER_PASSWORD", "gantipassword")
        user = AuthService().ensure_owner(username, password)
        click.echo(f"Owner '{user.username}' siap dipakai.")


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError(
            "SECRET_KEY wajib di-set untuk environment ini "
            "(lihat .env.example)."
        )

    from flask_migrate import Migrate
    from flask_wtf.csrf import CSRFProtect
    from models import db

    db.init_app(app)
    Migrate(app, db)
    CSRFProtect().init_app(app)

    from controllers import register_blueprints

    register_blueprints(app)

    _register_error_handlers(app)
    _register_template_filters(app)
    _register_cli(app)
    return app
