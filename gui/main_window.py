import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image
import utils
import server
from server import core, security, routes
import settings_manager
from .left_panel import LeftPanel
from .right_panel import RightPanel

class LimitDialog(ctk.CTkToplevel):
    def __init__(self, master, file_count, on_confirm, settings):
        super().__init__(master)
        self.title("Güvenli Paylaşım")
        self.geometry("420x340")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.on_confirm = on_confirm
        self.settings = settings

        # İkon
        try:
            import sys as _sys
            _base = getattr(_sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            icon_path = os.path.join(_base, "assets", "logo.ico")
            if os.path.exists(icon_path):
                self.after(200, lambda: self.iconbitmap(icon_path))
        except Exception:
            pass

        # Ekranın ortasına konumlandır
        self.update_idletasks()
        x = master.winfo_rootx() + (master.winfo_width() // 2) - (420 // 2)
        y = master.winfo_rooty() + (master.winfo_height() // 2) - (340 // 2)
        self.geometry(f"+{x}+{y}")

        # Header
        header = ctk.CTkLabel(
            self, text="🔒  Güvenli Paylaşım",
            font=ctk.CTkFont(family="Outfit", size=18, weight="bold"),
            text_color=("#6366f1", "#818cf8")
        )
        header.pack(pady=(22, 4))

        desc = ctk.CTkLabel(
            self,
            text=f"Seçilen {file_count} öğe için paylaşım limitleri belirleyin.\n(Limitsiz paylaşmak için 0 bırakın)",
            font=ctk.CTkFont(size=12), text_color=("#64748b", "#94a3b8")
        )
        desc.pack(pady=(0, 16))

        frame = ctk.CTkFrame(self, fg_color=("#f8fafc", "#1e293b"), corner_radius=10)
        frame.pack(fill="x", padx=30, ipady=6)

        # İndirme Limiti — son değeri yükle
        dl_frame = ctk.CTkFrame(frame, fg_color="transparent")
        dl_frame.pack(fill="x", padx=15, pady=(14, 6))
        ctk.CTkLabel(dl_frame, text="İndirme Limiti (Kişi):", font=ctk.CTkFont(weight="bold")).pack(side="left")
        self.downloads_entry = ctk.CTkEntry(dl_frame, width=80, justify="center")
        self.downloads_entry.insert(0, str(settings.get("default_download_limit", 0)))
        self.downloads_entry.pack(side="right")

        # Süre Limiti — son değeri yükle
        tm_frame = ctk.CTkFrame(frame, fg_color="transparent")
        tm_frame.pack(fill="x", padx=15, pady=(6, 14))
        ctk.CTkLabel(tm_frame, text="Süre Limiti (Dakika):", font=ctk.CTkFont(weight="bold")).pack(side="left")
        self.time_entry = ctk.CTkEntry(tm_frame, width=80, justify="center")
        self.time_entry.insert(0, str(settings.get("default_time_limit", 0)))
        self.time_entry.pack(side="right")

        # Seçimi hatırla switch
        self.remember_var = tk.BooleanVar(value=True)
        remember_sw = ctk.CTkSwitch(
            self, text="Bu değerleri varsayılan olarak hatırla",
            variable=self.remember_var,
            font=ctk.CTkFont(size=12)
        )
        remember_sw.pack(pady=(12, 0), padx=30, anchor="w")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20, padx=30)

        cancel_btn = ctk.CTkButton(
            btn_frame, text="İptal", width=120, height=36,
            fg_color="transparent", border_width=1,
            text_color=("black", "white"),
            command=self.destroy
        )
        cancel_btn.pack(side="left")

        confirm_btn = ctk.CTkButton(
            btn_frame, text="Paylaşımı Başlat", width=150, height=36,
            font=ctk.CTkFont(weight="bold"),
            fg_color="#6366f1", hover_color="#4f46e5",
            command=self.confirm
        )
        confirm_btn.pack(side="right")

    def confirm(self):
        try:
            d_limit = int(self.downloads_entry.get())
            t_limit = int(self.time_entry.get())
            if d_limit < 0 or t_limit < 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Hata", "Lütfen geçerli pozitif sayılar girin.")
            return

        # Hatırla seçiliyse kaydet
        if self.remember_var.get():
            self.settings["default_download_limit"] = d_limit
            self.settings["default_time_limit"] = t_limit
            settings_manager.save(self.settings)

        self.on_confirm(d_limit, t_limit)
        self.destroy()

class PyTransferGUI:
    """
    Masaüstü kullanıcı arayüzünü ve kullanıcı etkileşimlerini (dosya paylaşımı,
    sunucu kontrolü, sekme güncellemeleri, pano takibi vb.) yöneten ana denetleyici sınıftır.
    """
    def __init__(self, root, file_manager, start_server_callback, stop_server_callback):
        """
        PyTransferGUI sınıfının kurucu metodudur. Arayüz pencerelerini ve
        güvenlik değişkenlerini yapılandırır.
        """
        self.root = root
        self.file_manager = file_manager
        self.start_server_cb = start_server_callback
        self.stop_server_cb = stop_server_callback

        self.settings = settings_manager.load()

        self.port = self.settings["port"]
        self.server_running = False
        self._server_starting = False  # üst üste tıklamayı engeller
        self.qr_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "qr_code.png")

        self.root.title("PyTransfer - Mobil & Yerel Ağ Dosya Transferi")
        self.root.minsize(950, 660)

        win_w, win_h = 950, 660
        self.root.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = (screen_w - win_w) // 2
        y = (screen_h - win_h) // 2
        self.root.geometry(f"{win_w}x{win_h}+{x}+{y}")

        try:
            import sys as _sys
            _base = getattr(_sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            icon_path = os.path.join(_base, "assets", "logo.ico")
            if os.path.exists(icon_path):   
                self.root.iconbitmap(icon_path)
        except Exception:
            pass

        self.root.grid_columnconfigure(0, weight=0, minsize=380)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        self.root.configure(fg_color=("#F8FAFC", "gray14"))

        self.labeled_ips = utils.get_labeled_ips()
        self.selected_ip = self.labeled_ips[0]['ip'] if self.labeled_ips else "127.0.0.1"
        self.last_clipboard = ""
        self.auto_copy_var = tk.BooleanVar(value=True)
        self.otp_enabled_var = tk.BooleanVar(value=self.settings["otp_enabled"])
        self.auto_start_var = tk.BooleanVar(value=self.settings["auto_start_server"])
        self.auto_start_var.trace_add("write", lambda *_: self._save_auto_start())

        self.security_enabled_var = tk.BooleanVar(value=self.settings["security_enabled"])
        import random
        self.pin_code = str(random.randint(1000, 9999))
        core.pin_code = self.pin_code
        core.security_enabled = self.settings["security_enabled"]
        core.otp_enabled = self.settings["otp_enabled"]
        core.pin_changed_callback = self.on_pin_changed_by_server

        saved_dl = self.settings.get("download_dir", "")
        if saved_dl and os.path.isdir(saved_dl):
            self.file_manager.set_download_dir(saved_dl)

        theme_map = {"Sistem": "System", "Karanlık": "Dark", "Aydınlık": "Light"}
        ctk.set_appearance_mode(theme_map.get(self.settings["theme"], "System"))

        self.left_panel = LeftPanel(self.root, self)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

        self.right_panel = RightPanel(self.root, self)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)

        self.left_panel.update_pin_display(self.pin_code, self.settings["security_enabled"])

        self.update_qr_code()
        self.refresh_shared_files_list()
        self.refresh_received_files_list()

        self.poll_clipboard()
        self.poll_connected_clients()

        try:
            from tkinterdnd2 import DND_FILES
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.on_file_drop)
            self.add_log("SÜRÜKLE-BIRAK: Dosya sürükle-bırak aktif.")
        except Exception as e:
            self.add_log(f"SÜRÜKLE-BIRAK UYARI: Sürükle-bırak aktif edilemedi: {e}")

        if self.settings["auto_start_server"]:
            self.root.after(500, self.toggle_server)
            
        self.update_speeds()

    def update_speeds(self):
        """
        Her 1 saniyede bir core.transfer_stats üzerinden ağ hızını okuyup arayüzü günceller.
        """
        down_speed = core.transfer_stats.get("download_bytes_sec", 0) / (1024 * 1024)
        up_speed = core.transfer_stats.get("upload_bytes_sec", 0) / (1024 * 1024)
        active_dl = core.transfer_stats.get("active_downloads", 0)
        active_up = core.transfer_stats.get("active_uploads", 0)
        
        if hasattr(self.right_panel, 'queue_label'):
            self.right_panel.queue_label.configure(text=f"[Kuyruk: {active_dl} İndirme, {active_up} Yükleme]")

        self.right_panel.speed_label.configure(
            text=f"↓ {down_speed:.1f} MB/s | ↑ {up_speed:.1f} MB/s"
        )
        
        # Dinamik detay güncellemesi
        if hasattr(self, '_shared_detail_labels'):
            shared_list = self.file_manager.get_all_shared()
            
            # Liste boyutu değişmişse veya arka planda dosya silinmişse listeyi komple yenile
            if len(shared_list) != len(self._shared_detail_labels):
                self.refresh_shared_files_list()
            else:
                import time
                up_speed_bytes = core.transfer_stats.get("upload_bytes_sec", 0)
                
                for file_info in shared_list:
                    f_id = file_info['id']
                    if f_id in self._shared_detail_labels:
                        d_limit = file_info.get('max_downloads', 0)
                        c_down = file_info.get('current_downloads', 0)
                        exp_at = file_info.get('expires_at')
                        
                        dl_text = f"{c_down}/{d_limit}" if d_limit > 0 else f"{c_down} (Limitsiz)"
                        
                        time_left_text = "Yok"
                        if exp_at:
                            rem_sec = max(0, int(exp_at - time.time()))
                            time_left_text = f"{rem_sec // 60} dk {rem_sec % 60} sn"
                            
                        file_size_str = utils.format_size(file_info['size'])
                        detail_text = f"İndirme: {dl_text}  |  Kalan Süre: {time_left_text}  |  Boyut: {file_size_str}"
                        self._shared_detail_labels[f_id].configure(text=detail_text)
                        
        self.root.after(1000, self.update_speeds)

    def on_ip_changed(self, selected_label):
        """
        Kullanıcı arayüzden ağ arayüzünü (IP adresini) değiştirdiğinde tetiklenir
        ve QR kodu yeni IP adresine göre yeniden üretir.
        """
        for item in self.labeled_ips:
            if item['label'] == selected_label:
                self.selected_ip = item['ip']
                break
        self.update_qr_code()

    def update_qr_code(self):
        """
        Geçerli IP, port ve varsa güvenlik PIN kodunu içeren yeni bir QR kodu oluşturur
        ve sol panelde gösterir.
        """
        url = f"http://{self.selected_ip}:{self.port}"
        
        qr_url = url
        if self.security_enabled_var.get() and self.pin_code:
            qr_url = f"{url}?pin={self.pin_code}"
            
        self.left_panel.url_entry.configure(state="normal")
        self.left_panel.url_entry.delete(0, "end")
        self.left_panel.url_entry.insert(0, url)
        self.left_panel.url_entry.configure(state="readonly")
        
        try:
            utils.generate_qr(qr_url, self.qr_path)
            
            pil_img = Image.open(self.qr_path)
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(160, 160))
            
            self.left_panel.qr_image_label.configure(image=ctk_img, text="")
        except Exception as e:
            self.left_panel.qr_image_label.configure(image=None, text=f"QR Kod Üretilemedi\n{e}")

    def copy_url_to_clipboard(self):
        """
        Sunucu URL bağlantısını (güvenlik aktifse otomatik PIN parametresini de ekleyerek)
        bilgisayarın panosuna kopyalar.
        """
        url = self.left_panel.url_entry.get()
        if self.security_enabled_var.get() and self.pin_code:
            url = f"{url}?pin={self.pin_code}"
        self.root.clipboard_clear()
        self.root.clipboard_append(url)
        messagebox.showinfo("Başarılı", "Bağlantı adresi panoya kopyalandı!")

    def browse_download_folder(self):
        """
        Kullanıcıya dosya seçim penceresi açarak gelen dosyaların
        kaydedileceği dizini değiştirmesini sağlar.
        """
        folder = filedialog.askdirectory(initialdir=self.file_manager.download_dir)
        if folder:
            folder = os.path.abspath(folder)
            if self.file_manager.set_download_dir(folder):
                self.right_panel.dl_path_entry.configure(state="normal")
                self.right_panel.dl_path_entry.delete(0, "end")
                self.right_panel.dl_path_entry.insert(0, folder)
                self.right_panel.dl_path_entry.configure(state="readonly")
                self.settings["download_dir"] = folder
                settings_manager.save(self.settings)
                self.add_log(f"AYAR: Gelen dosyaların kayıt yolu güncellendi: {folder}")
            else:
                messagebox.showerror("Hata", "Geçersiz dizin seçildi.")

    def change_theme(self, choice):
        """
        Uygulamanın arayüz temasını (Karanlık, Aydınlık veya Sistem) değiştirir ve kaydeder.
        """
        modes = {"Sistem": "System", "Karanlık": "Dark", "Aydınlık": "Light"}
        ctk.set_appearance_mode(modes.get(choice, "System"))
        self.settings["theme"] = choice
        settings_manager.save(self.settings)

    def _save_auto_start(self):
        """Otomatik başlat switch'i değişince ayarı kaydeder."""
        self.settings["auto_start_server"] = self.auto_start_var.get()
        settings_manager.save(self.settings)

    def _get_port_entry(self):
        """
        Ayarlar popup'ı açıksa port_entry widget'ını döndürür, değilse None.
        """
        rp = self.right_panel
        if (hasattr(rp, 'port_entry') and rp.port_entry is not None
                and rp.port_entry.winfo_exists()):
            return rp.port_entry
        return None

    def toggle_server(self):
        """
        Sunucunun çalışma durumunu tersine çevirir.
        Başlatma/durdurma işlemleri thread'de yapılır, UI donmaz.
        """
        if self._server_starting:
            return

        if not self.server_running:
            if self.port < 1024 or self.port > 65535:
                messagebox.showerror("Hata", "Lütfen ayarlardan 1024 ile 65535 arasında geçerli bir port girin.")
                return

            self._server_starting = True
            self.left_panel.server_toggle_btn.configure(
                text="Başlatılıyor...",
                state="normal",
                fg_color="#f59e0b",
                hover_color="#f59e0b",
                text_color="white"
            )
            self.left_panel.ip_combobox.configure(state="disabled")
            port_entry = self._get_port_entry()
            if port_entry:
                port_entry.configure(state="disabled")

            self.update_qr_code()

            def _start():
                self.start_server_cb(self.selected_ip, self.port)
                self.root.after(0, self._on_server_started)

            threading.Thread(target=_start, daemon=True).start()
        else:
            self.left_panel.server_toggle_btn.configure(
                text="Durduruluyor...",
                state="normal",
                fg_color="#6b7280",
                hover_color="#6b7280",
                text_color="white"
            )
            self.server_running = False  # poll döngülerini hemen durdur

            def _stop():
                self.stop_server_cb()
                self.root.after(0, self._on_server_stopped)

            threading.Thread(target=_stop, daemon=True).start()

    def _on_server_started(self):
        """Sunucu başarıyla başladıktan sonra UI'ı günceller."""
        self._server_starting = False
        self.server_running = True
        self.left_panel.server_toggle_btn.configure(
            text="Sunucuyu Durdur", state="normal",
            fg_color="#ef4444", hover_color="#dc2626",
            text_color=("#fff", "#fff")
        )
        self.left_panel.status_frame.configure(fg_color=("#dcfce7", "#143f24"))
        self.left_panel.status_indicator.configure(text="● Sunucu Aktif", text_color="#10b981")
        self.add_log(f"BİLGİ: Sunucu başlatıldı -> http://{self.selected_ip}:{self.port}")

    def _on_server_stopped(self):
        """Sunucu başarıyla durdurulduktan sonra UI'ı günceller."""
        self.left_panel.server_toggle_btn.configure(
            text="Sunucuyu Başlat", state="normal",
            fg_color="#10b981", hover_color="#059669",
            text_color=("#fff", "#fff")
        )
        self.left_panel.status_frame.configure(fg_color=("#fee2e2", "#3f1a1a"))
        self.left_panel.status_indicator.configure(text="● Durduruldu", text_color="#ef4444")
        port_entry = self._get_port_entry()
        if port_entry:
            port_entry.configure(state="normal")
        self.left_panel.ip_combobox.configure(state="normal")
        self.add_log("BİLGİ: Sunucu durduruldu.")

    def _get_file_icon(self, filename):
        if not hasattr(self, '_icons_cache'):
            self._icons_cache = {}
            import os
            from PIL import Image
            import customtkinter as ctk
            
            icon_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icons")
            icon_map = {
                "video": ["mp4", "mkv", "avi", "mov", "wmv"],
                "audio": ["mp3", "wav", "ogg", "flac", "m4a"],
                "image": ["jpg", "jpeg", "png", "gif", "webp", "bmp"],
                "archive": ["zip", "rar", "7z", "tar", "gz"],
                "document": ["txt", "pdf", "doc", "docx", "xls", "xlsx", "py", "js", "html", "css", "md"]
            }
            
            for icon_name, exts in icon_map.items():
                try:
                    img = Image.open(os.path.join(icon_dir, f"{icon_name}.png"))
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(16, 16))
                    for ext in exts:
                        self._icons_cache[ext] = ctk_img
                except Exception:
                    pass
            try:
                def_img = Image.open(os.path.join(icon_dir, "default.png"))
                self._default_icon = ctk.CTkImage(light_image=def_img, dark_image=def_img, size=(16, 16))
            except Exception:
                self._default_icon = None

        ext = filename.split('.')[-1].lower() if '.' in filename else ""
        return self._icons_cache.get(ext, getattr(self, '_default_icon', None))

    def refresh_shared_files_list(self):
        """
        Mevcut paylaşılan dosyaları dosya yöneticisinden çeker ve listede günceller.
        """
        for widget in self.right_panel.shared_scrollable.winfo_children():
            widget.destroy()
            
        shared_list = self.file_manager.get_all_shared()
        
        if not shared_list:
            container = ctk.CTkFrame(self.right_panel.shared_scrollable, fg_color="transparent")
            container.pack(expand=True, fill="both", padx=25, pady=20)
            
            title_lbl = ctk.CTkLabel(
                container, 
                text="Paylaşım Başlatın",
                font=ctk.CTkFont(family="Outfit", size=18, weight="bold"),
                text_color=("#6366f1", "#818cf8")
            )
            title_lbl.pack(pady=(5, 5))
            
            desc_lbl = ctk.CTkLabel(
                container, 
                text="Dosya veya klasör göndermek için aşağıdaki adımları takip edin:",
                font=ctk.CTkFont(size=12, slant="italic"),
                text_color=("#475569", "#94a3b8")
            )
            desc_lbl.pack(pady=(0, 15))
            
            steps = [
                ("1", "Ağ Arayüzü Seçin", "Sol panelden cihazınızın bağlı olduğu IP adresini belirleyin."),
                ("2", "Sunucuyu Başlatın", "Sol alttaki 'Sunucuyu Başlat' butonuna basarak ağ yayınını açın."),
                ("3", "Dosya/Klasör Ekleyin", "Aşağıdaki butonları kullanarak paylaşmak istediğiniz ögeleri seçin."),
                ("4", "Cihazı Bağlayın", "Telefonunuzdan QR kodu taratın veya bağlantıyı açıp PIN şifresini girin.")
            ]
            
            for num, title, detail in steps:
                step_frame = ctk.CTkFrame(container, fg_color=("#e2e8f0", "#1e293b"), corner_radius=8)
                step_frame.pack(fill="x", pady=5, ipady=4)
                
                num_badge = ctk.CTkLabel(
                    step_frame, 
                    text=f" {num} ", 
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color="white",
                    fg_color="#6366f1",
                    corner_radius=4,
                    width=22,
                    height=22
                )
                num_badge.pack(side="left", padx=(12, 12), pady=6)
                
                text_frame = ctk.CTkFrame(step_frame, fg_color="transparent")
                text_frame.pack(side="left", fill="both", expand=True, pady=4)
                
                heading_lbl = ctk.CTkLabel(
                    text_frame, 
                    text=title, 
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=("#1e293b", "#f1f5f9"),
                    anchor="w"
                )
                heading_lbl.pack(fill="x", anchor="w")
                
                detail_lbl = ctk.CTkLabel(
                    text_frame, 
                    text=detail, 
                    font=ctk.CTkFont(size=11),
                    text_color=("#475569", "#94a3b8"),
                    anchor="w"
                )
                detail_lbl.pack(fill="x", anchor="w")
            
            self._shared_detail_labels = {}
            return

        self.selected_shared_vars = {}
        self._shared_detail_labels = {}
        import time

        for file_info in shared_list:
            row_frame = ctk.CTkFrame(self.right_panel.shared_scrollable, fg_color=("#f8fafc", "#1e293b"), corner_radius=8)
            row_frame.pack(fill="x", padx=5, pady=4)
            
            var = tk.BooleanVar(value=False)
            self.selected_shared_vars[file_info['id']] = var
            
            cb = ctk.CTkCheckBox(
                row_frame, 
                text="", 
                variable=var, 
                width=24,
                checkbox_height=20,
                checkbox_width=20
            )
            cb.pack(side="left", padx=(10, 5), pady=10)
            
            info_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
            
            file_name = file_info['name']
            display_name = file_name if len(file_name) <= 45 else file_name[:42] + "..."
            file_size_str = utils.format_size(file_info['size'])
            icon_img = self._get_file_icon(file_name)

            # Üst satır: İsim
            title_lbl = ctk.CTkLabel(
                info_frame, 
                text=f" {display_name}", 
                image=icon_img, 
                compound="left", 
                font=ctk.CTkFont(size=13, weight="bold"), 
                anchor="w"
            )
            title_lbl.pack(fill="x", anchor="w")

            # Alt satır: boyut | indirme | süre
            d_limit = file_info.get('max_downloads', 0)
            c_down = file_info.get('current_downloads', 0)
            exp_at = file_info.get('expires_at')

            dl_text = f"{c_down}/{d_limit}" if d_limit > 0 else f"{c_down} (Limitsiz)"

            time_left_text = "Yok"
            if exp_at:
                rem_sec = max(0, int(exp_at - time.time()))
                time_left_text = f"{rem_sec // 60} dk {rem_sec % 60} sn"

            detail_text = f"İndirme: {dl_text}  |  Kalan Süre: {time_left_text}  |  Boyut: {file_size_str}"
            detail_lbl = ctk.CTkLabel(info_frame, text=detail_text, font=ctk.CTkFont(size=11), text_color=("#64748b", "#94a3b8"), anchor="w")
            detail_lbl.pack(fill="x", anchor="w")
            
            self._shared_detail_labels[file_info['id']] = detail_lbl

    def share_file_dialog(self):
        """
        Paylaşılacak dosyaların seçilmesi için dosya seçici dialog pencerelerini açar.
        """
        filepaths = filedialog.askopenfilenames(title="Paylaşılacak Dosya(ları) Seçin")
        if filepaths:
            def on_confirm(d_limit, t_limit):
                import time
                expires_at = time.time() + (t_limit * 60) if t_limit > 0 else None
                for path in filepaths:
                    file_obj = self.file_manager.add_shared_file(path)
                    if file_obj:
                        file_obj.max_downloads = d_limit
                        file_obj.expires_at = expires_at
                        self.add_log(f"PAYLAŞIM: {file_obj.name} paylaşıma açıldı. Limit: {d_limit if d_limit>0 else 'Yok'}")
                self.refresh_shared_files_list()
                
            LimitDialog(self.root, len(filepaths), on_confirm, self.settings)

    def share_folder_dialog(self):
        """
        Paylaşılacak bir klasörün seçilmesini sağlar ve arka planda sıkıştırma işlemini tetikler.
        """
        folderpath = filedialog.askdirectory(title="Paylaşılacak Klasörü Seçin")
        if folderpath:
            folderpath = os.path.normpath(folderpath)
            folder_name = os.path.basename(folderpath)
            
            def on_confirm(d_limit, t_limit):
                zip_target_dir = os.path.join(self.file_manager.download_dir, ".temp_shares")
                os.makedirs(zip_target_dir, exist_ok=True)
                
                zip_filename = f"{folder_name}.zip"
                zip_path = os.path.join(zip_target_dir, zip_filename)
                
                if os.path.exists(zip_path):
                    try:
                        os.remove(zip_path)
                    except Exception:
                        import time
                        zip_filename = f"{folder_name}_{int(time.time())}.zip"
                        zip_path = os.path.join(zip_target_dir, zip_filename)
                
                self.add_log(f"PAYLAŞIM: '{folder_name}' klasörü sıkıştırılıyor (ZIP)... Lütfen bekleyin.")
                
                threading.Thread(
                    target=self._compress_folder_thread,
                    args=(folderpath, zip_path, folder_name, d_limit, t_limit),
                    daemon=True
                ).start()
                
            LimitDialog(self.root, 1, on_confirm, self.settings)

    def _compress_folder_thread(self, folderpath, zip_path, folder_name, d_limit, t_limit):
        """
        Arayüzün donmasını engellemek için arka planda bir thread üzerinde sıkıştırma işlemi yürütür.
        """
        self.root.after(0, lambda: self.right_panel.add_folder_btn.configure(state="disabled", text="Sıkıştırılıyor..."))
        self.root.after(0, lambda: self.right_panel.add_file_btn.configure(state="disabled"))
        self.root.after(0, lambda: self.right_panel.clear_selected_btn.configure(state="disabled"))
        
        self.root.after(0, lambda: self.right_panel.zip_progress_frame.grid())
        self.root.after(0, lambda: self.right_panel.zip_progress.set(0.0))
        self.root.after(0, lambda: self.right_panel.zip_label.configure(text=f"Klasör sıkıştırılıyor ({folder_name}): %0"))
        
        def progress_cb(progress, current_file=""):
            percent = int(progress * 100)
            self.root.after(0, lambda p=progress: self.right_panel.zip_progress.set(p))
            self.root.after(0, lambda pc=percent: self.right_panel.zip_label.configure(text=f"Klasör sıkıştırılıyor ({folder_name}): %{pc}"))
        try:
            utils.zip_folder_with_progress(folderpath, zip_path, progress_cb)
            self.root.after(0, self._on_zip_success, zip_path, folder_name, d_limit, t_limit)
        except Exception as e:
            self.root.after(0, self._on_zip_failure, folder_name, str(e))

    def _on_zip_success(self, zip_path, folder_name, d_limit, t_limit):
        """
        Sıkıştırma işlemi başarıyla bittiğinde dosyayı paylaşıma açar ve arayüzü sıfırlar.
        """
        import time
        expires_at = time.time() + (t_limit * 60) if t_limit > 0 else None
        
        file_obj = self.file_manager.add_shared_file(zip_path)
        if file_obj:
            file_obj.max_downloads = d_limit
            file_obj.expires_at = expires_at
            self.add_log(f"PAYLAŞIM: '{folder_name}' klasörü ZIP olarak paylaşıldı. Limit: {d_limit if d_limit>0 else 'Yok'}")
        self.refresh_shared_files_list()
        
        self.right_panel.zip_progress_frame.grid_remove()
        
        self.right_panel.add_folder_btn.configure(state="normal", text=" Klasör Paylaş (ZIP)")
        self.right_panel.add_file_btn.configure(state="normal")
        self.right_panel.clear_selected_btn.configure(state="normal")

    def _on_zip_failure(self, folder_name, error_msg):
        """
        Sıkıştırma işlemi başarısız olduğunda kullanıcıya hata mesajı gösterir.
        """
        self.add_log(f"HATA: Sıkıştırma hatası ({folder_name}) - {error_msg}")
        messagebox.showerror("Hata", f"Klasör sıkıştırılırken hata oluştu:\n{error_msg}")
        
        self.right_panel.zip_progress_frame.grid_remove()
        
        self.right_panel.add_folder_btn.configure(state="normal", text=" Klasör Paylaş (ZIP)")
        self.right_panel.add_file_btn.configure(state="normal")
        self.right_panel.clear_selected_btn.configure(state="normal")

    def remove_selected_share(self):
        """
        Kullanıcının seçtiği paylaşılan dosyayı listeden ve paylaşımdan kaldırır.
        """
        if not hasattr(self, 'selected_shared_vars'):
            return
            
        removed_any = False
        for f_id, var in self.selected_shared_vars.items():
            if var.get():
                file_obj = self.file_manager.get_shared_file(f_id)
                if file_obj:
                    self.add_log(f"PAYLAŞIM: {file_obj.name} paylaşımdan kaldırıldı.")
                self.file_manager.remove_shared_file(f_id)
                removed_any = True
                
        if not removed_any:
            messagebox.showwarning("Uyarı", "Lütfen kaldırmak istediğiniz paylaşılan dosyaları seçin.")
            return
            
        self.refresh_shared_files_list()


    def refresh_received_files_list(self):
        """
        Gelen (indirilen) dosyalar dizinini tarar ve gelen dosyalar sekmesinde günceller.
        """
        for widget in self.right_panel.received_scrollable.winfo_children():
            widget.destroy()

        received_files = []
        if os.path.exists(self.file_manager.download_dir):
            for entry in os.scandir(self.file_manager.download_dir):
                if entry.is_file() and not entry.name.startswith('.'):
                    stat = entry.stat()
                    received_files.append({
                        "name": entry.name,
                        "path": entry.path,
                        "size": stat.st_size,
                        "mtime": stat.st_mtime,
                    })

        # En yeni dosya üstte
        received_files.sort(key=lambda x: x["mtime"], reverse=True)

        if not received_files:
            no_files_label = ctk.CTkLabel(
                self.right_panel.received_scrollable,
                text="Henüz hiçbir dosya alınmadı.\nBağlı cihazlar üzerinden dosya yükleyebilirsiniz.",
                font=ctk.CTkFont(size=12),
                text_color="gray",
                pady=40
            )
            no_files_label.pack(expand=True, fill="both")
            return

        import datetime
        for file_info in received_files:
            # Giden dosyalarla aynı card stili
            row_frame = ctk.CTkFrame(
                self.right_panel.received_scrollable,
                fg_color=("#f8fafc", "#1e293b"),
                corner_radius=8
            )
            row_frame.pack(fill="x", padx=5, pady=4)

            # Sol: ikon + bilgi
            info_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=6)

            file_name = file_info['name']
            display_name = file_name if len(file_name) <= 42 else file_name[:39] + "..."
            file_size_str = utils.format_size(file_info['size'])
            file_path = file_info['path']
            icon_img = self._get_file_icon(file_name)

            # Üst satır: ikon + isim
            name_lbl = ctk.CTkLabel(
                info_frame,
                text=f" {display_name}",
                image=icon_img,
                compound="left",
                font=ctk.CTkFont(size=13, weight="bold"),
                anchor="w"
            )
            name_lbl.pack(fill="x", anchor="w")

            # Alt satır: tarih | boyut
            mtime_str = datetime.datetime.fromtimestamp(file_info['mtime']).strftime("%d.%m.%Y %H:%M")
            ext_type = file_name.split('.')[-1].upper() if '.' in file_name else "Bilinmeyen"
            detail_lbl = ctk.CTkLabel(
                info_frame,
                text=f"Alınma Zamanı: {mtime_str}  |  Tür: {ext_type}  |  Boyut: {file_size_str}",
                font=ctk.CTkFont(size=11),
                text_color=("#64748b", "#94a3b8"),
                anchor="w"
            )
            detail_lbl.pack(fill="x", anchor="w")

            # Sağ: Aç butonu
            open_btn = ctk.CTkButton(
                row_frame,
                text="Aç",
                width=52,
                height=28,
                font=ctk.CTkFont(size=11),
                fg_color=("#6366f1", "#4f46e5"),
                hover_color=("#4f46e5", "#3730a3"),
                command=lambda p=file_path: self.open_file_system(p)
            )
            open_btn.pack(side="right", padx=10, pady=8)

    def open_downloads_folder(self):
        """
        Gelen dosyaların saklandığı kayıt klasörünü işletim sistemi üzerinde açar.
        """
        if os.path.exists(self.file_manager.download_dir):
            os.startfile(self.file_manager.download_dir)
        else:
            messagebox.showerror("Hata", "Dosya saklama klasörü bulunamadı.")

    def open_file_system(self, filepath):
        """
        Belirtilen dosya yoluna sahip dosyayı varsayılan ilişkili programla açar.
        """
        try:
            if os.path.exists(filepath):
                os.startfile(filepath)
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya açılamadı:\n{e}")

    def add_log(self, message):
        """
        Sunucu günlük sekmesine yeni bir mesaj eklemek üzere thread-safe arayüz kuyruğu çağırır.
        """
        try:
            self.root.after(0, self._add_log_ui, message)
        except Exception:
            pass

    def _add_log_ui(self, message):
        """
        Sunucu günlüğüne tarih damgalı log ekler ve sol paneldeki canlı aktivite alanını günceller.
        """
        import datetime
        timestamp = datetime.datetime.now().strftime("[%H:%M:%S]")
        formatted_message = f"{timestamp} {message}\n"
        
        self.right_panel.logs_textbox.configure(state="normal")
        self.right_panel.logs_textbox.insert("end", formatted_message)
        self.right_panel.logs_textbox.configure(state="disabled")
        self.right_panel.logs_textbox.see("end")
        
        clean_msg = message
        if ": " in clean_msg:
            clean_msg = clean_msg.split(": ", 1)[1]
            
        self.left_panel.update_activity(clean_msg)

    def clear_logs(self):
        """
        Sunucu günlük panelindeki tüm geçmiş metinleri temizler.
        """
        self.right_panel.logs_textbox.configure(state="normal")
        self.right_panel.logs_textbox.delete("1.0", "end")
        self.right_panel.logs_textbox.configure(state="disabled")

    def _set_clipboard_text(self, text):
        """Clipboard textbox'a metin yazar, placeholder mantığını yönetir."""
        tb = self.right_panel.clipboard_textbox
        clip_tab = self.right_panel.clipboard_tab_view
        tb.delete("1.0", "end")
        if text:
            tb.insert("1.0", text)
            tb.configure(text_color=("#0f172a", "#f1f5f9"))
            clip_tab._placeholder_active = False
        else:
            tb.insert("1.0", clip_tab._placeholder)
            tb.configure(text_color=("#94a3b8", "#64748b"))
            clip_tab._placeholder_active = True

    def poll_clipboard(self):
        """
        Flask sunucusu üzerindeki panoyu her 1 saniyede bir kontrol eder ve değişiklik varsa kopyalar.
        """
        current_server_clip = core.clipboard_text
        if current_server_clip != self.last_clipboard:
            self.last_clipboard = current_server_clip
            self._set_clipboard_text(current_server_clip)

            if self.auto_copy_var.get() and current_server_clip:
                try:
                    self.root.clipboard_clear()
                    self.root.clipboard_append(current_server_clip)
                except Exception:
                    pass

        current_history = list(core.clipboard_history)
        if current_history != getattr(self, 'last_clipboard_history', None):
            self.last_clipboard_history = current_history
            self.refresh_clipboard_history_ui()

        self.root.after(1000, self.poll_clipboard)

    def send_to_server_clipboard(self):
        """
        Arayüzdeki metin alanında yazılı metni ortak panoya yükler.
        """
        clip_tab = self.right_panel.clipboard_tab_view
        if clip_tab._placeholder_active:
            messagebox.showwarning("Uyarı", "Göndermek için bir metin yazın.")
            return
        text = self.right_panel.clipboard_textbox.get("1.0", "end-1c").strip()
        routes.update_clipboard_text(text)
        self.last_clipboard = text
        self.add_log(f"BİLGİ: Arayüzden ortak panoya metin eklendi.")
        messagebox.showinfo("Başarılı", "Metin ortak panoya kaydedildi!")

    def select_history_clip(self, text):
        """
        Pano geçmişinden bir öğe seçildiğinde onu aktif pano metni yapar ve günceller.
        """
        self._set_clipboard_text(text)
        routes.update_clipboard_text(text)
        self.last_clipboard = text
        self.add_log("BİLGİ: Geçmişten pano öğesi seçildi.")

    def refresh_clipboard_history_ui(self):
        """
        Pano geçmişi arayüzünü günceller.
        """
        for widget in self.right_panel.clip_history_scrollable.winfo_children():
            widget.destroy()
            
        history = list(core.clipboard_history)
        if not history:
            no_history_label = ctk.CTkLabel(
                self.right_panel.clip_history_scrollable, 
                text="Geçmiş boş.",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            no_history_label.pack(pady=20)
            return
            
        for text in history:
            item_frame = ctk.CTkFrame(self.right_panel.clip_history_scrollable, fg_color="transparent")
            item_frame.pack(fill="x", pady=2, padx=2)
            
            display_text = text.replace("\n", " ")
            if len(display_text) > 35:
                display_text = display_text[:32] + "..."
                
            btn = ctk.CTkButton(
                item_frame, 
                text=display_text, 
                font=ctk.CTkFont(size=12),
                anchor="w",
                fg_color=("#f1f5f9", "#1e293b"),
                text_color=("#1e293b", "#f1f5f9"),
                hover_color=("#e2e8f0", "#334155"),
                command=lambda t=text: self.select_history_clip(t)
            )
            btn.pack(fill="x", expand=True)

    def poll_connected_clients(self):
        """
        Sunucuya bağlı olan cihazları periyodik olarak kontrol eder ve listeyi günceller.
        """
        if self.server_running:
            import time
            now = time.time()
            clients_list = []
            
            for ip, info in list(core.active_clients.items()):
                if now - info['last_seen'] < 60:
                    clients_list.append({
                        "ip": ip,
                        "device": info['device'],
                        "status": "blocked" if ip in core.blocked_clients else "active",
                        "last_seen_str": "Şimdi" if now - info['last_seen'] < 5 else f"{int(now - info['last_seen'])} sn önce"
                    })
                    
            for ip in core.blocked_clients:
                if not any(item['ip'] == ip for item in clients_list):
                    clients_list.append({
                        "ip": ip,
                        "device": core.active_clients.get(ip, {}).get('device', 'Bilinmeyen Cihaz'),
                        "status": "blocked",
                        "last_seen_str": "Engellendi"
                    })
            
            self.refresh_clients_ui(clients_list)
            self.refresh_servers_ui(list(core.discovered_servers.values()))
            
        self.root.after(2000, self.poll_connected_clients)

    def refresh_clients_ui(self, clients_list):
        """
        Bağlı cihazlar listesini UI üzerinde günceller.
        """
        for widget in self.right_panel.clients_scrollable.winfo_children():
            widget.destroy()
            
        if not clients_list:
            no_clients_label = ctk.CTkLabel(
                self.right_panel.clients_scrollable, 
                text="Aktif bağlı cihaz yok.",
                font=ctk.CTkFont(size=12),
                text_color="gray",
                pady=40
            )
            no_clients_label.pack(expand=True, fill="both")
            return
            
        for client in clients_list:
            row_frame = ctk.CTkFrame(self.right_panel.clients_scrollable, fg_color=("#f1f5f9", "#1e293b"), corner_radius=8)
            row_frame.pack(fill="x", padx=5, pady=4, ipady=4)
            
            device_text = f"{client['device']} ({client['ip']})"
            display_device = device_text if len(device_text) <= 35 else device_text[:32] + "..."
            
            if client['status'] == 'active':
                block_btn = ctk.CTkButton(
                    row_frame, 
                    text="Engelle", 
                    fg_color="#ef4444", 
                    hover_color="#dc2626",
                    width=80,
                    height=28,
                    command=lambda ip=client['ip']: self.block_client_ip(ip)
                )
                block_btn.pack(side="right", padx=10, pady=5)
            else:
                unblock_btn = ctk.CTkButton(
                    row_frame, 
                    text="Kaldır", 
                    fg_color="#10b981", 
                    hover_color="#059669",
                    width=80,
                    height=28,
                    command=lambda ip=client['ip']: self.unblock_client_ip(ip)
                )
                unblock_btn.pack(side="right", padx=10, pady=5)
            
            info_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)
            
            device_lbl = ctk.CTkLabel(
                info_frame, 
                text=display_device, 
                font=ctk.CTkFont(size=13, weight="bold"),
                anchor="w"
            )
            device_lbl.pack(fill="x")
            
            status_lbl = ctk.CTkLabel(
                info_frame, 
                text=f"Durum: {client['status'].upper()} | Görülme: {client['last_seen_str']}", 
                font=ctk.CTkFont(size=11),
                text_color="gray",
                anchor="w"
            )
            status_lbl.pack(fill="x")

    def refresh_servers_ui(self, servers_list):
        """
        Ağda keşfedilen diğer PyTransfer sunucularını günceller.
        """
        for widget in self.right_panel.servers_scrollable.winfo_children():
            widget.destroy()
            
        if not servers_list:
            no_servers_label = ctk.CTkLabel(
                self.right_panel.servers_scrollable, 
                text="Ağda başka cihaz bulunamadı.",
                font=ctk.CTkFont(size=12),
                text_color="gray",
                pady=40
            )
            no_servers_label.pack(expand=True, fill="both")
            return
            
        import webbrowser
        for server in servers_list:
            row_frame = ctk.CTkFrame(self.right_panel.servers_scrollable, fg_color=("#f1f5f9", "#1e293b"), corner_radius=8)
            row_frame.pack(fill="x", padx=5, pady=4, ipady=4)
            
            server_name = server['name']
            display_server = server_name if len(server_name) <= 35 else server_name[:32] + "..."
            
            connect_btn = ctk.CTkButton(
                row_frame, 
                text="Bağlan", 
                fg_color="#3b82f6", 
                hover_color="#2563eb",
                width=80,
                height=28,
                command=lambda ip=server['ip'], port=server['port']: webbrowser.open(f"http://{ip}:{port}")
            )
            connect_btn.pack(side="right", padx=10, pady=5)
            
            info_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)
            
            device_lbl = ctk.CTkLabel(
                info_frame, 
                text=display_server, 
                font=ctk.CTkFont(size=13, weight="bold"),
                anchor="w"
            )
            device_lbl.pack(fill="x")
            
            status_lbl = ctk.CTkLabel(
                info_frame, 
                text=f"IP: {server['ip']}:{server['port']}", 
                font=ctk.CTkFont(size=11),
                text_color="gray",
                anchor="w"
            )
            status_lbl.pack(fill="x")

    def block_client_ip(self, ip):
        """
        Belirtilen IP adresini sunucu üzerinden engeller.
        """
        security.block_ip(ip)
        self.add_log(f"ENGEL: {ip} IP adresi engellendi.")
        
    def unblock_client_ip(self, ip):
        """
        Belirtilen IP adresinin engelini kaldırır.
        """
        security.unblock_ip(ip)
        self.add_log(f"ENGEL KALDIRILDI: {ip} IP adresinin engeli kaldırıldı.")

    def on_file_drop(self, event):
        """
        Pencereye sürüklenip bırakılan dosyaları/klasörleri yakalar ve paylaşıma sunar.
        """
        paths = utils.parse_dropped_paths(event.data)
        if not paths:
            return
            
        for path in paths:
            self.share_dropped_path(path)

    def share_dropped_path(self, path):
        """
        Sürüklenip bırakılan bir dosya veya klasörü otomatik olarak paylaşır.
        """
        if not os.path.exists(path):
            return
            
        if os.path.isdir(path):
            folderpath = os.path.normpath(path)
            folder_name = os.path.basename(folderpath)
            
            zip_target_dir = os.path.join(self.file_manager.download_dir, ".temp_shares")
            os.makedirs(zip_target_dir, exist_ok=True)
            
            zip_filename = f"{folder_name}.zip"
            zip_path = os.path.join(zip_target_dir, zip_filename)
            
            if os.path.exists(zip_path):
                import time
                zip_filename = f"{folder_name}_{int(time.time())}.zip"
                zip_path = os.path.join(zip_target_dir, zip_filename)
                
            self.add_log(f"PAYLAŞIM: Bırakılan '{folder_name}' klasörü sıkıştırılıyor (ZIP)... Lütfen bekleyin.")
            
            threading.Thread(
                target=self._compress_folder_thread,
                args=(folderpath, zip_path, folder_name),
                daemon=True
            ).start()
        else:
            file_obj = self.file_manager.add_shared_file(path)
            if file_obj:
                self.add_log(f"PAYLAŞIM: Bırakılan {file_obj.name} paylaşıma açıldı.")
                self.refresh_shared_files_list()

    def on_file_received_trigger(self, filepath):
        """
        Web istemcisinden yeni bir dosya yüklendiğinde tetiklenir, log ekler ve listeyi tazeler.
        """
        self.add_log(f"DOSYA ALINDI: {os.path.basename(filepath)}")
        self.root.after(0, self.refresh_received_files_list)

    def on_security_toggle(self):
        """
        PIN korumalı erişim ayarı açılıp kapatıldığında tetiklenir ve sunucuyu günceller.
        """
        enabled = self.security_enabled_var.get()
        core.security_enabled = enabled
        self.left_panel.update_pin_display(self.pin_code, enabled)
        self.update_qr_code()
        self.add_log(f"GÜVENLİK: PIN koruması {'aktif edildi' if enabled else 'devre dışı bırakıldı'}.")
        self.settings["security_enabled"] = enabled
        settings_manager.save(self.settings)

    def on_otp_toggle(self):
        """
        Tek Kullanımlık PIN (OTP) ayarı açılıp kapatıldığında tetiklenir.
        """
        enabled = self.otp_enabled_var.get()
        core.otp_enabled = enabled
        self.add_log(f"GÜVENLİK: Tek Kullanımlık PIN (OTP) {'aktif edildi' if enabled else 'devre dışı bırakıldı'}.")
        self.settings["otp_enabled"] = enabled
        settings_manager.save(self.settings)

    def update_custom_pin(self):
        """
        Kullanıcının ayarlardan girdiği özel PIN kodunu doğrular ve sunucuya tanımlar.
        """
        new_pin = self.right_panel.pin_entry.get().strip()
        if not new_pin:
            messagebox.showwarning("Uyarı", "Lütfen bir PIN kodu girin.")
            return
        if not new_pin.isdigit() or len(new_pin) < 4 or len(new_pin) > 6:
            messagebox.showerror("Hata", "PIN kodu sadece rakamlardan oluşmalı ve 4-6 hane uzunluğunda olmalıdır.")
            return
            
        self.pin_code = new_pin
        core.pin_code = self.pin_code
        self.left_panel.update_pin_display(self.pin_code, self.security_enabled_var.get())
        self.update_qr_code()
        self.add_log(f"GÜVENLİK: Erişim PIN kodu güncellendi: {self.pin_code}")
        messagebox.showinfo("Başarılı", f"Erişim PIN kodu başarıyla güncellendi: {self.pin_code}")

    def generate_new_pin(self):
        """
        Kullanıcı için rastgele 4 haneli yeni bir PIN kodu üretir ve günceller.
        """
        import random
        self.pin_code = str(random.randint(1000, 9999))
        core.pin_code = self.pin_code
        if hasattr(self.right_panel, 'pin_entry') and self.right_panel.pin_entry is not None and self.right_panel.pin_entry.winfo_exists():
            self.right_panel.pin_entry.delete(0, "end")
            self.right_panel.pin_entry.insert(0, self.pin_code)
        self.left_panel.update_pin_display(self.pin_code, self.security_enabled_var.get())
        self.update_qr_code()
        self.add_log(f"GÜVENLİK: Yeni rastgele PIN kodu üretildi: {self.pin_code}")

    def on_pin_changed_by_server(self, new_pin):
        """
        Sunucudaki PIN değiştiğinde (örneğin OTP ile) arayüzdeki PIN alanlarını ve QR kodu günceller.
        """
        self.root.after(0, self._update_pin_ui, new_pin)

    def _update_pin_ui(self, new_pin):
        """
        PIN kodu güncellemelerini UI bileşenlerine yansıtır.
        """
        self.pin_code = new_pin
        if hasattr(self.right_panel, 'pin_entry') and self.right_panel.pin_entry is not None and self.right_panel.pin_entry.winfo_exists():
            self.right_panel.pin_entry.delete(0, "end")
            self.right_panel.pin_entry.insert(0, new_pin)
        self.left_panel.update_pin_display(new_pin, self.security_enabled_var.get())
        self.update_qr_code()

    def cleanup(self):
        """
        Uygulama kapatılırken geçici QR resmi ve geçici ZIP dosyalarını diskten temizler.
        """
        if os.path.exists(self.qr_path):
            try:
                os.remove(self.qr_path)
            except Exception:
                pass
                
        temp_shares_dir = os.path.join(self.file_manager.download_dir, ".temp_shares")
        if os.path.exists(temp_shares_dir):
            import shutil
            try:
                shutil.rmtree(temp_shares_dir)
            except Exception:
                pass
