"""controllers/dashboard_controller.py — Blueprint ``dashboard_bp``.

Routes:
  - GET / — ringkasan bulan berjalan (proteksi: login)
"""
from flask import Blueprint, render_template, request, session

from controllers.decorators import login_required
from services.report_service import ReportService, current_month

dashboard_bp = Blueprint("dashboard", __name__)
_report_service = ReportService()


@dashboard_bp.route("/")
@login_required
def index():
    month = request.args.get("month") or current_month()
    data = _report_service.dashboard(session["user_id"], month)
    return render_template("dashboard/index.html", **data)
