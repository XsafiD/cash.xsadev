"""models/user.py — Model User (Actor / pemilik keuangan)."""
from werkzeug.security import check_password_hash, generate_password_hash

from models import db, generate_uuid, utcnow

MIN_PASSWORD_LENGTH = 6


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    # ── Kredensial ──
    def set_password(self, password_plain: str) -> None:
        if not password_plain or len(password_plain) < MIN_PASSWORD_LENGTH:
            raise ValueError(
                f"Password minimal {MIN_PASSWORD_LENGTH} karakter"
            )
        self.password_hash = generate_password_hash(password_plain)

    def check_password(self, password_plain: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password_plain)

    # ── Serialisasi ──
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<User {self.username}>"
