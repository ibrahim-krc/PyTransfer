import os
import werkzeug
from flask import jsonify, request, send_file, render_template, session
from server import core
from server.security import trigger_otp_regeneration
import db.database as db

def send_desktop_notification(title, message):
    try:
        from plyer import notification
        import threading
        import sys
        import os
        def show_notif():
            _base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            icon_path = os.path.join(_base, "assets", "logo.ico")
            if not os.path.exists(icon_path):
                icon_path = None
                
            notification.notify(
                title=title,
                message=message,
                app_name="PyTransfer",
                app_icon=icon_path,
                timeout=5
            )
        threading.Thread(target=show_notif).start()
    except Exception:
        pass

def is_authenticated():
    """
    Checks if the client session is authenticated.
    
    Returns:
        bool: True if authenticated or security is disabled, False otherwise.
    """
    if not core.security_enabled:
        return True
    return session.get('authenticated') == True

def update_clipboard_text(new_text, source_ip=None):
    """
    Updates the shared clipboard text and adds it to the history.
    
    Args:
        new_text (str): The new text to set in the clipboard.
        source_ip (str, optional): The IP address of the client sending the text.
    """
    if new_text != core.clipboard_text:
        core.clipboard_text = new_text
        if new_text:
            if new_text in core.clipboard_history:
                core.clipboard_history.remove(new_text)
            core.clipboard_history.insert(0, new_text)
            if len(core.clipboard_history) > 10:
                core.clipboard_history = core.clipboard_history[:10]
        if core.log_callback:
            source = source_ip if source_ip else "Arayüz"
            logged_text = core.clipboard_text[:30] + "..." if len(core.clipboard_text) > 30 else core.clipboard_text
            core.log_callback(f"PANO GÜNCELLENDİ: '{logged_text}' <- {source}")

_notified_ips = set()

