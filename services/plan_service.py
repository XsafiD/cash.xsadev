"""services/plan_service.py — Kalkulator Perencanaan (di luar ledger)."""
import re
from decimal import Decimal, InvalidOperation
from typing import List, Optional

from sqlalchemy import func

from models import db
from models.plan_item import PlanItem
from models.plan_period import PlanPeriod

PERIOD_PATTERN = re.compile(r"^\d{4}-\d{2}$")


class PlanService:
    """Item kebutuhan reusable + uang kotor per bulan. Tidak menyentuh saldo."""

    # ── Item kebutuhan ──
    def list_items(self, user_id: str, active_only: bool = False) -> List[PlanItem]:
        query = PlanItem.query.filter(PlanItem.user_id == user_id)
        if active_only:
            query = query.filter(PlanItem.is_active.is_(True))
        return query.order_by(PlanItem.position.asc(), PlanItem.created_at.asc()).all()

    def get_item(self, user_id: str, item_id: str) -> Optional[PlanItem]:
        return PlanItem.query.filter(
            PlanItem.id == item_id, PlanItem.user_id == user_id
        ).first()

    def create_item(self, user_id: str, name: str, amount, note: str = None) -> PlanItem:
        name = (name or "").strip()
        if len(name) < 2:
            raise ValueError("Nama item minimal 2 karakter")
        max_pos = (
            db.session.query(func.coalesce(func.max(PlanItem.position), 0))
            .filter(PlanItem.user_id == user_id)
            .scalar()
        )
        item = PlanItem(
            user_id=user_id,
            name=name,
            amount=self._parse_amount(amount),
            note=(note or "").strip() or None,
            position=int(max_pos or 0) + 1,
        )
        db.session.add(item)
        db.session.commit()
        return item

    def update_item(self, user_id, item_id, name, amount, note=None,
                    is_active=None) -> PlanItem:
        item = self.get_item(user_id, item_id)
        if item is None:
            raise ValueError("Item tidak ditemukan")
        name = (name or "").strip()
        if len(name) < 2:
            raise ValueError("Nama item minimal 2 karakter")
        item.name = name
        item.amount = self._parse_amount(amount)
        item.note = (note or "").strip() or None
        if is_active is not None:
            item.is_active = bool(is_active)
        db.session.commit()
        return item

    def delete_item(self, user_id: str, item_id: str) -> None:
        item = self.get_item(user_id, item_id)
        if item is None:
            raise ValueError("Item tidak ditemukan")
        db.session.delete(item)
        db.session.commit()

    def total_needs(self, user_id: str) -> Decimal:
        total = (
            db.session.query(func.coalesce(func.sum(PlanItem.amount), 0))
            .filter(PlanItem.user_id == user_id, PlanItem.is_active.is_(True))
            .scalar()
        )
        return Decimal(total or 0)

    # ── Uang kotor per bulan ──
    def get_period(self, user_id: str, period: str) -> Optional[PlanPeriod]:
        return PlanPeriod.query.filter_by(user_id=user_id, period=period).first()

    def set_gross_income(self, user_id: str, period: str, gross) -> PlanPeriod:
        if not PERIOD_PATTERN.match(period or ""):
            raise ValueError("Format periode harus YYYY-MM")
        row = self.get_period(user_id, period)
        if row is None:
            row = PlanPeriod(user_id=user_id, period=period)
            db.session.add(row)
        row.gross_income = self._parse_amount(gross, allow_zero=True)
        db.session.commit()
        return row

    def list_periods(self, user_id: str, limit: int = 12) -> List[PlanPeriod]:
        return (
            PlanPeriod.query
            .filter(PlanPeriod.user_id == user_id)
            .order_by(PlanPeriod.period.desc())
            .limit(limit)
            .all()
        )

    # ── Kalkulator ──
    def summary(self, user_id: str, period: str) -> dict:
        row = self.get_period(user_id, period)
        gross = Decimal(row.gross_income if row else 0)
        needs = self.total_needs(user_id)
        # Porsi kebutuhan terhadap uang kotor. None bila uang kotor 0
        # (rasio tak terdefinisi, hindari bagi nol).
        if gross > 0:
            ratio = needs / gross * 100
            needs_ratio = ratio.quantize(Decimal("0.1"))
            needs_ratio_width = float(min(ratio, Decimal(100)))
        else:
            needs_ratio = None
            needs_ratio_width = 0.0
        return {
            "period": period,
            "gross_income": gross,
            "total_needs": needs,
            "net_income": gross - needs,
            "needs_ratio": needs_ratio,
            "needs_ratio_width": needs_ratio_width,
        }

    @staticmethod
    def _parse_amount(amount, allow_zero: bool = False) -> Decimal:
        try:
            value = Decimal(str(amount))
        except (InvalidOperation, TypeError):
            raise ValueError("Nominal tidak valid")
        if value < 0 or (value == 0 and not allow_zero):
            raise ValueError("Nominal harus lebih dari 0")
        return value.quantize(Decimal("0.01"))
