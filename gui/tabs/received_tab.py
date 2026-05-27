import customtkinter as ctk

class ReceivedTab(ctk.CTkFrame):
    """
    Diğer cihazlardan bilgisayara yüklenen gelen dosyaların
    listelendiği sekme bileşenlerini barındırır.
    """
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        
        self.received_scrollable = ctk.CTkScrollableFrame(self, label_text="Gelen Dosyalar (Cihazlardan Yüklenenler)")
        self.received_scrollable.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 10))
        
        open_folder_btn = ctk.CTkButton(
            btn_frame, 
            text="Klasörü Aç", 
            command=self.controller.open_downloads_folder
        )
        open_folder_btn.grid(row=0, column=0, padx=(0, 10))
