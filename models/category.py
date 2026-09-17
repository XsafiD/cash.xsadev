"""models/category.py — Model Category (kategori pemasukan/pengeluaran)."""
from models import db, generate_uuid, utcnow

VALID_CATEGORY_KINDS = ("income", "expense")


class Category(db.Model):
    __tablename__ = "category"

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(
        db.String(36), db.ForeignKey("user.id"), nullable=False, index=True
    )
    name = db.Column(db.String(100), nullable=False)
    kind = db.Column(db.String(10), nullable=False, default="expense")

    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "kind": self.kind,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<Category {self.name} ({self.kind})>"
