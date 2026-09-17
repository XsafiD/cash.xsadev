"""models/plan_item.py — Item kebutuhan bulanan (reusable, di luar ledger)."""
from decimal import Decimal

from models import db, generate_uuid, utcnow


class PlanItem(db.Model):
    __tablename__ = "plan_item"

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(
        db.String(36), db.ForeignKey("user.id"), nullable=False, index=True
    )
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(
        db.Numeric(18, 2), nullable=False, default=Decimal("0.00")
    )
    note = db.Column(db.String(255), nullable=True)
    position = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "amount": float(self.amount or 0),
            "note": self.note,
            "position": self.position,
            "is_active": self.is_active,
        }

    def __repr__(self) -> str:
        return f"<PlanItem {self.name} {self.amount} active={self.is_active}>"
