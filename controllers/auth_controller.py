"""controllers/auth_controller.py — Blueprint ``auth_bp``.

Routes:
  - GET/POST /auth/setup  — buat owner pertama (sekali pakai, mode setup)
  - GET/POST /auth/login  — masuk
  - POST     /auth/logout — keluar (CSRF-only)
"""
import hmac

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    session,
    url_for,
)
from flask_wtf import FlaskForm
from sqlalchemy.exc import SQLAlchemyError
from wtforms import PasswordField, StringField
from wtforms.validators import DataRequired, EqualTo, Length, Optional

from controllers.decorators import setup_only
from models.user import MIN_PASSWORD_LENGTH
from services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
_auth_service = AuthService()


class SetupForm(FlaskForm):
    """Form owner pertama — hanya valid saat mode setup terbuka."""

    setup_token = StringField(
        "Token Setup",
        validators=[Optional(), Length(max=255)],
        render_kw={"autocomplete": "off"},
    )
    username = StringField(
        "Username",
        validators=[
            DataRequired(message="Username wajib diisi"),
            Length(min=3, max=50, message="Username 3-50 karakter"),
        ],
        render_kw={"autocomplete": "username", "autofocus": True},
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Password wajib diisi"),
            Length(
                min=MIN_PASSWORD_LENGTH,
                max=128,
                message=f"Password minimal {MIN_PASSWORD_LENGTH} karakter",
            ),
        ],
        render_kw={"autocomplete": "new-password"},
    )
    password_confirm = PasswordField(
        "Ulangi Password",
        validators=[
            DataRequired(message="Konfirmasi password wajib diisi"),
            EqualTo("password", message="Konfirmasi password tidak sama"),
        ],
        render_kw={"autocomplete": "new-password"},
    )


class LoginForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            DataRequired(message="Username wajib diisi"),
            Length(min=3, max=50, message="Username 3-50 karakter"),
        ],
        render_kw={"autocomplete": "username", "autofocus": True},
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(message="Password wajib diisi")],
        render_kw={"autocomplete": "current-password"},
    )


class ConfirmForm(FlaskForm):
    """Form kosong — hanya CSRF protection untuk aksi singkat."""
    pass


@auth_bp.route("/setup", methods=["GET", "POST"])
@setup_only
def setup():
    token_required = bool(current_app.config.get("SETUP_TOKEN"))
    form = SetupForm()

    if form.validate_on_submit():
        expected = current_app.config.get("SETUP_TOKEN") or ""
        if expected and not hmac.compare_digest(expected, form.setup_token.data or ""):
            flash("Token setup tidak valid.", "error")
        else:
            try:
                user = _auth_service.create_initial_owner(
                    form.username.data, form.password.data
                )
            except ValueError as err:
                flash(str(err), "error")
            except SQLAlchemyError:
                current_app.logger.exception("Setup gagal — database belum siap")
                flash(
                    "Database belum siap. Jalankan migrasi terlebih dahulu.",
                    "error",
                )
            else:
                session.clear()
                session["user_id"] = user.id
                session["role"] = "owner"
                session["nama"] = user.username
                session.permanent = True
                flash("Akun owner berhasil dibuat. Selamat datang!", "success")
                return redirect(url_for("dashboard.index"))

    return render_template("auth/setup.html", form=form, token_required=token_required)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = _auth_service.authenticate(form.username.data, form.password.data)
        if user is None:
            flash("Username atau password salah.", "error")
        else:
            session.clear()
            session["user_id"] = user.id
            session["role"] = "owner"
            session["nama"] = user.username
            session.permanent = True
            return redirect(url_for("dashboard.index"))
    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
def logout():
    form = ConfirmForm()
    if form.validate_on_submit():
        session.clear()
        flash("Anda telah keluar.", "success")
    return redirect(url_for("auth.login"))
