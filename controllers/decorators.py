"""controllers/decorators.py — Proteksi endpoint.

Session contract (di-set oleh AuthService.login):
    session['user_id'] : ID user (UUID)
    session['role']    : 'owner' | 'admin'
    session['nama']    : display name (username)
"""
from functools import wraps

from flask import abort, flash, redirect, session, url_for


def login_required(f):
    """Redirect ke /auth/login jika belum terautentikasi."""
    @wraps(f)
    def _wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Anda harus login terlebih dahulu.", "error")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return _wrapper


def admin_required(f):
    """Belum login → redirect; login tapi bukan admin → HTTP 403."""
    @wraps(f)
    def _wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Anda harus login terlebih dahulu.", "error")
            return redirect(url_for("auth.login"))
        if session.get("role") != "admin":
            abort(403)
        return f(*args, **kwargs)
    return _wrapper