def register_routes(app):
    """
    Registers all web routes and API endpoints for the Flask application.
    
    Args:
        app (Flask): The Flask application instance.
    """
    @app.route('/')
    def index():
        """
        Renders the main index page. Handles automatic login if a valid PIN is provided in the URL.
        """
        client_ip = request.remote_addr
        
        if client_ip not in _notified_ips:
            send_desktop_notification("Yeni Bağlantı", f"{client_ip} cihazı PyTransfer'a bağlandı.")
            _notified_ips.add(client_ip)
            
        url_pin = request.args.get('pin')
        if url_pin and core.security_enabled and url_pin == str(core.pin_code):
            session['authenticated'] = True
            if core.log_callback:
                core.log_callback(f"BAĞLANTI: {client_ip} QR kod ile otomatik giriş yaptı")
            if core.otp_enabled:
                trigger_otp_regeneration()
        else:
            if core.log_callback:
                core.log_callback(f"BAĞLANTI: {client_ip} bağlandı")
        return render_template('index.html')

    @app.route('/api/verify-pin', methods=['POST'])
    def verify_pin():
        """
        Verifies the PIN code submitted by a client and grants access if correct.
        """
        if not core.security_enabled:
            session['authenticated'] = True
            return jsonify({"status": "success"})
            
        data = request.get_json()
        entered_pin = data.get('pin', '')
        
        if str(entered_pin) == str(core.pin_code):
            session['authenticated'] = True
            if core.log_callback:
                core.log_callback(f"BAĞLANTI: {request.remote_addr} PIN doğrulayarak giriş yaptı")
            if core.otp_enabled:
                trigger_otp_regeneration()
            return jsonify({"status": "success"})
        else:
            if core.log_callback:
                core.log_callback(f"BAĞLANTI HATA: {request.remote_addr} geçersiz PIN denedi: {entered_pin}")
            return jsonify({"status": "error", "message": "Geçersiz PIN kodu!"}), 401

    @app.route('/api/files', methods=['GET'])
    def get_files():
        """
        Retrieves the list of all shared files.
        """
        if not is_authenticated():
            return jsonify({"status": "error", "message": "Yetkisiz erişim"}), 401
        if core.file_manager:
            import time
            now = time.time()
            valid_files = []
            for f in list(core.file_manager.shared_files.values()):
                if f.expires_at and now > f.expires_at:
                    core.file_manager.remove_shared_file(f.id)
                    continue
                if f.max_downloads > 0 and f.current_downloads >= f.max_downloads:
                    core.file_manager.remove_shared_file(f.id)
                    continue
                valid_files.append(f.to_dict())
            return jsonify(valid_files)
        return jsonify([])

    @app.route('/api/download/<file_id>', methods=['GET'])
    def download_file(file_id):
        """
        Serves the requested shared file for download or preview.
        """
        if not is_authenticated():
            return "Yetkisiz erişim", 401
        if not core.file_manager:
            return jsonify({"status": "error", "message": "File manager not initialized"}), 500
        
        file_obj = core.file_manager.get_shared_file(file_id)
        if not file_obj:
            return jsonify({"status": "error", "message": "File not found"}), 404

        import time
        if file_obj.expires_at and time.time() > file_obj.expires_at:
            core.file_manager.remove_shared_file(file_id)
            return jsonify({"status": "error", "message": "Bu dosyanın paylaşım süresi dolmuştur."}), 403
            
        if file_obj.max_downloads > 0 and file_obj.current_downloads >= file_obj.max_downloads:
            core.file_manager.remove_shared_file(file_id)
            return jsonify({"status": "error", "message": "Bu dosyanın indirme limitine ulaşılmıştır."}), 403

        client_ip = request.remote_addr
        
        # Check if this is a fresh full request (not a partial range request resume)
        range_header = request.headers.get("Range")
        if not range_header or range_header.startswith("bytes=0-"):
            file_obj.current_downloads += 1
            if core.log_callback:
                core.log_callback(f"İNDİRME: {file_obj.name} -> {client_ip} (Limit: {file_obj.current_downloads}/{file_obj.max_downloads if file_obj.max_downloads>0 else 'Yok'})")
            # SQLite'a geçmişi kaydet
            db.add_history(file_obj.name, "İndirme", client_ip)
            
            # Eğer son indirme yapıldıysa, dosyayı paylaşımdan kaldır (indirme bitince silmek zor olduğu için hemen kaldırıyoruz, ama transfer stream devam eder)
            if file_obj.max_downloads > 0 and file_obj.current_downloads >= file_obj.max_downloads:
                if core.log_callback:
                    core.log_callback(f"BİLGİ: {file_obj.name} indirme limitine ulaştığı için paylaşımdan kaldırıldı.")
                core.file_manager.remove_shared_file(file_id)

        preview = request.args.get('preview') == 'true'
        return send_file(file_obj.path, as_attachment=not preview, download_name=file_obj.name, conditional=True)

    @app.route('/api/download_all', methods=['GET'])
    def download_all():
        """
        Serves all shared files as a single uncompressed ZIP archive.
        """
        if not is_authenticated():
            return "Yetkisiz erişim", 401
        if not core.file_manager:
            return jsonify({"status": "error", "message": "File manager not initialized"}), 500

        shared_files = list(core.file_manager.shared_files.values())
        if not shared_files:
            return jsonify({"status": "error", "message": "No files to download"}), 404

        import zipfile
        import os
        from datetime import datetime
        
        # Temp klasörünü ayarla
        temp_dir = os.path.join(core.file_manager.download_dir, ".temp_shares")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Benzersiz bir ZIP dosya adı oluştur
        zip_filename = f"PyTransfer_TumDosyalar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        zip_path = os.path.join(temp_dir, zip_filename)

        try:
            # İşlemci ve RAM'i yormamak için sıkıştırma yapmıyoruz (ZIP_STORED)
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_STORED) as zf:
                for f_obj in shared_files:
                    if os.path.isfile(f_obj.path):
                        zf.write(f_obj.path, f_obj.name)
                    elif os.path.isdir(f_obj.path):
                        for root, _, files in os.walk(f_obj.path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                # Klasör yapısını korumak için arcname oluştur
                                arcname = os.path.join(f_obj.name, os.path.relpath(file_path, f_obj.path))
                                zf.write(file_path, arcname)
                                
            client_ip = request.remote_addr
            if core.log_callback:
                core.log_callback(f"İNDİRME (TOPLU): Tüm dosyalar (ZIP) -> {client_ip}")
            db.add_history("Tüm Dosyalar (ZIP)", "İndirme", client_ip)
            
            return send_file(zip_path, as_attachment=True, download_name=zip_filename)
        except Exception as e:
            if core.log_callback:
                core.log_callback(f"HATA: Toplu ZIP oluşturulamadı. {str(e)}")
            return jsonify({"status": "error", "message": "Failed to create ZIP"}), 500

    @app.route('/api/upload', methods=['POST'])
    def upload_file():
        """
        Handles file uploads from clients and saves them to the configured download directory.
        """
        if not is_authenticated():
            return jsonify({"status": "error", "message": "Yetkisiz erişim"}), 401
        if not core.file_manager:
            return jsonify({"status": "error", "message": "File manager not initialized"}), 500
        
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No file part"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"status": "error", "message": "No selected file"}), 400
            
        if file:
            original_name = file.filename
            filename = werkzeug.utils.secure_filename(original_name)
            if not filename:
                filename = f"received_{werkzeug.utils.secure_filename(original_name)}"
                if not filename or filename == "received_":
                    filename = "uploaded_file"
                    
            name, ext = os.path.splitext(filename)
            dest_path = os.path.join(core.file_manager.download_dir, filename)
            counter = 1
            while os.path.exists(dest_path):
                filename = f"{name}_{counter}{ext}"
                dest_path = os.path.join(core.file_manager.download_dir, filename)
                counter += 1
                
            file.save(dest_path)
            
            client_ip = request.remote_addr
            if core.log_callback:
                core.log_callback(f"YÜKLEME: {original_name} <- {client_ip} ({filename} olarak kaydedildi)")

            # SQLite'a geçmişi kaydet
            db.add_history(original_name, "Yükleme", client_ip)
            if core.received_callback:
                core.received_callback(dest_path)
                
            send_desktop_notification("PyTransfer - Yeni Dosya", f"{client_ip} cihazından yeni dosya alındı:\n{original_name}")
                
            return jsonify({"status": "success", "filename": filename})
            
        return jsonify({"status": "error", "message": "Upload failed"}), 500

    @app.route('/dropzone/<token>', methods=['GET'])
    def dropzone_page(token):
        """
        Dosya talep kutusu (Dropzone) arayüzünü sunar.
        """
        if token not in core.active_dropzones:
            return "Geçersiz veya süresi dolmuş bağlantı.", 404
        return render_template('dropzone.html', token=token)

    @app.route('/api/dropzone_upload/<token>', methods=['POST'])
    def dropzone_upload(token):
        """
        Dropzone arayüzü üzerinden gelen dosyaları kabul eder (PIN gerektirmez).
        """
        if token not in core.active_dropzones:
            return jsonify({"status": "error", "message": "Geçersiz token"}), 401
            
        if not core.file_manager:
            return jsonify({"status": "error", "message": "Sistem hazır değil"}), 500
            
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "Dosya bulunamadı"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"status": "error", "message": "Dosya seçilmedi"}), 400
            
        if file:
            original_name = file.filename
            filename = werkzeug.utils.secure_filename(original_name)
            if not filename:
                filename = f"dropzone_{werkzeug.utils.secure_filename(original_name)}"
                if not filename or filename == "dropzone_":
                    filename = "uploaded_file"
                    
            name, ext = os.path.splitext(filename)
            dest_path = os.path.join(core.file_manager.download_dir, filename)
            counter = 1
            while os.path.exists(dest_path):
                filename = f"{name}_{counter}{ext}"
                dest_path = os.path.join(core.file_manager.download_dir, filename)
                counter += 1
                
            file.save(dest_path)
            
            client_ip = request.remote_addr
            if core.log_callback:
                core.log_callback(f"DROPZONE: {original_name} <- {client_ip}")

            db.add_history(original_name, "Talep (Dropzone)", client_ip)
            if core.received_callback:
                core.received_callback(dest_path)
                
            send_desktop_notification("PyTransfer Dropzone", f"{client_ip} size dosya yolladı:\n{original_name}")
                
            return jsonify({"status": "success", "filename": filename})
            
        return jsonify({"status": "error", "message": "Upload failed"}), 500

    @app.route('/api/sync/list', methods=['GET'])
    def sync_list():
        """
        Ortak klasördeki dosyaların listesini ve son değiştirilme zamanlarını döndürür.
        """
        # Güvenlik kontrolü - opsiyonel ama iyi olabilir, aynı ağdan geldiğini varsayıyoruz.
        if not core.sync_manager or not core.sync_manager.running:
            return jsonify({"status": "error", "message": "Sync is disabled"}), 400
            
        sync_folder = core.sync_manager.sync_folder
        if not os.path.exists(sync_folder):
            return jsonify({"files": []})
            
        files = []
        try:
            for f in os.listdir(sync_folder):
                path = os.path.join(sync_folder, f)
                if os.path.isfile(path):
                    files.append({
                        "name": f,
                        "mtime": os.path.getmtime(path),
                        "size": os.path.getsize(path)
                    })
        except Exception:
            pass
            
        return jsonify({"status": "success", "files": files})

    @app.route('/api/sync/download/<path:filename>', methods=['GET'])
    def sync_download(filename):
        """
        Ortak klasördeki spesifik bir dosyayı indirir.
        """
        if not core.sync_manager or not core.sync_manager.running:
            return "Sync is disabled", 400
            
        sync_folder = core.sync_manager.sync_folder
        safe_path = os.path.normpath(os.path.join(sync_folder, filename))
        
        if not safe_path.startswith(sync_folder) or not os.path.exists(safe_path) or not os.path.isfile(safe_path):
            return "File not found", 404
            
        return send_file(safe_path, as_attachment=True)

    @app.route('/api/clipboard', methods=['GET', 'POST'])
    def manage_clipboard():
        """
        Manages getting and setting the shared clipboard text.
        """
        if not is_authenticated():
            return jsonify({"status": "error", "message": "Yetkisiz erişim"}), 401
        if request.method == 'POST':
            data = request.get_json()
            new_text = data.get('text', '')
            update_clipboard_text(new_text, request.remote_addr)
            return jsonify({"status": "success"})
        else:
            return jsonify({"text": core.clipboard_text})

    @app.route('/api/clipboard/history', methods=['GET'])
    def get_clipboard_history():
        """
        Retrieves the history of clipboard entries.
        """
        if not is_authenticated():
            return jsonify({"status": "error", "message": "Yetkisiz erişim"}), 401
        return jsonify({"history": core.clipboard_history})

    @app.route('/api/discovery', methods=['GET'])
    def get_discovered_servers():
        """
        Returns a list of discovered PyTransfer servers on the local network.
        """
        if not is_authenticated():
            return jsonify({"status": "error", "message": "Yetkisiz erişim"}), 401
        
        servers = []
        for name, info in core.discovered_servers.items():
            servers.append({
                "name": info["name"],
                "ip": info["ip"],
                "port": info["port"]
            })
        return jsonify({"servers": servers})
