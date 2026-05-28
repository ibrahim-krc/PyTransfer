import threading
from werkzeug.serving import make_server
from server import core
from server.security import register_security_hooks
from server.routes import register_routes
from server.discovery import register_mdns, unregister_mdns
import os

_server_thread = None
_routes_registered = False

class ServerThread(threading.Thread):
    """
    Background thread to run the Flask HTTP server without blocking the main GUI thread.
    """
    def __init__(self, host, port, app, wsgi_app=None):
        """
        Initializes the server thread and creates the server context.
        """
        threading.Thread.__init__(self, daemon=True)
        self.srv = make_server(host, port, wsgi_app or app, threaded=True)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        """
        Starts the Flask HTTP server loop.
        """
        try:
            self.srv.serve_forever()
        except Exception:
            pass

    def shutdown(self):
        """
        Gracefully shuts down the running Flask HTTP server.
        """
        try:
            self.srv.shutdown()
        except Exception:
            pass

_server_thread = None

def start_server(host, port, fm, log_cb, rec_cb):
    """
    Initializes and starts the Flask HTTP server, registers routes, and publishes the mDNS record.
    
    Args:
        host (str): IP address to bind the server to.
        port (int): Port number to run the server on.
        fm (FileManager): Instance of the file manager to handle shared files.
        log_cb (callable): Callback function for logging server events.
        rec_cb (callable): Callback function for handling received files.
    """
    global _server_thread
    
    core.file_manager = fm
    core.log_callback = log_cb
    core.received_callback = rec_cb
    
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    if _server_thread:
        stop_server()
    global _routes_registered
    if not _routes_registered:
        register_security_hooks(core.app)
        register_routes(core.app)
        _routes_registered = True

    # Sync Manager'ı başlat
    import settings_manager
    from server.sync import SyncManager
    settings = settings_manager.load()
    
    if not core.sync_manager:
        core.sync_manager = SyncManager()
        
    if settings.get("sync_enabled", False):
        sync_folder = settings.get("sync_folder", os.path.join(os.path.expanduser("~"), "Documents", "PyTransfer_Sync"))
        if not os.path.exists(sync_folder):
            os.makedirs(sync_folder, exist_ok=True)
        core.sync_manager.start(sync_folder)

    # _server_thread varsa ve yaşıyorsa durdur
    if _server_thread and _server_thread.is_alive():
        _server_thread.shutdown()
        _server_thread.join()
        
    from server.middleware import SpeedTrackerMiddleware
    wrapped_app = SpeedTrackerMiddleware(core.app)
    
    from werkzeug.middleware.proxy_fix import ProxyFix
    wrapped_app = ProxyFix(wrapped_app, x_for=1, x_host=1)
        
    _server_thread = ServerThread(host, port, core.app, wsgi_app=wrapped_app)
    _server_thread.start()
    
    register_mdns(host, port)

def stop_server():
    """
    Stops the Flask HTTP server and unregisters the mDNS discovery record.
    """
    global _server_thread

    if core.sync_manager:
        core.sync_manager.stop()

    if _server_thread:
        try:
            _server_thread.shutdown()
        except Exception:
            pass
        _server_thread = None

    unregister_mdns()
