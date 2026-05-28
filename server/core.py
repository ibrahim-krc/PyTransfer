import os
from flask import Flask

_template_folder = os.environ.get("PYTRANSFER_TEMPLATE_FOLDER", "templates")
_static_folder   = os.environ.get("PYTRANSFER_STATIC_FOLDER",   "static")

app = Flask(__name__, template_folder=_template_folder, static_folder=_static_folder)
app.secret_key = os.urandom(24)

file_manager = None
log_callback = None
received_callback = None
pin_changed_callback = None
sync_manager = None

clipboard_text = ""
clipboard_history = []

security_enabled = True
pin_code = ""

otp_enabled = False
_otp_timer = None

public_url = None

active_clients = {}
blocked_clients = set()
discovered_servers = {}

transfer_stats = {
    "download_bytes_sec": 0,
    "upload_bytes_sec": 0
}
