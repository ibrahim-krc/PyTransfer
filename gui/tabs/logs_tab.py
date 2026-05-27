import customtkinter as ctk

class LogsTab(ctk.CTkFrame):
    """
    Sunucudaki dosya indirme, yükleme ve bağlantı hareketlerinin
    günlüğünün görüntülendiği sekme bileşenlerini barındırır.
    """
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        
        self.logs_textbox = ctk.CTkTextbox(self, state="disabled")
        self.logs_textbox.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        clear_logs_btn = ctk.CTkButton(
            self, 
            text="Günlüğü Temizle", 
            fg_color="#6b7280", 
            hover_color="#4b5563",
            command=self.controller.clear_logs
        )
        clear_logs_btn.grid(row=1, column=0, sticky="w", padx=10, pady=(5, 10))
