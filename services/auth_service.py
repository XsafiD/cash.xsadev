"""services/auth_service.py — Autentikasi owner."""
from typing import Optional

from models import db
from models.user import User

USERNAME_PATTERN_MIN = 3
USERNAME_PATTERN_MAX = 50


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
