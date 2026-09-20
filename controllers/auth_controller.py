"""controllers/auth_controller.py — Blueprint ``auth_bp``.

Routes:
  - GET/POST /auth/login  — masuk
  - POST     /auth/logout — keluar (CSRF-only)
"""
from flask import Blueprint, flash, redirect, render_template, session, url_for
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField
from wtforms.validators import DataRequired, Length

from services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
_auth_service = AuthService()


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
