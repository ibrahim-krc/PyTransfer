import time
import threading
from flask import request
from server import core

def parse_user_agent(ua_string):
    """
    Parses the operating system and browser information from the User-Agent string.
    
    Args:
        ua_string (str): The User-Agent string to parse.
        
    Returns:
        str: A formatted string containing OS and browser info, e.g., 'Windows (Chrome)'.
    """
    if not ua_string:
        return "Bilinmeyen Cihaz"
    
    os_name = "Bilinmeyen OS"
    if "Android" in ua_string:
        os_name = "Android"
    elif "iPhone" in ua_string or "iPad" in ua_string:
        os_name = "iOS"
    elif "Windows" in ua_string:
        os_name = "Windows"
    elif "Macintosh" in ua_string:
        os_name = "macOS"
    elif "Linux" in ua_string:
        os_name = "Linux"
        
    browser_name = "Bilinmeyen Tarayici"
    if "Chrome" in ua_string or "CriOS" in ua_string:
        browser_name = "Chrome"
    elif "Safari" in ua_string and "Chrome" not in ua_string:
        browser_name = "Safari"
    elif "Firefox" in ua_string or "FxiOS" in ua_string:
        browser_name = "Firefox"
    elif "Edg" in ua_string:
        browser_name = "Edge"
        
    return f"{os_name} ({browser_name})"

def trigger_otp_regeneration():
    """
    Regenerates the one-time PIN code every 5 seconds if OTP is enabled.
    """
    if not core.otp_enabled or not core.security_enabled:
        return
    
    if core._otp_timer:
        core._otp_timer.cancel()
        
    def regenerate():
        import random
        new_pin = str(random.randint(1000, 9999))
        core.pin_code = new_pin
        if core.log_callback:
            core.log_callback(f"GÜVENLİK: Tek kullanimlik PIN yenilendi. Yeni PIN: {new_pin}")
        if core.pin_changed_callback:
            try:
                core.pin_changed_callback(new_pin)
            except Exception:
                pass
                
    core._otp_timer = threading.Timer(5.0, regenerate)
    core._otp_timer.start()

def block_ip(ip):
    """
    Adds a specified IP address to the blocked clients list.
    
    Args:
        ip (str): The IP address to block.
    """
    core.blocked_clients.add(ip)
    if core.log_callback:
        core.log_callback(f"ENGEL: {ip} engellendi.")

def unblock_ip(ip):
    """
    Removes a specified IP address from the blocked clients list.
    
    Args:
        ip (str): The IP address to unblock.
    """
    if ip in core.blocked_clients:
        core.blocked_clients.remove(ip)
        if core.log_callback:
            core.log_callback(f"ENGEL KALDIRILDI: {ip} engeli kaldirildi.")

def register_security_hooks(app):
    """
    Registers the before_request hook to intercept and handle blocked clients,
    and updates the active clients tracking list.
    
    Args:
        app (Flask): The Flask application instance.
    """
    @app.before_request
    def check_blocked_and_track():
        client_ip = request.remote_addr
        if client_ip in core.blocked_clients:
            if request.path == '/' or request.path.startswith('/static/'):
                return None
            return "Erişim Engellendi: Bu cihaza erişiminiz engellenmiştir.", 403
            
        if client_ip == "127.0.0.1":
            return
            
        ua = request.headers.get('User-Agent', '')
        core.active_clients[client_ip] = {
            "ip": client_ip,
            "device": parse_user_agent(ua),
            "last_seen": time.time()
        }
