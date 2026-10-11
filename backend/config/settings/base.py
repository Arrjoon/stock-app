"""
Shared settings.

Environment variables are the only source of secrets.
Development and production modules extend this file.
"""

from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1", "web"]),
    CORS_ALLOWED_ORIGINS=(list, ["http://localhost:3000", "http://127.0.0.1:3000"]),
)

_env_file = BASE_DIR.parent / ".env"
if _env_file.exists():
    environ.Env.read_env(_env_file)

SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-only-change-me")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "django_celery_beat",
    "channels",
    "apps.accounts",
    "apps.companies",
    "apps.market",
    "apps.news",
    "apps.analysis",
    "apps.crawling",
    "apps.realtime",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="postgres://postgres:postgres@localhost:5432/stockapp",
    )
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kathmandu"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}
MEDIA_URL = "media/"
MEDIA_ROOT = Path(env("MEDIA_ROOT", default=str(BASE_DIR / "media")))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_CREDENTIALS = True

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "common.exceptions.api_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.int("JWT_ACCESS_MINUTES", default=60)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("JWT_REFRESH_DAYS", default=7)),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "NEPSE Stock API",
    "DESCRIPTION": "Role-gated NEPSE market, news, and analysis API.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    "SERVE_AUTHENTICATION": [],
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": "/api",
    "TAGS": [
        {"name": "Health", "description": "Liveness"},
        {"name": "Auth", "description": "JWT login and refresh"},
    ],
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "displayRequestDuration": True,
        "filter": True,
        "tryItOutEnabled": True,
    },
}

REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [REDIS_URL]},
    }
}

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/1")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/1")
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_TRACK_STARTED = True
CELERY_WORKER_SEND_TASK_EVENTS = True
CELERY_TASK_SEND_SENT_EVENT = True
CELERY_TASK_TIME_LIMIT = env.int("CELERY_TASK_TIME_LIMIT", default=900)
CELERY_TASK_SOFT_TIME_LIMIT = env.int("CELERY_TASK_SOFT_TIME_LIMIT", default=720)
CELERY_TASK_DEFAULT_QUEUE = "celery"
CELERY_TASK_ROUTES = {
    "apps.news.tasks.crawl_portal_news": {"queue": "crawl"},
    "apps.news.tasks.fetch_article": {"queue": "crawl"},
    "apps.market.tasks.crawl_prices": {"queue": "market"},
    "apps.market.tasks.crawl_floorsheet": {"queue": "market"},
    "apps.analysis.tasks.categorize_article": {"queue": "ml"},
    "apps.analysis.tasks.compute_behavior": {"queue": "ml"},
}

COMPANIES_YAML = env("COMPANIES_YAML", default=str(BASE_DIR.parent / "companies.yaml"))

CRAWLER_USER_AGENT = env(
    "CRAWLER_USER_AGENT",
    default="StockAppBot/0.1 (+https://localhost; research crawler)",
)
CRAWLER_TIMEOUT = env.float("CRAWLER_TIMEOUT", default=30.0)
CRAWL_NEWS_MINUTES = env.int("CRAWL_NEWS_MINUTES", default=30)
CRAWL_PRICES_HOUR = env.int("CRAWL_PRICES_HOUR", default=15)
CRAWL_PRICES_MINUTE = env.int("CRAWL_PRICES_MINUTE", default=0)
CRAWL_FLOORSHEET_HOUR = env.int("CRAWL_FLOORSHEET_HOUR", default=15)
CRAWL_FLOORSHEET_MINUTE = env.int("CRAWL_FLOORSHEET_MINUTE", default=15)
ANALYSIS_HOUR = env.int("ANALYSIS_HOUR", default=15)
ANALYSIS_MINUTE = env.int("ANALYSIS_MINUTE", default=45)
NEPSE_TLS_VERIFY = env.bool("NEPSE_TLS_VERIFY", default=False)
MARKET_PRICE_DAYS = env.int("MARKET_PRICE_DAYS", default=30)
MARKET_FLOORSHEET_DAYS = env.int("MARKET_FLOORSHEET_DAYS", default=3)


def _portal(name, defaults):
    prefix = f"CRAWLER_{name.upper()}_"
    cfg = {}
    for key, value in defaults.items():
        env_key = f"{prefix}{key.upper()}"
        if isinstance(value, bool):
            cfg[key] = env.bool(env_key, default=value)
        elif isinstance(value, float):
            cfg[key] = env.float(env_key, default=value)
        elif isinstance(value, int):
            cfg[key] = env.int(env_key, default=value)
        else:
            cfg[key] = env(env_key, default=value)
    return cfg


CRAWLER_CONFIG = {
    "merolagani": _portal(
        "merolagani",
        {
            "base_url": "https://merolagani.com",
            "news_list_url": "https://merolagani.com/NewsList.aspx",
            "floorsheet_url": "https://merolagani.com/Floorsheet.aspx",
            "price_history_url": "https://merolagani.com/handlers/webrequesthandler.ashx",
            "min_interval": 2.0,
            "max_pages": 5,
            "enabled": True,
            "use_selenium": True,
        },
    ),
    "sharesansar": _portal(
        "sharesansar",
        {
            "base_url": "https://www.sharesansar.com",
            "news_list_url": "https://www.sharesansar.com/category/latest-news",
            "min_interval": 1.5,
            "max_pages": 5,
            "enabled": True,
            "use_selenium": False,
        },
    ),
    "nepsealpha": _portal(
        "nepsealpha",
        {
            "base_url": "https://nepsealpha.com",
            "news_list_url": "https://nepsealpha.com/",
            "min_interval": 2.0,
            "max_pages": 1,
            "enabled": False,
            "use_selenium": False,
        },
    ),
    "bizmandu": _portal(
        "bizmandu",
        {
            "base_url": "https://wp.bizmandu.com",
            "news_list_url": "https://wp.bizmandu.com/content/category/market.html",
            "min_interval": 2.0,
            "max_pages": 5,
            "enabled": True,
            "use_selenium": False,
        },
    ),
}

SEED_ADMIN_PASSWORD = env("SEED_ADMIN_PASSWORD", default="")
SEED_ANALYST_PASSWORD = env("SEED_ANALYST_PASSWORD", default="")
SEED_VIEWER_PASSWORD = env("SEED_VIEWER_PASSWORD", default="")

LOG_DIR = Path(env("LOG_DIR", default=str(BASE_DIR / "logs")))
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "plain": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "plain"},
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "crawler.log"),
            "maxBytes": 5_000_000,
            "backupCount": 3,
            "formatter": "plain",
        },
    },
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", default="INFO")},
    "loggers": {
        "apps.crawling": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "apps.news": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "apps.market": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
