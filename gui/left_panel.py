import tkinter as tk
import customtkinter as ctk
import utils

class LeftPanel(ctk.CTkFrame):
    """
    Uygulamanın sol tarafındaki ağ yapılandırması, sunucu durum bilgisi,
    bağlantı QR kodu ve erişim şifresi panellerini barındıran sınıftır.
    """
    def __init__(self, parent, controller):
        """
        LeftPanel sınıfı kurucusudur. Panel yerleşimini ve bileşenlerini oluşturur.
        """
        super().__init__(parent, width=360, corner_radius=0)
        self.controller = controller
        self.grid_rowconfigure(10, weight=1)
        
        self.create_widgets()

    def create_widgets(self):
        """
        Sol panelde bulunan tüm grafiksel bileşenleri (Etiketler, IP Seçim Kutusu, QR Kod, PIN ve Aktivite göstergeleri) tanımlar.
        """
        try:
            import sys as _sys
            from PIL import Image
            import os
            _base = getattr(_sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            logo_path = os.path.join(_base, "assets", "logo.png")
            if os.path.exists(logo_path):
                pil_img = Image.open(logo_path)
                logo_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(40, 40))
            else:
                logo_img = None
                
            upload_icon_path = os.path.join(_base, "assets", "icons", "upload.png")
            if os.path.exists(upload_icon_path):
                up_img = Image.open(upload_icon_path)
                upload_img = ctk.CTkImage(light_image=up_img, dark_image=up_img, size=(18, 18))
            else:
                upload_img = None
        except Exception:
            logo_img = None
            upload_img = None

        logo_label = ctk.CTkLabel(
            self, 
            text=" PyTransfer", 
            image=logo_img,
            compound="left",
            font=ctk.CTkFont(family="Outfit", size=24, weight="bold"),
            text_color="#6366f1"
        )
        logo_label.grid(row=0, column=0, padx=20, pady=(25, 5), sticky="w")
        
        subtitle_label = ctk.CTkLabel(
            self, 
            text="Yerel ağ üzerinden hızlı veri transferi", 
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")
        
        self.status_frame = ctk.CTkFrame(self, height=45, fg_color=("#fee2e2", "#3f1a1a"))
        self.status_frame.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        self.status_frame.grid_columnconfigure(1, weight=1)
        
        self.status_indicator = ctk.CTkLabel(
            self.status_frame, 
            text="● Durduruldu", 
            text_color="#ef4444",
            font=ctk.CTkFont(weight="bold")
        )
        self.status_indicator.grid(row=0, column=0, padx=15, pady=8, sticky="w")
        
        self.ip_header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.ip_header_frame.grid(row=3, column=0, padx=20, pady=(15, 5), sticky="ew")
        
        ip_label = ctk.CTkLabel(self.ip_header_frame, text="Ağ Arayüzü (IP)", font=ctk.CTkFont(size=13, weight="bold"))
        ip_label.pack(side="left")
        
        separator_label = ctk.CTkLabel(self.ip_header_frame, text=" | ", font=ctk.CTkFont(size=13), text_color="gray")
        separator_label.pack(side="left", padx=5)
        
        self.tunnel_switch = ctk.CTkSwitch(
            self.ip_header_frame,
            text="İnternete Aç (Dış Ağ)",
            font=ctk.CTkFont(weight="bold", size=11),
            command=self.controller.on_tunnel_toggle,
            state="disabled",
            switch_width=32,
            switch_height=16
        )
        self.tunnel_switch.pack(side="left")
        
        ip_options = [item['label'] for item in self.controller.labeled_ips]
        self.ip_combobox = ctk.CTkComboBox(
            self, 
            values=ip_options, 
            width=320,
            command=self.controller.on_ip_changed
        )
        self.ip_combobox.grid(row=4, column=0, padx=20, pady=5, sticky="w")
        if ip_options:
            self.ip_combobox.set(ip_options[0])
            
        self.qr_frame = ctk.CTkFrame(self, width=180, height=180, fg_color="white", corner_radius=12)
        self.qr_frame.grid(row=5, column=0, padx=20, pady=10)
        self.qr_frame.grid_propagate(False)
        
        self.qr_image_label = ctk.CTkLabel(self.qr_frame, text="QR Kod\nYükleniyor...", text_color="black")
        self.qr_image_label.pack(expand=True, fill="both", padx=10, pady=10)
        
        self.url_container = ctk.CTkFrame(self, fg_color="transparent")
        self.url_container.grid(row=6, column=0, padx=20, pady=5, sticky="ew")
        self.url_container.grid_columnconfigure(0, weight=1)
        
        self.url_entry = ctk.CTkEntry(self.url_container, placeholder_text="http://...", state="readonly", height=32)
        self.url_entry.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        
        copy_url_btn = ctk.CTkButton(
            self.url_container, 
            text="Kopyala", 
            width=65, 
            height=32,
            command=self.controller.copy_url_to_clipboard
        )
        copy_url_btn.grid(row=0, column=1, sticky="e")
        
        self.dropzone_btn = ctk.CTkButton(
            self,
            text=" Dosya İsteği Linki Oluştur",
            image=upload_img,
            fg_color="#3b82f6",
            hover_color="#2563eb",
            height=32,
            font=ctk.CTkFont(weight="bold", size=12),
            command=self.controller.generate_dropzone_link,
            state="disabled"
        )
        self.dropzone_btn.grid(row=7, column=0, padx=20, pady=(5, 10), sticky="ew")
        
        self.activity_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.activity_frame.grid(row=8, column=0, padx=20, pady=(5, 5), sticky="ew")
        self.activity_frame.grid_columnconfigure(0, weight=1)
        
        self.activity_label = ctk.CTkLabel(
            self.activity_frame, 
            text="⚡ Son Aktivite: Sunucu başlatılmadı", 
            font=ctk.CTkFont(size=11, slant="italic"),
            text_color=("#475569", "#94a3b8"),
            anchor="w"
        )
        self.activity_label.grid(row=0, column=0, sticky="ew")
        

        

        self.server_toggle_btn = ctk.CTkButton(
            self, 
            text="Sunucuyu Başlat", 
            fg_color="#10b981", 
            hover_color="#059669",
            height=40,
            font=ctk.CTkFont(weight="bold", size=14),
            command=self.controller.toggle_server
        )
        self.server_toggle_btn.grid(row=11, column=0, padx=20, pady=(15, 25), sticky="ew")

    def update_pin_display(self, pin_code, security_enabled):
        """
        LeftPanel artık PIN değerini tek başına göstermiyor,
        bu özellik main_window tarafından status bar üzerinden yönetiliyor.
        Bunu geriye dönük uyumluluk için boş bıraktık.
        """
        pass

    def update_activity(self, message):
        """
        Bağlı cihazlardan gelen son etkinlik mesajını tek satırlık log alanında gösterir.
        """
        max_len = 40
        truncated = message if len(message) <= max_len else message[:max_len - 3] + "..."
        self.activity_label.configure(text=f"⚡ {truncated}")
