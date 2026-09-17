"""models/transaction.py — Model Transaction (mutasi keuangan).

Satu row merepresentasikan satu event:
  - income   : uang masuk ke ``account``
  - expense  : uang keluar dari ``account``
  - transfer : perpindahan saldo ``account`` → ``account_to``
"""
from datetime import date

from models import db, generate_uuid, utcnow

VALID_TRANSACTION_TYPES = ("income", "expense", "transfer")


class Transaction(db.Model):
    __tablename__ = "transaction"

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(
        db.String(36), db.ForeignKey("user.id"), nullable=False, index=True
    )
    type = db.Column(db.String(10), nullable=False, index=True)
    amount = db.Column(db.Numeric(18, 2), nullable=False)

    account_id = db.Column(
        db.String(36), db.ForeignKey("account.id"), nullable=False, index=True
    )
    account_to_id = db.Column(
        db.String(36), db.ForeignKey("account.id"), nullable=True
    )
    category_id = db.Column(
        db.String(36), db.ForeignKey("category.id"), nullable=True, index=True
    )

    note = db.Column(db.String(255), nullable=True)
    occurred_on = db.Column(db.Date, nullable=False, default=date.today, index=True)

    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    # ── Relationship (forward: eager karena selalu dirender) ──
    account = db.relationship(
        "Account",
        foreign_keys=[account_id],
        lazy="joined",
        backref=db.backref("transaction_list", lazy=True),
    )
    account_to = db.relationship(
        "Account",
        foreign_keys=[account_to_id],
        lazy="joined",
        backref=db.backref("transfer_in_list", lazy=True),
    )
    category = db.relationship(
        "Category",
        lazy="joined",
        backref=db.backref("transaction_list", lazy=True),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "amount": float(self.amount or 0),
            "account_id": self.account_id,
            "account_to_id": self.account_to_id,
            "category_id": self.category_id,
            "note": self.note,
            "occurred_on": self.occurred_on.isoformat() if self.occurred_on else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<Transaction {self.type} {self.amount} on {self.occurred_on}>"
