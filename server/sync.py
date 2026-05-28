import os
import time
import json
import threading
import urllib.request
import urllib.error
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from server import core

class SyncManager:
    def __init__(self):
        self.sync_folder = None
        self.observer = None
        self.poller_thread = None
        self.running = False
        self.ignore_list = set()
        self.ignore_lock = threading.Lock()

    def start(self, sync_folder):
        if not sync_folder or not os.path.exists(sync_folder):
            if core.log_callback:
                core.log_callback(f"Sync HATA: Klasör bulunamadı ({sync_folder})")
            return

        self.sync_folder = sync_folder
        self.running = True

        # Watchdog observer başlat
        event_handler = SyncFolderEventHandler(self)
        self.observer = Observer()
        self.observer.schedule(event_handler, self.sync_folder, recursive=False)
        self.observer.start()

        # Poller thread başlat
        self.poller_thread = threading.Thread(target=self._poll_discovered_servers, daemon=True)
        self.poller_thread.start()
        
        if core.log_callback:
            core.log_callback(f"Auto-Sync Başlatıldı: {self.sync_folder}")

    def stop(self):
        self.running = False
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
        if core.log_callback:
            core.log_callback("Auto-Sync Durduruldu.")

    def add_to_ignore(self, filename):
        with self.ignore_lock:
            self.ignore_list.add(filename)

    def remove_from_ignore(self, filename):
        with self.ignore_lock:
            if filename in self.ignore_list:
                self.ignore_list.remove(filename)

    def is_ignored(self, filename):
        with self.ignore_lock:
            return filename in self.ignore_list

    def _poll_discovered_servers(self):
        """
        Ağdaki diğer PyTransfer cihazlarına gidip yeni dosya var mı diye kontrol eder.
        """
        while self.running:
            try:
                # Gecikmeyi azaltmak için sunucu listesini kopyalayalım
                servers = list(core.discovered_servers.values())
                
                # Kendi yerel dosyalarımızın listesini çıkaralım ki olanı tekrar indirmeyelim
                local_files = {}
                if os.path.exists(self.sync_folder):
                    for f in os.listdir(self.sync_folder):
                        path = os.path.join(self.sync_folder, f)
                        if os.path.isfile(path):
                            local_files[f] = os.path.getmtime(path)

                for srv in servers:
                    url = f"http://{srv['ip']}:{srv['port']}/api/sync/list"
                    try:
                        req = urllib.request.Request(url, headers={'Content-Type': 'application/json'})
                        with urllib.request.urlopen(req, timeout=3) as response:
                            if response.status == 200:
                                data = json.loads(response.read().decode('utf-8'))
                                remote_files = data.get("files", [])
                                
                                for rf in remote_files:
                                    r_name = rf.get("name")
                                    r_mtime = rf.get("mtime", 0)
                                    
                                    # Bizde yoksa veya bizdeki eskiyse indir
                                    should_download = False
                                    if r_name not in local_files:
                                        should_download = True
                                    else:
                                        # mtime farkı varsa (1 saniyeden büyükse)
                                        if r_mtime > local_files[r_name] + 1:
                                            should_download = True
                                            
                                    if should_download and not self.is_ignored(r_name):
                                        self._download_sync_file(srv['ip'], srv['port'], r_name)

                    except Exception as e:
                        # Sunucu kapalı veya ulaşılamıyor olabilir, sessizce geç
                        pass
                        
            except Exception as e:
                if core.log_callback:
                    core.log_callback(f"Sync Poller Hatası: {e}")
            
            # Her 5 saniyede bir yokla
            time.sleep(5)

    def _download_sync_file(self, ip, port, filename):
        url = f"http://{ip}:{port}/api/sync/download/{urllib.parse.quote(filename)}"
        save_path = os.path.join(self.sync_folder, filename)
        
        try:
            if core.log_callback:
                core.log_callback(f"Sync İndiriliyor: {filename} ({ip})")
                
            self.add_to_ignore(filename)
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=30) as response:
                with open(save_path, 'wb') as f:
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
            
            # İndirme bitince ignore'dan hemen çıkarma, watchdog etkinliklerini pas geçmesi için 1 sn bekle
            threading.Timer(2.0, self.remove_from_ignore, args=[filename]).start()
            
            if core.log_callback:
                core.log_callback(f"Sync Tamamlandı: {filename}")
        except Exception as e:
            self.remove_from_ignore(filename)
            if core.log_callback:
                core.log_callback(f"Sync İndirme Hatası ({filename}): {e}")

class SyncFolderEventHandler(FileSystemEventHandler):
    def __init__(self, manager):
        self.manager = manager
        super().__init__()

    def process_event(self, event):
        if event.is_directory:
            return
            
        filename = os.path.basename(event.src_path)
        
        # Eğer bu dosyayı şu an biz indiriyorsak veya yeni indirdiysek tetikleme
        if self.manager.is_ignored(filename):
            return
            
        # Dosya silindiyse bir şey yapmayalım (Sadece Append-Only yapıyoruz)
        if event.event_type == 'deleted':
            return
            
        # Dosya eklendi veya değişti, paylaşıma aç (add_shared_file idempotent'tir, aynı dosya varsa yeniler)
        if core.file_manager:
            file_obj = core.file_manager.add_shared_file(event.src_path)
            if file_obj and core.log_callback:
                core.log_callback(f"Sync Paylaşıma Açıldı: {filename}")

    def on_created(self, event):
        self.process_event(event)

    def on_modified(self, event):
        self.process_event(event)
