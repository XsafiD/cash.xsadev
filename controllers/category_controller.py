"""controllers/category_controller.py — Blueprint ``category_bp``.

Routes:
  - GET      /category/               — daftar kategori
  - GET/POST /category/create         — tambah kategori
  - GET/POST /category/<id>/edit      — edit kategori
  - POST     /category/<id>/delete    — hapus (soft) kategori
"""
from flask import (
    Blueprint, abort, flash, redirect, render_template, request, session, url_for,
)
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField
from wtforms.validators import DataRequired, Length

from controllers.decorators import login_required
from services.category_service import CategoryService

category_bp = Blueprint("category", __name__, url_prefix="/category")
_category_service = CategoryService()

KIND_LABELS = {"income": "Pemasukan", "expense": "Pengeluaran"}


class CategoryForm(FlaskForm):
    name = StringField(
        "Nama Kategori",
        validators=[
            DataRequired(message="Nama kategori wajib diisi"),
            Length(max=100, message="Nama maksimal 100 karakter"),
        ],
    )
    kind = SelectField(
        "Jenis",
        choices=[(key, label) for key, label in KIND_LABELS.items()],
        validators=[DataRequired(message="Jenis wajib dipilih")],
    )


class ConfirmForm(FlaskForm):
    pass


@category_bp.route("/")
@login_required
def index():
    kind = request.args.get("kind") or None
    try:
        categories = _category_service.get_all(session["user_id"], kind)
        error = None
    except ValueError as err:
        categories, error = [], str(err)
    if error:
        flash(error, "error")
    return render_template(
        "category/list.html",
        categories=categories,
        kind_labels=KIND_LABELS,
        active_kind=kind,
    )


@category_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    form = CategoryForm()
    if form.validate_on_submit():
        try:
            category = _category_service.create(
                session["user_id"], form.name.data, form.kind.data
            )
            flash(f"Kategori '{category.name}' berhasil dibuat.", "success")
            return redirect(url_for("category.index"))
        except ValueError as err:
            flash(str(err), "error")
    return render_template("category/form.html", form=form, mode="create")


@category_bp.route("/<category_id>/edit", methods=["GET", "POST"])
@login_required
def edit(category_id: str):
    category = _category_service.get_by_id(session["user_id"], category_id)
    if category is None:
        abort(404)

    form = CategoryForm(name=category.name, kind=category.kind)
    if form.validate_on_submit():
        try:
            _category_service.update(
                session["user_id"], category_id, form.name.data, form.kind.data
            )
            flash("Kategori berhasil diperbarui.", "success")
            return redirect(url_for("category.index"))
        except ValueError as err:
            flash(str(err), "error")
    return render_template(
        "category/form.html", form=form, mode="edit", category=category
    )


@category_bp.route("/<category_id>/delete", methods=["POST"])
@login_required
def delete(category_id: str):
    form = ConfirmForm()
    if form.validate_on_submit():
        try:
            _category_service.delete(session["user_id"], category_id)
            flash("Kategori berhasil dihapus.", "success")
        except ValueError as err:
            flash(str(err), "error")
    return redirect(url_for("category.index"))
