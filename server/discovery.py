import socket
import threading
from zeroconf import IPVersion, ServiceInfo, Zeroconf, ServiceBrowser
from server import core

_zeroconf = None
_zc_info = None
_browser = None

class PyTransferListener:
    """
    Listens for other PyTransfer services on the local network.
    """
    def remove_service(self, zeroconf, type, name):
        """
        Called when a service is removed.
        """
        if name.startswith("PyTransfer_"):
            if name in core.discovered_servers:
                del core.discovered_servers[name]

    def add_service(self, zeroconf, type, name):
        """
        Called when a new service is discovered.
        """
        if name.startswith("PyTransfer_"):
            info = zeroconf.get_service_info(type, name)
            if info and info.addresses:
                ip_addr = socket.inet_ntoa(info.addresses[0])
                port = info.port
                # Avoid adding ourselves if we can detect it (naive check by port/name)
                if _zc_info and _zc_info.name == name:
                    return
                core.discovered_servers[name] = {
                    "ip": ip_addr,
                    "port": port,
                    "name": name.split('.')[0]
                }

    def update_service(self, zeroconf, type, name):
        """
        Called when a service is updated.
        """
        pass

def register_mdns(host, port):
    """
    Registers the PyTransfer application as an mDNS (Zeroconf) service on the local network
    and starts browsing for other PyTransfer services.
    
    Args:
        host (str): The IP address to bind the service to.
        port (int): The port the server is running on.
    """
    global _zeroconf, _zc_info, _browser
    try:
        _zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
        desc = {'path': '/'}
        service_name = f"PyTransfer_{port}._http._tcp.local."
        _zc_info = ServiceInfo(
            "_http._tcp.local.",
            service_name,
            addresses=[socket.inet_aton(host)],
            port=port,
            properties=desc,
            server="pytransfer.local."
        )
        _zeroconf.register_service(_zc_info)
        
        # Start browsing for other PyTransfer servers
        listener = PyTransferListener()
        _browser = ServiceBrowser(_zeroconf, "_http._tcp.local.", listener)
        
        if core.log_callback:
            core.log_callback("mDNS: pytransfer.local yerel ağda yayınlanıyor")
    except Exception as e:
        if core.log_callback:
            core.log_callback(f"mDNS HATA: Keşif servisi başlatılamadı: {e}")

def unregister_mdns():
    """
    Unregisters the mDNS service and closes the Zeroconf connection in a background thread
    to prevent blocking.
    """
    global _zeroconf, _zc_info, _browser
    
    zc, zc_info, browser = _zeroconf, _zc_info, _browser
    _zeroconf = None
    _zc_info = None
    _browser = None

    if zc:
        def _close_zc():
            try:
                if browser:
                    browser.cancel()
                if zc_info:
                    zc.unregister_service(zc_info)
                zc.close()
            except Exception:
                pass
        t = threading.Thread(target=_close_zc, daemon=True)
        t.start()
        t.join(timeout=1.0)
