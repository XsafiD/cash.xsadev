"""controllers/account_controller.py — Blueprint ``account_bp``.

Routes:
  - GET      /account/                — daftar akun
  - GET/POST /account/create          — tambah akun
  - GET/POST /account/<id>/edit       — edit akun
  - POST     /account/<id>/delete     — hapus (soft) akun
"""
from flask import (
    Blueprint, abort, flash, redirect, render_template, url_for,
)
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField
from wtforms.validators import DataRequired, Length

from controllers.decorators import login_required
from services.account_service import AccountService

account_bp = Blueprint("account", __name__, url_prefix="/account")
_account_service = AccountService()

TYPE_LABELS = {"cash": "Tunai", "bank": "Bank", "ewallet": "E-Wallet"}


class AccountForm(FlaskForm):
    name = StringField(
        "Nama Akun",
        validators=[
            DataRequired(message="Nama akun wajib diisi"),
            Length(max=100, message="Nama maksimal 100 karakter"),
        ],
    )
    type = SelectField(
        "Tipe",
        choices=[(key, label) for key, label in TYPE_LABELS.items()],
        validators=[DataRequired(message="Tipe wajib dipilih")],
    )


class ConfirmForm(FlaskForm):
    pass


@account_bp.route("/")
@login_required
def index():
    from flask import session

    accounts = _account_service.get_all(session["user_id"])
    return render_template(
        "account/list.html",
        accounts=accounts,
        total=_account_service.total_balance(session["user_id"]),
        type_labels=TYPE_LABELS,
    )


@account_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    from flask import session

    form = AccountForm()
    if form.validate_on_submit():
        try:
            account = _account_service.create(
                session["user_id"], form.name.data, form.type.data
            )
            flash(f"Akun '{account.name}' berhasil dibuat.", "success")
            return redirect(url_for("account.index"))
        except ValueError as err:
            flash(str(err), "error")
    return render_template("account/form.html", form=form, mode="create")


@account_bp.route("/<account_id>/edit", methods=["GET", "POST"])
@login_required
def edit(account_id: str):
    from flask import session

    account = _account_service.get_by_id(session["user_id"], account_id)
    if account is None:
        abort(404)

    form = AccountForm(name=account.name, type=account.type)
    if form.validate_on_submit():
        try:
            _account_service.update(
                session["user_id"], account_id, form.name.data, form.type.data
            )
            flash("Akun berhasil diperbarui.", "success")
            return redirect(url_for("account.index"))
        except ValueError as err:
            flash(str(err), "error")
    return render_template(
        "account/form.html", form=form, mode="edit", account=account
    )


@account_bp.route("/<account_id>/delete", methods=["POST"])
@login_required
def delete(account_id: str):
    from flask import session

    form = ConfirmForm()
    if form.validate_on_submit():
        try:
            _account_service.delete(session["user_id"], account_id)
            flash("Akun berhasil dihapus.", "success")
        except ValueError as err:
            flash(str(err), "error")
    return redirect(url_for("account.index"))
