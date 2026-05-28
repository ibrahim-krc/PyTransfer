import sqlite3
import os
import json
import time

APP_DATA_DIR = os.path.join(os.path.expanduser("~"), ".pytransfer")
os.makedirs(APP_DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(APP_DATA_DIR, "PyTransfer.db")

def _get_connection():
    # Multi-threading desteği için check_same_thread=False (sadece basit okuma/yazmalar için)
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def initialize_database():
    """
    Veritabanı tablolarını yoksa oluşturur.
    """
    conn = _get_connection()
    cursor = conn.cursor()

    # Ayarlar Tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    # Transfer Geçmişi Tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS TransferHistory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            filename TEXT,
            action TEXT,
            client_ip TEXT
        )
    ''')

    conn.commit()
    conn.close()

# --- AYARLAR (SETTINGS) İŞLEMLERİ ---

def save_setting(key: str, value):
    """
    Belirli bir ayarı veritabanına kaydeder/günceller.
    Değerleri JSON string formatında tutuyoruz, böylece list/dict/int desteklenir.
    """
    conn = _get_connection()
    cursor = conn.cursor()
    str_value = json.dumps(value, ensure_ascii=False)
    cursor.execute('''
        INSERT INTO Settings (key, value) 
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value
    ''', (key, str_value))
    conn.commit()
    conn.close()

def load_settings() -> dict:
    """
    Veritabanındaki tüm ayarları sözlük olarak döndürür.
    """
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT key, value FROM Settings')
    rows = cursor.fetchall()
    conn.close()

    settings = {}
    for key, val in rows:
        try:
            settings[key] = json.loads(val)
        except Exception:
            settings[key] = val
    return settings

# --- GEÇMİŞ (HISTORY) İŞLEMLERİ ---

def add_history(filename: str, action: str, client_ip: str):
    """
    Geçmişe yeni bir indirme veya yükleme kaydı ekler.
    action: 'İndirme' veya 'Yükleme'
    """
    conn = _get_connection()
    cursor = conn.cursor()
    # Şu anki zamanı localtime olarak ekliyoruz (YYYY-MM-DD HH:MM:SS)
    current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    cursor.execute('''
        INSERT INTO TransferHistory (timestamp, filename, action, client_ip)
        VALUES (?, ?, ?, ?)
    ''', (current_time, filename, action, client_ip))
    conn.commit()
    conn.close()

def get_history(limit=50) -> list:
    """
    Geçmiş kayıtlarını (en yeniden en eskiye) liste olarak döndürür.
    """
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT timestamp, filename, action, client_ip
        FROM TransferHistory
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    history_list = []
    for row in rows:
        history_list.append({
            "time": row[0],
            "filename": row[1],
            "action": row[2],
            "ip": row[3]
        })
    return history_list

# Import edildiğinde DB'yi otomatik hazırla
initialize_database()
