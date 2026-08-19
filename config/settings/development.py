import os
from urllib.parse import urlparse

from .base import *

DEBUG = True

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///" + str(BASE_DIR / "db.sqlite3"))

if DATABASE_URL.startswith("sqlite"):
    db_path = DATABASE_URL.replace("sqlite:///", "")
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / db_path if db_path else BASE_DIR / "db.sqlite3",
        }
    }
else:
    url = urlparse(DATABASE_URL)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": url.path[1:],
            "USER": url.username,
            "PASSWORD": url.password,
            "HOST": url.hostname,
            "PORT": url.port or 5432,
        }
    }
