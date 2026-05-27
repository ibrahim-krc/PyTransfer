import os
import tkinter as tk
import customtkinter as ctk

class RightPanel(ctk.CTkFrame):
    """
    Uygulamanın sağ tarafındaki sekmeli panelleri (Paylaşılan Dosyalar,
    Gelen Dosyalar, Ortak Pano, Bağlı Cihazlar, Sunucu Günlükleri ve Ayarlar) yöneten sınıftır.
    """
    def __init__(self, parent, controller):
        """
        RightPanel sınıfı kurucusudur. Sekme yöneticisini ve düzeni kurar.
        """
        super().__init__(parent, corner_radius=0)
        self.controller = controller
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.create_widgets()

    def create_widgets(self):
        """
        Sekme yapısını oluşturur ve her sekmenin ilgili kurulum fonksiyonunu çağırır.
        Ayarlar sekmesi kaldırılmış olup sağ üst köşedeki ikon butonuyla açılır.
        """
        # Üst bar: ayarlar ikonu sağ üste
        self.top_bar = ctk.CTkFrame(self, fg_color="transparent", height=36)
        self.top_bar.grid(row=0, column=0, sticky="ew", padx=15, pady=(10, 0))
        self.top_bar.grid_columnconfigure(0, weight=1)
        self.top_bar.grid_propagate(False)
        self.queue_label = ctk.CTkLabel(
            self.top_bar,
            text="[Kuyruk: 0 İndirme, 0 Yükleme]",
            font=ctk.CTkFont(family="Outfit", size=11, weight="bold"),
            text_color=("#3b82f6", "#60a5fa")
        )
        self.queue_label.grid(row=0, column=1, sticky="e", padx=(0, 10))

        self.speed_label = ctk.CTkLabel(
            self.top_bar,
            text="↓ 0.0 MB/s | ↑ 0.0 MB/s",
            font=ctk.CTkFont(family="Outfit", size=11, weight="normal"),
            text_color=("#94a3b8", "#64748b")
        )
        self.speed_label.grid(row=0, column=2, sticky="e", padx=(0, 10))

        self.settings_btn = ctk.CTkButton(
            self.top_bar,
            text="⚙",
            width=34,
            height=30,
            font=ctk.CTkFont(size=18),
            fg_color="transparent",
            hover_color=("#e2e8f0", "#2d3748"),
            text_color=("#475569", "#94a3b8"),
            corner_radius=8,
            command=self.open_settings_window
        )
        self.settings_btn.grid(row=0, column=3, sticky="e")


        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=15, pady=(4, 15))

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        self.tab_shared = self.tabview.add("Paylaşılan Dosyalar")
        self.tab_received = self.tabview.add("Gelen Dosyalar")
        self.tab_clipboard = self.tabview.add("Ortak Pano")
        self.tab_clients = self.tabview.add("Bağlı Cihazlar")

        self.tab_history = self.tabview.add("Geçmiş")
        self.tab_logs = self.tabview.add("Sunucu Günlüğü")

        from .tabs import SharedTab, ReceivedTab, ClipboardTab, ClientsTab, LogsTab, HistoryTab

        self.shared_tab_view = SharedTab(self.tab_shared, self.controller)
        self.shared_tab_view.pack(fill="both", expand=True)

        self.received_tab_view = ReceivedTab(self.tab_received, self.controller)
        self.received_tab_view.pack(fill="both", expand=True)

        self.clipboard_tab_view = ClipboardTab(self.tab_clipboard, self.controller)
        self.clipboard_tab_view.pack(fill="both", expand=True)

        self.clients_tab_view = ClientsTab(self.tab_clients, self.controller)
        self.clients_tab_view.pack(fill="both", expand=True)

        self.history_tab_view = HistoryTab(self.tab_history, self.controller)
        self.history_tab_view.pack(fill="both", expand=True)
        self.history_tab_view.start_auto_refresh()

        self.logs_tab_view = LogsTab(self.tab_logs, self.controller)
        self.logs_tab_view.pack(fill="both", expand=True)

        self._settings_window = None

    def open_settings_window(self):
        """
        Ayarlar penceresini ekranın ortasında açar. Pencere zaten açıksa öne getirir.
        """
        if self._settings_window is not None and self._settings_window.winfo_exists():
            self._settings_window.focus()
            return

        win = ctk.CTkToplevel(self)
        win.title("Ayarlar")
        win.resizable(False, False)
        win.grab_set()
        self._settings_window = win

        # İkonu ana pencereyle aynı yap
        try:
            import sys as _sys
            _base = getattr(_sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            icon_path = os.path.join(_base, "assets", "logo.ico")
            if os.path.exists(icon_path):
                win.after(200, lambda: win.iconbitmap(icon_path))
        except Exception:
            pass

        # Pencereyi ekranın ortasına konumlandır
        win_w, win_h = 540, 640
        win.update_idletasks()
        screen_w = win.winfo_screenwidth()
        screen_h = win.winfo_screenheight()
        x = (screen_w - win_w) // 2
        y = (screen_h - win_h) // 2
        win.geometry(f"{win_w}x{win_h}+{x}+{y}")

        win.grid_columnconfigure(0, weight=1)
        win.grid_rowconfigure(0, weight=1)

        self._build_settings_content(win)

    def _build_settings_content(self, parent):
        """
        Ayarlar penceresinin içeriğini kaydırılabilir bir çerçeve içinde oluşturur.
        """
        # Kaydırılabilir ana alan
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        scroll.grid_columnconfigure(0, weight=0)
        scroll.grid_columnconfigure(1, weight=1)

        row = 0

        # ── Genel Ayarlar başlığı ──────────────────────────────────────
        section1 = ctk.CTkLabel(scroll, text="⚙  Genel Ayarlar",
                                font=ctk.CTkFont(size=14, weight="bold"),
                                text_color=("#6366f1", "#818cf8"))
        section1.grid(row=row, column=0, columnspan=2, padx=15, pady=(18, 6), sticky="w")
        row += 1

        # İndirme klasörü
        dl_label = ctk.CTkLabel(scroll, text="Gelen Dosyaların Kayıt Yolu:", font=ctk.CTkFont(weight="bold"))
        dl_label.grid(row=row, column=0, columnspan=2, padx=15, pady=(8, 3), sticky="w")
        row += 1

        dl_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        dl_frame.grid(row=row, column=0, columnspan=2, padx=15, pady=(0, 8), sticky="ew")
        dl_frame.grid_columnconfigure(0, weight=1)
        row += 1

        self.dl_path_entry = ctk.CTkEntry(dl_frame, placeholder_text="İndirme klasörü...")
        self.dl_path_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.dl_path_entry.insert(0, self.controller.file_manager.download_dir)
        self.dl_path_entry.configure(state="readonly")

        dl_browse_btn = ctk.CTkButton(dl_frame, text="Gözat...", width=80,
                                      command=self.controller.browse_download_folder)
        dl_browse_btn.grid(row=0, column=1)

        # Port
        port_label = ctk.CTkLabel(scroll, text="Sunucu Portu:", font=ctk.CTkFont(weight="bold"))
        port_label.grid(row=row, column=0, padx=15, pady=(8, 3), sticky="w")
        row += 1

        self.port_entry = ctk.CTkEntry(scroll, width=120)
        self.port_entry.grid(row=row, column=0, padx=15, pady=(0, 8), sticky="w")
        self.port_entry.insert(0, str(self.controller.port))
        if self.controller.server_running:
            self.port_entry.configure(state="disabled")
        # Odak çekilince otomatik kaydet
        self.port_entry.bind("<FocusOut>", lambda e: self._on_port_focusout())
        self.port_entry.bind("<Return>", lambda e: self._on_port_focusout())
        row += 1

        # Tema
        theme_label = ctk.CTkLabel(scroll, text="Tema (Görünüm):", font=ctk.CTkFont(weight="bold"))
        theme_label.grid(row=row, column=0, padx=15, pady=(8, 3), sticky="w")
        row += 1

        self.theme_combo = ctk.CTkComboBox(
            scroll,
            values=["Sistem", "Karanlık", "Aydınlık"],
            width=160,
            command=self.controller.change_theme
        )
        self.theme_combo.grid(row=row, column=0, padx=15, pady=(0, 8), sticky="w")
        self.theme_combo.set(self.controller.settings.get("theme", "Sistem"))
        row += 1

        # Otomatik başlat
        self.auto_start_switch = ctk.CTkSwitch(
            scroll,
            text="Uygulama açılınca sunucuyu otomatik başlat",
            variable=self.controller.auto_start_var,
            font=ctk.CTkFont(size=12)
        )
        self.auto_start_switch.grid(row=row, column=0, columnspan=2, padx=15, pady=(4, 8), sticky="w")
        row += 1

        # Varsayılan Paylaşım Limitleri
        share_limits_label = ctk.CTkLabel(scroll, text="Varsayılan Paylaşım Limitleri:", font=ctk.CTkFont(weight="bold"))
        share_limits_label.grid(row=row, column=0, columnspan=2, padx=15, pady=(8, 3), sticky="w")
        row += 1

        limits_frame = ctk.CTkFrame(scroll, fg_color=("#f1f5f9", "#1e293b"), corner_radius=8)
        limits_frame.grid(row=row, column=0, columnspan=2, padx=15, pady=(0, 12), sticky="ew")
        row += 1

        dl_lim_row = ctk.CTkFrame(limits_frame, fg_color="transparent")
        dl_lim_row.pack(fill="x", padx=12, pady=(10, 4))
        ctk.CTkLabel(dl_lim_row, text="İndirme Limiti (0=sınırsız):", font=ctk.CTkFont(size=12)).pack(side="left")
        self.default_dl_limit_entry = ctk.CTkEntry(dl_lim_row, width=70, justify="center")
        self.default_dl_limit_entry.insert(0, str(self.controller.settings.get("default_download_limit", 0)))
        self.default_dl_limit_entry.pack(side="right")
        self.default_dl_limit_entry.bind("<FocusOut>", lambda e: self._save_default_limits())
        self.default_dl_limit_entry.bind("<Return>", lambda e: self._save_default_limits())

        tm_lim_row = ctk.CTkFrame(limits_frame, fg_color="transparent")
        tm_lim_row.pack(fill="x", padx=12, pady=(4, 10))
        ctk.CTkLabel(tm_lim_row, text="Süre Limiti dk (0=sınırsız):", font=ctk.CTkFont(size=12)).pack(side="left")
        self.default_tm_limit_entry = ctk.CTkEntry(tm_lim_row, width=70, justify="center")
        self.default_tm_limit_entry.insert(0, str(self.controller.settings.get("default_time_limit", 0)))
        self.default_tm_limit_entry.pack(side="right")
        self.default_tm_limit_entry.bind("<FocusOut>", lambda e: self._save_default_limits())
        self.default_tm_limit_entry.bind("<Return>", lambda e: self._save_default_limits())

        # ── Güvenlik Ayarları başlığı ──────────────────────────────────
        sep1 = ctk.CTkFrame(scroll, height=2, fg_color=("#e2e8f0", "#2d3748"))
        sep1.grid(row=row, column=0, columnspan=2, sticky="ew", padx=15, pady=(4, 0))
        row += 1

        section2 = ctk.CTkLabel(scroll, text="🔒  Güvenlik Ayarları",
                                 font=ctk.CTkFont(size=14, weight="bold"),
                                 text_color=("#6366f1", "#818cf8"))
        section2.grid(row=row, column=0, columnspan=2, padx=15, pady=(12, 6), sticky="w")
        row += 1

        self.security_switch = ctk.CTkSwitch(
            scroll,
            text="PIN Korumalı Erişimi Aktif Et",
            variable=self.controller.security_enabled_var,
            command=self.controller.on_security_toggle
        )
        self.security_switch.grid(row=row, column=0, columnspan=2, padx=15, pady=(4, 4), sticky="w")
        row += 1

        self.otp_switch = ctk.CTkSwitch(
            scroll,
            text="Tek Kullanımlık PIN (OTP)",
            variable=self.controller.otp_enabled_var,
            command=self.controller.on_otp_toggle,
            font=ctk.CTkFont(size=12)
        )
        self.otp_switch.grid(row=row, column=0, columnspan=2, padx=15, pady=(4, 8), sticky="w")
        row += 1

        # PIN düzenleme
        self.pin_edit_frame = ctk.CTkFrame(scroll, fg_color=("#f1f5f9", "#1e293b"), corner_radius=8)
        self.pin_edit_frame.grid(row=row, column=0, columnspan=2, padx=15, pady=(0, 12), sticky="ew")
        self.pin_edit_frame.grid_columnconfigure(1, weight=1)
        row += 1

        self.pin_entry_label = ctk.CTkLabel(self.pin_edit_frame, text="PIN (4-6 hane):",
                                            font=ctk.CTkFont(size=12))
        self.pin_entry_label.grid(row=0, column=0, padx=(12, 8), pady=10, sticky="w")

        self.pin_entry = ctk.CTkEntry(self.pin_edit_frame, width=90,
                                      font=ctk.CTkFont(family="Consolas", size=13))
        self.pin_entry.grid(row=0, column=1, padx=(0, 8), pady=10, sticky="w")
        self.pin_entry.insert(0, self.controller.pin_code)

        self.pin_update_btn = ctk.CTkButton(self.pin_edit_frame, text="Güncelle", width=90,
                                            command=self.controller.update_custom_pin)
        self.pin_update_btn.grid(row=0, column=2, padx=(0, 8), pady=10)

        self.pin_gen_btn = ctk.CTkButton(self.pin_edit_frame, text="Rastgele", width=90,
                                         fg_color="#8b5cf6", hover_color="#7c3aed",
                                         command=self.controller.generate_new_pin)
        self.pin_gen_btn.grid(row=0, column=3, padx=(0, 12), pady=10)

    def _on_port_focusout(self):
        """Port alanından odak çekilince portu doğrular ve kaydeder."""
        import settings_manager
        from tkinter import messagebox
        try:
            new_port = int(self.port_entry.get().strip())
            if new_port < 1024 or new_port > 65535:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Hata", "Lütfen 1024 ile 65535 arasında geçerli bir port girin.",
                                 parent=self._settings_window)
            self.port_entry.delete(0, "end")
            self.port_entry.insert(0, str(self.controller.port))
            return

        if new_port != self.controller.port:
            self.controller.port = new_port
            self.controller.update_qr_code()
            self.controller.settings["port"] = new_port
            settings_manager.save(self.controller.settings)
            self.controller.add_log(f"AYAR: Port {new_port} olarak güncellendi.")

    def _save_default_limits(self):
        """Varsayılan paylaşım limitlerini kaydeder."""
        import settings_manager
        try:
            dl = int(self.default_dl_limit_entry.get().strip())
            tm = int(self.default_tm_limit_entry.get().strip())
            if dl < 0 or tm < 0:
                raise ValueError()
        except ValueError:
            return
        self.controller.settings["default_download_limit"] = dl
        self.controller.settings["default_time_limit"] = tm
        settings_manager.save(self.controller.settings)

    @property
    def shared_scrollable(self):
        return self.shared_tab_view.shared_scrollable

    @property
    def zip_progress_frame(self):
        return self.shared_tab_view.zip_progress_frame

    @property
    def zip_label(self):
        return self.shared_tab_view.zip_label

    @property
    def zip_progress(self):
        return self.shared_tab_view.zip_progress

    @property
    def zip_file_label(self):
        return self.shared_tab_view.zip_file_label

    @property
    def clients_scrollable(self):
        return self.clients_tab_view.clients_scrollable
        
    @property
    def servers_scrollable(self):
        return self.clients_tab_view.servers_scrollable

    @property
    def add_folder_btn(self):
        return self.shared_tab_view.add_folder_btn

    @property
    def add_file_btn(self):
        return self.shared_tab_view.add_file_btn

    @property
    def clear_selected_btn(self):
        return self.shared_tab_view.clear_selected_btn

    @property
    def received_scrollable(self):
        return self.received_tab_view.received_scrollable

    @property
    def logs_textbox(self):
        return self.logs_tab_view.logs_textbox

    @property
    def clipboard_textbox(self):
        return self.clipboard_tab_view.clipboard_textbox

    @property
    def clip_history_scrollable(self):
        return self.clipboard_tab_view.clip_history_scrollable

    @property
    def clients_scrollable(self):
        return self.clients_tab_view.clients_scrollable

    @property
    def servers_scrollable(self):
        return self.clients_tab_view.servers_scrollable
