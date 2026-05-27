import customtkinter as ctk

class ClientsTab(ctk.CTkFrame):
    """
    Sunucuya bağlı aktif cihazları listelemek ve onları
    engellemek/engellerini kaldırmak için arayüz bileşenlerini barındırır.
    """
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1, uniform="list")
        self.grid_rowconfigure(1, weight=1, uniform="list")
        
        self.clients_scrollable = ctk.CTkScrollableFrame(self, label_text="Bağlı Cihazlar Listesi")
        self.clients_scrollable.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))

        self.servers_scrollable = ctk.CTkScrollableFrame(self, label_text="Ağdaki Diğer PyTransfer Sunucuları")
        self.servers_scrollable.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))

