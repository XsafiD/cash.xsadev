"""services/category_service.py — Business logic Category."""
from typing import List, Optional

from models import db
from models.category import Category, VALID_CATEGORY_KINDS


class CategoryService:
    """CRUD + business rules untuk Category."""

    def get_all(self, user_id: str, kind: Optional[str] = None) -> List[Category]:
        query = Category.query.filter(
            Category.user_id == user_id, Category.deleted_at.is_(None)
        )
        if kind:
            if kind not in VALID_CATEGORY_KINDS:
                raise ValueError(
                    f"Jenis kategori tidak valid. Pilihan: {', '.join(VALID_CATEGORY_KINDS)}"
                )
            query = query.filter(Category.kind == kind)
        return query.order_by(Category.name.asc()).all()

    def get_by_id(self, user_id: str, category_id: str) -> Optional[Category]:
        return Category.query.filter(
            Category.id == category_id,
            Category.user_id == user_id,
            Category.deleted_at.is_(None),
        ).first()

    def create(self, user_id: str, name: str, kind: str) -> Category:
        name = (name or "").strip()
        if len(name) < 2:
            raise ValueError("Nama kategori minimal 2 karakter")
        if kind not in VALID_CATEGORY_KINDS:
            raise ValueError(
                f"Jenis kategori tidak valid. Pilihan: {', '.join(VALID_CATEGORY_KINDS)}"
            )
        duplicate = Category.query.filter(
            Category.user_id == user_id,
            Category.name == name,
            Category.kind == kind,
            Category.deleted_at.is_(None),
        ).first()
        if duplicate is not None:
            raise ValueError(f"Kategori '{name}' sudah ada")
        category = Category(user_id=user_id, name=name, kind=kind)
        db.session.add(category)
        db.session.commit()
        return category

    def update(self, user_id: str, category_id: str, name: str, kind: str) -> Category:
        category = self.get_by_id(user_id, category_id)
        if category is None:
            raise ValueError("Kategori tidak ditemukan")
        name = (name or "").strip()
        if len(name) < 2:
            raise ValueError("Nama kategori minimal 2 karakter")
        if kind not in VALID_CATEGORY_KINDS:
            raise ValueError(
                f"Jenis kategori tidak valid. Pilihan: {', '.join(VALID_CATEGORY_KINDS)}"
            )
        category.name = name
        category.kind = kind
        db.session.commit()
        return category

    def delete(self, user_id: str, category_id: str) -> None:
        from models import utcnow

        category = self.get_by_id(user_id, category_id)
        if category is None:
            raise ValueError("Kategori tidak ditemukan")
        category.deleted_at = utcnow()
        db.session.commit()
