import os
import sys
import ctypes
import customtkinter as ctk
from tkinterdnd2 import TkinterDnD

def resource_path(relative_path):
    """
    PyInstaller ile paketlenmiş EXE içinde veya normal çalışmada
    kaynak dosyaların mutlak yolunu döner.
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

os.environ.setdefault("PYTRANSFER_TEMPLATE_FOLDER", resource_path("templates"))
os.environ.setdefault("PYTRANSFER_STATIC_FOLDER", resource_path("static"))

import utils
import server
from gui import PyTransferGUI

try:
    myappid = 'pytransfer.filesharing.v1'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

class CTkDnD(ctk.CTk, TkinterDnD.DnDWrapper):
    """
    CustomTkinter CTk penceresini sürükle-bırak desteği ile genişleten sınıftır.
    """
    def __init__(self, *args, **kwargs):
        """
        Pencereyi kurar ve TkDnd Tcl uzantısını yükler.
        """
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

def main():
    """
    Uygulamanın ana giriş noktasıdır. Dosya yöneticisini başlatır,
    CustomTkinter arayüz penceresini oluşturur ve Flask sunucusu ile arayüz
    arasındaki geri bildirim mekanizmalarını kurarak döngüyü başlatır.
    """
    file_manager = utils.FileManager()
    root = CTkDnD()
    
    def start_server_callback(host, port):
        """
        Masaüstü arayüzünden gelen tetikleme ile Flask sunucusunu başlatır.
        """
        server.start_server(
            host=host, 
            port=port, 
            fm=file_manager, 
            log_cb=gui_app.add_log, 
            rec_cb=gui_app.on_file_received_trigger
        )
        
    def stop_server_callback():
        """
        Masaüstü arayüzünden gelen tetikleme ile Flask sunucusunu durdurur.
        """
        server.stop_server()
        
    gui_app = PyTransferGUI(
        root=root,
        file_manager=file_manager,
        start_server_callback=start_server_callback,
        stop_server_callback=stop_server_callback
    )
    
    import pystray
    from pystray import MenuItem as item
    import threading
    from PIL import Image
    import os

    icon_path = resource_path(os.path.join("assets", "logo.ico"))
    if os.path.exists(icon_path):
        icon_image = Image.open(icon_path)
    else:
        icon_image = Image.new('RGB', (64, 64), color=(73, 109, 137))
        
    def real_quit():
        server.stop_server()
        gui_app.cleanup()
        root.destroy()
        sys.exit(0)

    def quit_window(icon, item):
        icon.stop()
        root.after(0, real_quit)

    def show_window(icon, item):
        icon.stop()
        root.after(0, root.deiconify)

    def on_closing():
        """
        Pencere kapatıldığında arka plandaki Flask sunucusunu durdurmaz,
        sadece pencereyi gizler ve sistem tepsisine atar.
        """
        root.withdraw()
        menu = (item('Göster', show_window), item('Çıkış', quit_window))
        tray_icon = pystray.Icon("PyTransfer", icon_image, "PyTransfer Arka Planda Çalışıyor", menu)
        # Sistem tepsisi iş parçacığını başlat
        threading.Thread(target=tray_icon.run, daemon=True).start()
        
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    def check_signals():
        """
        Windows üzerinde terminalden gelen Ctrl+C sinyallerini yakalamak ve
        arayüz ana döngüsünü kesintiye uğratabilmek için periyodik kontrol yapar.
        """
        root.after(200, check_signals)
        
    root.after(200, check_signals)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        server.stop_server()
        gui_app.cleanup()
        root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    main()
