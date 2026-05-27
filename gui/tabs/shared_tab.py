import customtkinter as ctk

class SharedTab(ctk.CTkFrame):
    """
    Paylaşılan dosyaların listelendiği, dosya/klasör ekleme ve
    paylaşım kaldırma işlemlerinin yapıldığı sekme bileşenlerini barındırır.
    """
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        
        self.shared_scrollable = ctk.CTkScrollableFrame(self, label_text="Paylaşılan Dosyalar Listesi")
        self.shared_scrollable.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        self.zip_progress_frame = ctk.CTkFrame(self, height=45, fg_color="transparent")
        self.zip_progress_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(2, 8))
        self.zip_progress_frame.grid_columnconfigure(0, weight=1)
        self.zip_progress_frame.grid_remove()
        
        self.zip_label = ctk.CTkLabel(self.zip_progress_frame, text="Klasör sıkıştırılıyor: %0", font=ctk.CTkFont(size=12, weight="bold"))
        self.zip_label.grid(row=0, column=0, sticky="w", pady=(0, 2))
        
        self.zip_file_label = ctk.CTkLabel(self.zip_progress_frame, text="", font=ctk.CTkFont(size=10), text_color="gray")
        self.zip_file_label.grid(row=1, column=0, sticky="w", pady=(0, 2))
        
        self.zip_progress = ctk.CTkProgressBar(self.zip_progress_frame)
        self.zip_progress.grid(row=2, column=0, sticky="ew", pady=2)
        self.zip_progress.set(0.0)
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 10))
        
        self.add_file_btn = ctk.CTkButton(
            btn_frame, 
            text=" Dosya Paylaş", 
            fg_color="#6366f1", 
            hover_color="#4f46e5",
            command=self.controller.share_file_dialog
        )
        self.add_file_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.add_folder_btn = ctk.CTkButton(
            btn_frame, 
            text=" Klasör Paylaş (ZIP)", 
            fg_color="#8b5cf6", 
            hover_color="#7c3aed",
            command=self.controller.share_folder_dialog
        )
        self.add_folder_btn.grid(row=0, column=1, padx=(0, 10))
        
        self.clear_selected_btn = ctk.CTkButton(
            btn_frame, 
            text=" Seçilenleri Kaldır", 
            width=140,
            command=self.controller.remove_selected_share,
            fg_color=("#ef4444", "#dc2626"),
            hover_color=("#dc2626", "#b91c1c")
        )
        self.clear_selected_btn.grid(row=0, column=2, padx=(0, 10))
