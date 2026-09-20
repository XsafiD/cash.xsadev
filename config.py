"""config.py — Konfigurasi aplikasi (env-based, sensible defaults)."""
import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

DEFAULT_DATABASE_URL = (
    "mysql+pymysql://cashxsadev:secret@127.0.0.1:3307/cashxsadev?charset=utf8mb4"
)


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-fallback-JANGAN-dipakai-production")

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "echo": False,
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)

    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

    APP_TZ = os.environ.get("APP_TZ", "Asia/Jakarta")
    APP_VERSION = os.environ.get("APP_VERSION", "1.0.0")

    # Aktifkan hanya bila app berada di belakang reverse proxy tepercaya (nginx).
    # Mencegah spoofing X-Forwarded-* saat app diekspos langsung.
    TRUST_PROXY = os.environ.get("TRUST_PROXY", "0") == "1"


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {}
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret-key"


class ProductionConfig(Config):
    # Fail-fast: production tanpa fallback diam-diam.
    # Sengaja None (bukan KeyError saat import) — `create_app` yang menolak jalan.
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    # Default aman: HTTPS-only. Set SESSION_COOKIE_SECURE=0 bila diakses
    # HTTP polos tanpa reverse proxy/TLS (mis. akses lokal langsung ke port app).
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "1") == "1"
