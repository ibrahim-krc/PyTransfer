import os
import subprocess
import threading
import urllib.request
import platform
import re
import time

class CloudflareTunnel:
    """
    Cloudflare Hızlı Tünel (trycloudflare) yönetimini sağlayan sınıftır.
    Yerel sunucuyu güvenli bir HTTPS adresiyle dünyaya açar.
    """
    def __init__(self, host, port, log_callback=None):
        self.host = host
        self.port = port
        self.log_callback = log_callback
        self.process = None
        self.public_url = None
        self.thread = None
        self._stop_event = threading.Event()
        
        self.bin_dir = os.path.join(os.path.expanduser("~"), ".pytransfer_bin")
        self.exe_name = "cloudflared.exe" if platform.system() == "Windows" else "cloudflared"
        self.exe_path = os.path.join(self.bin_dir, self.exe_name)

    def _log(self, msg):
        if self.log_callback:
            self.log_callback(msg)
            
    def ensure_cloudflared(self):
        """Cloudflared dosyasının var olduğunu kontrol eder, yoksa indirir."""
        if os.path.exists(self.exe_path):
            return True
            
        os.makedirs(self.bin_dir, exist_ok=True)
        
        system = platform.system()
        machine = platform.machine().lower()
        
        if system == "Windows":
            if "amd64" in machine or "x86_64" in machine:
                url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
            else:
                url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-386.exe"
        else:
            self._log("HATA: Otomatik cloudflared indirmesi şu an sadece Windows destekliyor.")
            return False
            
        self._log("BİLGİ: Cloudflare Tünel aracı indiriliyor, lütfen bekleyin...")
        try:
            # urllib yerine sistemdeki curl aracını kullanarak daha güvenli indirme yapıyoruz
            creationflags = 0
            if system == "Windows":
                creationflags = subprocess.CREATE_NO_WINDOW
                
            subprocess.run(["curl", "-L", "-o", self.exe_path, url], check=True, creationflags=creationflags)
            self._log("BİLGİ: Tünel aracı başarıyla indirildi.")
            return True
        except Exception as e:
            self._log(f"HATA: Tünel aracı indirilemedi: {e}")
            return False

    def start(self):
        """Tüneli başlatır ve public URL alana kadar (max 15 sn) bekler."""
        if not self.ensure_cloudflared():
            return False
            
        self._stop_event.clear()
        self.thread = threading.Thread(target=self._run_tunnel, daemon=True)
        self.thread.start()
        
        # URL'nin alınmasını bekle (Max 15 sn)
        for _ in range(30):
            if self.public_url or self._stop_event.is_set():
                break
            time.sleep(0.5)
            
        return self.public_url is not None

    def _run_tunnel(self):
        """Arka planda cloudflared'i çalıştırır ve çıktıları (URL'yi) yakalar."""
        cmd = [self.exe_path, "tunnel", "--url", f"http://{self.host}:{self.port}"]
        
        try:
            # Siyah terminal penceresi çıkmasını engellemek için
            creationflags = 0
            if platform.system() == "Windows":
                creationflags = subprocess.CREATE_NO_WINDOW
                
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=creationflags
            )
            
            url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
            
            # cloudflared tüm logları stderr'e yazar
            for line in self.process.stderr:
                if self._stop_event.is_set():
                    break
                    
                match = url_pattern.search(line)
                if match and not self.public_url:
                    self.public_url = match.group(0)
                    self._log(f"BAŞARILI: Tünel açıldı -> {self.public_url}")
                    
        except Exception as e:
            self._log(f"HATA: Tünel başlatılamadı: {e}")
            
    def stop(self):
        """Tünel işlemini sonlandırır."""
        self._stop_event.set()
        if self.process:
            try:
                self.process.terminate()
            except Exception:
                pass
            try:
                self.process.kill()
            except Exception:
                pass
            self.process = None
        self.public_url = None
        self._log("BİLGİ: Dış ağ tüneli kapatıldı.")
