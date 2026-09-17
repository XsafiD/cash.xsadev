"""models/plan_period.py — Uang kotor per bulan (di luar ledger)."""
from decimal import Decimal

from models import db, generate_uuid, utcnow


class PlanPeriod(db.Model):
    __tablename__ = "plan_period"
    __table_args__ = (
        db.UniqueConstraint("user_id", "period", name="uq_plan_period_user_period"),
    )

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(
        db.String(36), db.ForeignKey("user.id"), nullable=False, index=True
    )
    period = db.Column(db.String(7), nullable=False, index=True)  # "YYYY-MM"
    gross_income = db.Column(
        db.Numeric(18, 2), nullable=False, default=Decimal("0.00")
    )

    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "period": self.period,
            "gross_income": float(self.gross_income or 0),
        }

    def __repr__(self) -> str:
        return f"<PlanPeriod {self.period} gross={self.gross_income}>"
