"""
Test-only Django settings: SQLite in-memory, fast hashing.
"""
from train_station_service.settings import *  # noqa: F401, F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Fast password hashing during tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable media storage side-effects
DEFAULT_FILE_STORAGE = "django.core.files.storage.InMemoryStorage"
