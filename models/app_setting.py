"""models/app_setting.py — Key-value setting aplikasi (marker setup, dst)."""
from models import db, utcnow


class AppSetting(db.Model):
    """Setting level aplikasi (bukan milik user).

    PK natural (`key`) — nilai tunggal per kunci. Dipakai antara lain sebagai
    marker permanen ``setup_completed_at`` agar mode setup tidak terbuka lagi
    walau seluruh user dihapus.
    """

    __tablename__ = "app_setting"

    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    # ── Serialisasi ──
    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<AppSetting {self.key}>"
