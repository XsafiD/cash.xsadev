"""services/auth_service.py — Autentikasi owner + bootstrap setup."""
from typing import Optional

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from models import db, utcnow
from models.app_setting import AppSetting
from models.user import User

USERNAME_PATTERN_MIN = 3
USERNAME_PATTERN_MAX = 50

# Marker permanen: begitu terisi, mode setup tertutup selamanya.
SETUP_MARKER_KEY = "setup_completed_at"


class AuthService:
    """Pintu masuk operasi autentikasi."""

    def get_by_id(self, user_id: str) -> Optional[User]:
        return db.session.get(User, user_id)

    def get_by_username(self, username: str) -> Optional[User]:
        return User.query.filter_by(username=(username or "").strip()).first()

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Return User bila kredensial cocok, else None."""
        user = self.get_by_username(username)
        if user is None or not password:
            return None
        if not user.check_password(password):
            return None
        return user

    def ensure_owner(self, username: str, password: str) -> User:
        """Buat owner bila belum ada (idempotent, untuk seeding)."""
        username = (username or "").strip()
        if len(username) < USERNAME_PATTERN_MIN or len(username) > USERNAME_PATTERN_MAX:
            raise ValueError(
                f"Username {USERNAME_PATTERN_MIN}-{USERNAME_PATTERN_MAX} karakter"
            )
        existing = self.get_by_username(username)
        if existing is not None:
            return existing
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    # ── Bootstrap setup (sekali pakai) ──
    def is_initialized(self) -> bool:
        """True bila setup tidak boleh dibuka lagi.

        Cek marker permanen dulu, lalu fallback ke keberadaan user (mendukung
        database lama yang sudah di-seed lewat CLI). DB belum siap → False.
        """
        try:
            if db.session.get(AppSetting, SETUP_MARKER_KEY) is not None:
                return True
            return db.session.query(User.id).first() is not None
        except SQLAlchemyError:
            return False

    def create_initial_owner(self, username: str, password: str) -> User:
        """Buat owner pertama + kunci marker setup secara atomik.

        Marker di-INSERT dalam transaction yang sama dengan user; unique PK
        pada ``app_setting`` menjamin hanya satu request yang menang saat
        beberapa worker gunicorn memproses POST bersamaan.

        Raises:
            ValueError: setup sudah tertutup, username tidak valid, atau
                username sudah dipakai.
        """
        if self.is_initialized():
            raise ValueError("Aplikasi sudah dikonfigurasi.")

        username = (username or "").strip()
        if len(username) < USERNAME_PATTERN_MIN or len(username) > USERNAME_PATTERN_MAX:
            raise ValueError(
                f"Username {USERNAME_PATTERN_MIN}-{USERNAME_PATTERN_MAX} karakter"
            )

        marker = AppSetting(key=SETUP_MARKER_KEY, value=utcnow().isoformat())
        db.session.add(marker)
        try:
            db.session.flush()  # klaim atomik; kalah balapan → IntegrityError
        except IntegrityError:
            db.session.rollback()
            raise ValueError("Aplikasi sudah dikonfigurasi.")

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ValueError("Username sudah dipakai.")
        return user
