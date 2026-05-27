import tkinter as tk
import customtkinter as ctk
import db.database as db

class HistoryTab(ctk.CTkFrame):
    """
    İndirme ve yükleme geçmişini (transfer history) gösteren sekme.
    """
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self._last_history_count = -1
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Üst Araç Çubuğu
        self.toolbar = ctk.CTkFrame(self, fg_color="transparent")
        self.toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        self.title_lbl = ctk.CTkLabel(
            self.toolbar, 
            text="Transfer Geçmişi", 
            font=ctk.CTkFont(size=15, weight="bold")
        )
        self.title_lbl.pack(side="left", padx=5)
        
        self.refresh_btn = ctk.CTkButton(
            self.toolbar,
            text="🔄 Yenile",
            width=80,
            command=self.refresh_history
        )
        self.refresh_btn.pack(side="right", padx=5)
        
        self.clear_btn = ctk.CTkButton(
            self.toolbar,
            text="🗑 Temizle",
            width=80,
            fg_color="#ef4444",
            hover_color="#dc2626",
            command=self.clear_history
        )
        self.clear_btn.pack(side="right", padx=5)

        # Tablo formatı için scrollable frame
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.grid(row=1, column=0, sticky="nsew")
        self.scroll_frame.grid_columnconfigure(0, weight=1)
        self.scroll_frame.grid_columnconfigure(1, weight=3)
        self.scroll_frame.grid_columnconfigure(2, weight=1)
        self.scroll_frame.grid_columnconfigure(3, weight=1)
        
        # Tablo Başlıkları
        self._add_headers()
        self.refresh_history()

    def _add_headers(self):
        headers = ["Tarih", "Dosya Adı", "IP Adresi", "İşlem"]
        for i, h in enumerate(headers):
            lbl = ctk.CTkLabel(self.scroll_frame, text=h, font=ctk.CTkFont(weight="bold"))
            lbl.grid(row=0, column=i, sticky="w", padx=10, pady=5)

    def refresh_history(self):
        history = db.get_history()
        
        # Eğer veri sayısı değişmediyse tabloyu baştan çizme (flicker/titreme sorununu çözer)
        if len(history) == self._last_history_count:
            return
            
        self._last_history_count = len(history)

        # Önceki verileri temizle (başlık hariç)
        for widget in self.scroll_frame.winfo_children():
            if widget.grid_info()['row'] > 0:
                widget.destroy()
                
        if not history:
            lbl = ctk.CTkLabel(self.scroll_frame, text="Henüz bir transfer geçmişi yok.", text_color="gray")
            lbl.grid(row=1, column=0, columnspan=4, pady=20)
            return
            
        for row_idx, item in enumerate(history, start=1):
            # Veritabanında zaman timestamp olarak gelir
            time_lbl = ctk.CTkLabel(self.scroll_frame, text=item["time"])
            time_lbl.grid(row=row_idx, column=0, sticky="w", padx=10, pady=2)
            
            name_lbl = ctk.CTkLabel(self.scroll_frame, text=item["filename"], wraplength=200)
            name_lbl.grid(row=row_idx, column=1, sticky="w", padx=10, pady=2)
            
            ip_lbl = ctk.CTkLabel(self.scroll_frame, text=item["ip"])
            ip_lbl.grid(row=row_idx, column=2, sticky="w", padx=10, pady=2)
            
            action_color = "#10b981" if item["action"] == "İndirme" else "#3b82f6"
            action_lbl = ctk.CTkLabel(self.scroll_frame, text=item["action"], text_color=action_color)
            action_lbl.grid(row=row_idx, column=3, sticky="w", padx=10, pady=2)

    def clear_history(self):
        conn = db._get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM TransferHistory')
        conn.commit()
        conn.close()
        
        self._last_history_count = -1
        self.refresh_history()

    def start_auto_refresh(self):
        self.refresh_history()
        self.after(2000, self.start_auto_refresh)
