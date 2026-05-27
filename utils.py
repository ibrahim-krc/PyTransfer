import os
import socket
import qrcode
import uuid
from PIL import Image

class SharedFile:
    """
    Paylaşılan tek bir dosyanın üst verilerini (ID, ad, boyut, yol, uzantı)
    temsil eden sınıftır.
    """
    def __init__(self, filepath):
        """
        SharedFile sınıfı kurucusudur. Dosya bilgilerini toplar ve rastgele ID atar.
        """
        self.id = str(uuid.uuid4())[:8] 
        self.path = os.path.abspath(filepath)
        self.name = os.path.basename(filepath)
        self.size = os.path.getsize(filepath)
        self.ext = os.path.splitext(self.name)[1].lower()
        
        self.max_downloads = 0
        self.current_downloads = 0
        self.expires_at = None

    def to_dict(self):
        """
        Dosya bilgilerini web istemcisine gönderilecek JSON uyumlu sözlük formatına çevirir.
        """
        return {
            "id": self.id,
            "name": self.name,
            "size": self.size,
            "ext": self.ext,
            "max_downloads": self.max_downloads,
            "current_downloads": self.current_downloads,
            "expires_at": self.expires_at
        }

class FileManager:
    """
    Uygulamadaki paylaşılan dosyaları ve indirilen dosyaların dizinini
    yöneten sınıftır.
    """
    def __init__(self):
        """
        FileManager sınıfı kurucusudur. İndirme dizinini doğrular ve hazırlar.
        """
        self.shared_files = {}
        self.download_dir = os.path.join(os.path.expanduser("~"), "Downloads", "PyTransfer")
        if not os.path.exists(self.download_dir):
            try:
                os.makedirs(self.download_dir)
            except Exception:
                self.download_dir = os.path.abspath("./received_files")
                os.makedirs(self.download_dir, exist_ok=True)

    def add_shared_file(self, filepath):
        """
        Listeye yeni bir paylaşılan dosya ekler. Eğer dosya zaten paylaşımdaysa mevcut olanı döner.
        """
        if not os.path.exists(filepath):
            return None
        file_obj = SharedFile(filepath)
        for fid, f in list(self.shared_files.items()):
            if f.path == file_obj.path:
                return f
        self.shared_files[file_obj.id] = file_obj
        return file_obj

    def remove_shared_file(self, file_id):
        """
        Belirtilen ID'ye sahip dosyayı paylaşımdan kaldırır.
        """
        if file_id in self.shared_files:
            del self.shared_files[file_id]
            return True
        return False

    def get_shared_file(self, file_id):
        """
        Belirtilen ID'ye sahip paylaşılan dosyanın nesnesini döner.
        """
        return self.shared_files.get(file_id)

    def get_all_shared(self):
        """
        Tüm paylaşılan dosyaların listesini döner.
        """
        return [f.to_dict() for f in self.shared_files.values()]

    def set_download_dir(self, directory):
        """
        Gelen dosyaların kaydedileceği dizini değiştirir.
        """
        if os.path.exists(directory) and os.path.isdir(directory):
            self.download_dir = os.path.abspath(directory)
            return True
        return False

def get_primary_ip():
    """
    Sistemin birincil ağ arayüzünün IP adresini tespit eder.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def get_all_ips():
    """
    Sistemdeki tüm aktif IPv4 yerel IP adreslerini toplar ve listeler.
    """
    ips = []
    try:
        hostname = socket.gethostname()
        host_ips = socket.gethostbyname_ex(hostname)[2]
        for ip in host_ips:
            if not ip.startswith("127.") and ":" not in ip:
                ips.append(ip)
    except Exception:
        pass
    
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None):
            if info[0] == socket.AF_INET:
                ip = info[4][0]
                if not ip.startswith("127.") and ip not in ips:
                    ips.append(ip)
    except Exception:
        pass
        
    primary = get_primary_ip()
    if primary != '127.0.0.1':
        if primary in ips:
            ips.remove(primary)
        ips.insert(0, primary)
        
    if not ips:
        ips = ['127.0.0.1']
        
    return list(dict.fromkeys(ips))

def get_labeled_ips():
    """
    IP adreslerini kullanıcı dostu şekilde etiketler (Yerel Ağ, Mobil Erişim Noktası vb.).
    """
    ips = get_all_ips()
    labeled = []
    for ip in ips:
        if ip.startswith("192.168.137."):
            labeled.append({"ip": ip, "label": f"Mobil Erişim Noktası (Hotspot) - {ip}"})
        elif ip == "127.0.0.1":
            labeled.append({"ip": ip, "label": f"Yerel Sunucu (Localhost) - {ip}"})
        else:
            labeled.append({"ip": ip, "label": f"Yerel Ağ (Wi-Fi/Ethernet) - {ip}"})
    return labeled

def generate_qr(data, filepath):
    """
    İstemcilerin tarayarak bağlanması için bağlantı URL'sini içeren bir QR kod resmi üretir.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filepath)
    return filepath

def format_size(size_bytes):
    """
    Bayt cinsinden dosya boyutunu okunabilir formatlara çevirir (KB, MB, GB).
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

def zip_folder_with_progress(folderpath, zip_path, progress_callback):
    """
    Bir klasörü ZIP biçiminde sıkıştırırken ilerleme durumunu geri bildirim olarak döner.
    """
    import zipfile
    
    total_size = 0
    file_list = []
    
    for root, dirs, files in os.walk(folderpath):
        for file in files:
            full_path = os.path.join(root, file)
            if os.path.abspath(full_path) == os.path.abspath(zip_path):
                continue
            try:
                size = os.path.getsize(full_path)
                total_size += size
                file_list.append((full_path, os.path.relpath(full_path, folderpath), size))
            except Exception:
                pass
                
    if not file_list:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            pass
        progress_callback(1.0)
        return

    written_size = 0
    import time
    last_update_time = 0
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=1) as zf:
        for full_path, rel_path, size in file_list:
            try:
                zf.write(full_path, rel_path)
                written_size += size
                progress = written_size / total_size
                current_time = time.time()
                # 0.1 saniyede bir arayüzü güncelle (hem donmayı önler hem akıcı görünür)
                if current_time - last_update_time > 0.1:
                    progress_callback(progress, rel_path)
                    last_update_time = current_time
            except Exception:
                pass
    progress_callback(1.0, "Tamamlandı")

def parse_dropped_paths(data_str):
    """
    Sürükle-bırak ile gelen veri dizgesini (özellikle boşluklu ve süslü parantezli yolları)
    düzgün bir dosya yolları listesine dönüştürür.
    """
    paths = []
    if not data_str:
        return paths
        
    import re
    pattern = r'\{([^}]+)\}|(\S+)'
    for match in re.finditer(pattern, data_str):
        path = match.group(1) or match.group(2)
        if path:
            path = os.path.normpath(path)
            paths.append(path)
            
    return paths
