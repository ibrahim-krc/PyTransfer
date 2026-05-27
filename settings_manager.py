"""
Uygulama ayarlarını JSON dosyasında saklayan ve yükleyen modül.
"""
import os
import json
import db.database as db

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

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
    """Ayarları veritabanından yükler; eski JSON varsa DB'ye aktarıp (migrate) JSON'u siler."""
    settings = dict(DEFAULTS)
    
    # 1. Migration (JSON'dan SQLite'a aktarım)
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            
            # Veritabanına kaydet
            for k, v in saved.items():
                if k in DEFAULTS:
                    db.save_setting(k, v)
                    
            # Başarılı aktarım sonrası JSON dosyasını sil
            os.remove(SETTINGS_FILE)
        except Exception:
            pass

    # 2. Veritabanından Oku
    db_settings = db.load_settings()
    settings.update({k: v for k, v in db_settings.items() if k in DEFAULTS})
    
    return settings

def save(settings: dict):
    """Ayarları SQLite veritabanına yazar."""
    for k in DEFAULTS:
        if k in settings:
            db.save_setting(k, settings[k])
