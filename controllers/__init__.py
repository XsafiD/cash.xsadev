"""controllers/__init__.py — Registrasi Blueprint terpusat."""
from importlib import import_module

from flask import Blueprint, Flask

BLUEPRINT_MODULES = (
    "controllers.auth_controller",
    "controllers.dashboard_controller",
    "controllers.account_controller",
    "controllers.category_controller",
    "controllers.transaction_controller",
    "controllers.plan_controller",
)


def register_blueprints(app: Flask) -> None:
    """Daftarkan semua Blueprint; modul yang belum ada dilewati dengan warning."""
    for module_path in BLUEPRINT_MODULES:
        try:
            module = import_module(module_path)
        except ImportError:
            app.logger.warning("Blueprint module dilewati: %s", module_path)
            continue

        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, Blueprint):
                app.register_blueprint(obj)
