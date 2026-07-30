import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEMO_MODE = os.getenv("DEMO_MODE") == "1"
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "local-synthetic-demo-only" if DEMO_MODE else "")
DEBUG = DEMO_MODE
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "support",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
            ]
        },
    }
]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("PGDATABASE", "support_ops"),
        "USER": os.getenv("PGUSER", "dw"),
        "HOST": os.getenv("PGHOST", "/Users/dw/code/portfolio-python/.runtime/pg16/support/socket"),
        "PORT": os.getenv("PGPORT", "15531"),
    }
}
USE_TZ = True
TIME_ZONE = "UTC"
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
DATA_UPLOAD_MAX_MEMORY_SIZE = 262144
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
