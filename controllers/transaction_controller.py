"""controllers/transaction_controller.py — Blueprint ``transaction_bp``.

Routes:
  - GET      /transaction/            — daftar transaksi (filter: type, month, account)
  - GET/POST /transaction/create      — catat transaksi
  - POST     /transaction/<id>/delete — hapus + reversal saldo
"""
from datetime import date

from flask import (
    Blueprint, abort, flash, redirect, render_template, request, session, url_for,
)
from flask_wtf import FlaskForm
from wtforms import DateField, DecimalField, SelectField, StringField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

from controllers.decorators import login_required
from services.account_service import AccountService
from services.category_service import CategoryService
from services.report_service import current_month
from services.transaction_service import TransactionService

transaction_bp = Blueprint("transaction", __name__, url_prefix="/transaction")
_transaction_service = TransactionService()
_account_service = AccountService()
_category_service = CategoryService()

TYPE_LABELS = {"income": "Pemasukan", "expense": "Pengeluaran", "transfer": "Transfer"}
ACCOUNT_TYPE_LABELS = {"cash": "Tunai", "bank": "Bank", "ewallet": "E-Wallet"}
KIND_LABELS = {"income": "Pemasukan", "expense": "Pengeluaran"}


class TransactionForm(FlaskForm):
    type = SelectField(
        "Tipe",
        choices=[(key, label) for key, label in TYPE_LABELS.items()],
        validators=[DataRequired(message="Tipe wajib dipilih")],
    )
    amount = DecimalField(
        "Nominal",
        places=2,
        render_kw={
            "type": "text",
            "inputmode": "numeric",
            "autocomplete": "off",
            "data_money": "true",
        },
        validators=[
            DataRequired(message="Nominal wajib diisi"),
            NumberRange(min=0.01, message="Nominal harus lebih dari 0"),
        ],
    )
    account_id = SelectField(
        "Akun",
        choices=[],
        validators=[DataRequired(message="Akun wajib dipilih")],
        validate_choice=False,
    )
    account_to_id = SelectField(
        "Akun Tujuan",
        choices=[],
        validators=[Optional()],
        validate_choice=False,
    )
    category_id = SelectField(
        "Kategori",
        choices=[],
        validators=[Optional()],
        validate_choice=False,
    )
    occurred_on = DateField(
        "Tanggal",
        validators=[DataRequired(message="Tanggal wajib diisi")],
    )
    note = StringField(
        "Catatan",
        validators=[Optional(), Length(max=255, message="Catatan maksimal 255 karakter")],
    )


class ConfirmForm(FlaskForm):
    pass


def _populate_choices(form: TransactionForm, user_id: str) -> None:
    accounts = _account_service.get_all(user_id)
    account_choices = [
        (a.id, f"{a.name} · {ACCOUNT_TYPE_LABELS.get(a.type, a.type)}")
        for a in accounts
    ]
    form.account_id.choices = account_choices
    form.account_to_id.choices = [("", "—")] + account_choices

    categories = _category_service.get_all(user_id)
    form.category_id.choices = [("", "—")] + [
        (c.id, f"{c.name} ({KIND_LABELS.get(c.kind, c.kind)})") for c in categories
    ]


@transaction_bp.route("/")
@login_required
def index():
    filters = {
        key: value
        for key, value in {
            "type": request.args.get("type"),
            "month": request.args.get("month"),
            "account_id": request.args.get("account_id"),
        }.items()
        if value
    }
    try:
        transactions = _transaction_service.get_all(session["user_id"], filters)
    except ValueError as err:
        flash(str(err), "error")
        transactions = []
    return render_template(
        "transaction/list.html",
        transactions=transactions,
        accounts=_account_service.get_all(session["user_id"]),
        type_labels=TYPE_LABELS,
        filters=filters,
        current_month=current_month(),
    )


@transaction_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    form = TransactionForm(occurred_on=date.today())
    if form.validate_on_submit():
        try:
            _transaction_service.create(
                user_id=session["user_id"],
                type=form.type.data,
                amount=form.amount.data,
                account_id=form.account_id.data,
                category_id=form.category_id.data or None,
                account_to_id=form.account_to_id.data or None,
                note=form.note.data,
                occurred_on=form.occurred_on.data,
            )
            flash("Transaksi berhasil dicatat.", "success")
            return redirect(url_for("transaction.index"))
        except ValueError as err:
            flash(str(err), "error")
    _populate_choices(form, session["user_id"])
    return render_template("transaction/form.html", form=form)


@transaction_bp.route("/<transaction_id>/delete", methods=["POST"])
@login_required
def delete(transaction_id: str):
    form = ConfirmForm()
    if form.validate_on_submit():
        try:
            _transaction_service.delete(session["user_id"], transaction_id)
            flash("Transaksi dihapus dan saldo dikembalikan.", "success")
        except ValueError as err:
            flash(str(err), "error")
    return redirect(url_for("transaction.index"))
