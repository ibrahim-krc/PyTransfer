import customtkinter as ctk

class ClipboardTab(ctk.CTkFrame):
    """
    Cihazlar arasında anlık metin ve web bağlantılarının paylaşıldığı
    ortak pano sekme bileşenlerini barındırır.
    """
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        self.grid_columnconfigure(0, weight=1, uniform="clip")
        self.grid_columnconfigure(1, weight=1, uniform="clip")
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)
        
        clip_label = ctk.CTkLabel(
            self, 
            text="Ortak Pano İçeriği:", 
            font=ctk.CTkFont(size=13, weight="bold")
        )
        clip_label.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))
        
        self.clipboard_textbox = ctk.CTkTextbox(self)
        self.clipboard_textbox.grid(row=1, column=0, sticky="nsew", padx=15, pady=5)

        self._placeholder = "Panodan gelen veya gönderilecek metin..."
        self._placeholder_active = True
        self.clipboard_textbox.insert("1.0", self._placeholder)
        self.clipboard_textbox.configure(text_color=("#94a3b8", "#64748b"))

        def _on_focus_in(e):
            if self._placeholder_active:
                self.clipboard_textbox.delete("1.0", "end")
                self.clipboard_textbox.configure(text_color=("#0f172a", "#f1f5f9"))
                self._placeholder_active = False

        def _on_focus_out(e):
            if not self.clipboard_textbox.get("1.0", "end-1c").strip():
                self.clipboard_textbox.insert("1.0", self._placeholder)
                self.clipboard_textbox.configure(text_color=("#94a3b8", "#64748b"))
                self._placeholder_active = True

        self.clipboard_textbox.bind("<FocusIn>", _on_focus_in)
        self.clipboard_textbox.bind("<FocusOut>", _on_focus_out)
        
        self.auto_copy_switch = ctk.CTkSwitch(
            self, 
            text="Gelen metinleri bilgisayar panosuna (Clipboard) otomatik kopyala", 
            variable=self.controller.auto_copy_var,
            font=ctk.CTkFont(size=12)
        )
        self.auto_copy_switch.grid(row=2, column=0, sticky="w", padx=15, pady=10)
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=3, column=0, sticky="ew", padx=15, pady=(5, 15))
        
        send_clip_btn = ctk.CTkButton(
            btn_frame, 
            text="Gönder / Panoyu Güncelle", 
            command=self.controller.send_to_server_clipboard
        )
        send_clip_btn.grid(row=0, column=0)

        history_label = ctk.CTkLabel(
            self,
            text="Pano Geçmişi (Son 10 Metin):",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        history_label.grid(row=0, column=1, sticky="w", padx=15, pady=(15, 5))

        self.clip_history_scrollable = ctk.CTkScrollableFrame(self, label_text="Pano Geçmişi")
        self.clip_history_scrollable.grid(row=1, column=1, rowspan=3, sticky="nsew", padx=15, pady=5)
