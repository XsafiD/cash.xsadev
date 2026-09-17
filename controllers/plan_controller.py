"""controllers/plan_controller.py — Blueprint ``plan_bp``.

Halaman kalkulator perencanaan — TIDAK menyentuh ledger/saldo.

Routes:
  - GET  /plan/                  — kalkulator bulan berjalan
  - POST /plan/gross             — simpan uang kotor bulanan
  - POST /plan/item/create       — tambah item kebutuhan
  - POST /plan/item/<id>/update  — ubah item kebutuhan
  - POST /plan/item/<id>/delete  — hapus item kebutuhan
"""
from flask import (
    Blueprint, flash, redirect, render_template, request, session, url_for,
)
from flask_wtf import FlaskForm
from wtforms import BooleanField, DecimalField, StringField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

from controllers.decorators import login_required
from services.plan_service import PlanService
from services.report_service import current_month

plan_bp = Blueprint("plan", __name__, url_prefix="/plan")
_plan_service = PlanService()


class PlanItemForm(FlaskForm):
    name = StringField(
        "Nama Kebutuhan",
        validators=[
            DataRequired(message="Nama kebutuhan wajib diisi"),
            Length(max=100, message="Nama maksimal 100 karakter"),
        ],
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
    note = StringField(
        "Catatan",
        validators=[Optional(), Length(max=255, message="Catatan maksimal 255 karakter")],
    )
    is_active = BooleanField("Aktif dihitung", default=True)


class GrossForm(FlaskForm):
    gross_income = DecimalField(
        "Uang Kotor Bulanan",
        places=2,
        render_kw={
            "type": "text",
            "inputmode": "numeric",
            "autocomplete": "off",
            "data_money": "true",
        },
        validators=[
            DataRequired(message="Uang kotor wajib diisi"),
            NumberRange(min=0, message="Uang kotor tidak boleh negatif"),
        ],
    )


class ConfirmForm(FlaskForm):
    pass


def _render_index(period: str):
    user_id = session["user_id"]
    summary = _plan_service.summary(user_id, period)
    items = _plan_service.list_items(user_id)
    edit_forms = {item.id: PlanItemForm(obj=item) for item in items}
    return render_template(
        "plan/index.html",
        period=period,
        summary=summary,
        gross_form=GrossForm(gross_income=summary["gross_income"]),
        item_form=PlanItemForm(),
        items=items,
        edit_forms=edit_forms,
        periods=_plan_service.list_periods(user_id),
        default_period=current_month(),
    )


@plan_bp.route("/")
@login_required
def index():
    period = request.args.get("period") or current_month()
    return _render_index(period)


@plan_bp.route("/gross", methods=["POST"])
@login_required
def set_gross():
    period = request.form.get("period") or current_month()
    form = GrossForm()
    if form.validate_on_submit():
        try:
            _plan_service.set_gross_income(
                session["user_id"], period, form.gross_income.data
            )
            flash("Uang kotor bulanan disimpan.", "success")
        except ValueError as err:
            flash(str(err), "error")
    return redirect(url_for("plan.index", period=period))


@plan_bp.route("/item/create", methods=["POST"])
@login_required
def create_item():
    period = request.form.get("period") or current_month()
    form = PlanItemForm()
    if form.validate_on_submit():
        try:
            _plan_service.create_item(
                session["user_id"], form.name.data, form.amount.data, form.note.data
            )
            flash("Item kebutuhan ditambahkan.", "success")
        except ValueError as err:
            flash(str(err), "error")
    return redirect(url_for("plan.index", period=period))


@plan_bp.route("/item/<item_id>/update", methods=["POST"])
@login_required
def update_item(item_id: str):
    period = request.form.get("period") or current_month()
    form = PlanItemForm()
    if form.validate_on_submit():
        try:
            _plan_service.update_item(
                session["user_id"], item_id, form.name.data,
                form.amount.data, form.note.data, form.is_active.data,
            )
            flash("Item kebutuhan diperbarui.", "success")
        except ValueError as err:
            flash(str(err), "error")
    return redirect(url_for("plan.index", period=period))


@plan_bp.route("/item/<item_id>/delete", methods=["POST"])
@login_required
def delete_item(item_id: str):
    period = request.form.get("period") or current_month()
    form = ConfirmForm()
    if form.validate_on_submit():
        try:
            _plan_service.delete_item(session["user_id"], item_id)
            flash("Item kebutuhan dihapus.", "success")
        except ValueError as err:
            flash(str(err), "error")
    return redirect(url_for("plan.index", period=period))
