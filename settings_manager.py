"""
Uygulama ayarlarını JSON dosyasında saklayan ve yükleyen modül.
"""
import os
import db.database as db

DEFAULTS = {
    "port": 5000,
    "theme": "Sistem",
    "auto_start_server": True,
    "download_dir": os.path.join(os.path.expanduser("~"), "Downloads", "PyTransfer"),
    "security_enabled": True,
    "otp_enabled": False,
    "default_download_limit": 0,
    "default_time_limit": 0,
}

def load() -> dict:
    """Ayarları SQLite veritabanından yükler."""
    settings = dict(DEFAULTS)
    db_settings = db.load_settings()
    settings.update({k: v for k, v in db_settings.items() if k in DEFAULTS})
    return settings

def save(settings: dict):
    """Ayarları SQLite veritabanına yazar."""
    for k in DEFAULTS:
        if k in settings:
            db.save_setting(k, settings[k])
