# 🚀 PyTransfer

PyTransfer, yerel ağınız (Wi-Fi, Ethernet veya Mobil Erişim Noktası) üzerinden bilgisayarınız ve mobil cihazlarınız arasında yüksek hızlı, güvenli dosya ve pano transferi yapmanızı sağlayan premium, modüler bir masaüstü uygulamasıdır.

Masaüstünde **CustomTkinter** ile modern ve koyu renkli bir arayüz sunarken, web tarafında ise **Apple AirDrop/WeTransfer** sadeliğinde, insan elinden çıkmış hissi uyandıran premium bir açık tema tasarımı kullanır.

---

## ✨ Özellikler

*   **⚡ Ultra Hızlı Aktarım**: İnternet bağlantısı olmasa dahi tamamen yerel ağ hızıyla dosya gönderip alabilirsiniz.
*   **🛞 Masaüstü Sürükle-Bırak (Drag & Drop)**: Bilgisayarınızdaki dosya veya klasörleri doğrudan PyTransfer penceresine sürükleyip bırakarak anında paylaşıma açabilirsiniz. Klasörler arka planda otomatik olarak sıkıştırılır (ZIP).
*   **📡 mDNS (Zeroconf) ile Otomatik Keşif**: Uygulama ağ üzerinde `pytransfer.local` adıyla yayın yapar, böylece IP adresi yazmaya gerek kalmadan kolayca keşfedilebilir.
*   **👥 Aktif Bağlantı Yönetimi (Client Manager)**: Sunucuya bağlı olan cihazları IP adresi ve cihaz bilgisi (tarayıcı/işletim sistemi) ile listeyebilir, istediğiniz cihazın erişimini tek tıkla engelleyebilir (Kara Liste) veya engelini kaldırabilirsiniz.
*   **🔑 Tek Kullanımlık PIN (One-Time PIN / OTP)**: Güvenlik sekmesinden aktif edildiğinde, bir cihaz başarılı giriş yaptıktan 5 saniye sonra sistem otomatik olarak yeni bir PIN kodu üreterek QR kodunu ve erişim şifrelerini yeniler.
*   **📋 Pano Geçmişi (Clipboard History)**: Kopyalanan son 10 pano verisi hem masaüstü uygulamasında hem de mobil web arayüzünde listelenir. İstediğiniz eski pano metnine tıklayarak aktif pano haline getirebilirsiniz.
*   **🎬 Medya Önizleme Oynatıcısı (Media Preview)**: Paylaşılan resim, video (MP4/WebM/OGG) ve ses (MP3/WAV/AAC/M4A) dosyalarını indirmeden doğrudan tarayıcı üzerinden görüntüleyebilir veya oynatabilirsiniz.
*   **🔒 PIN Korumalı Erişim Güvenliği**: Yetkisiz kişilerin dosyalarınıza erişmesini engellemek için tarayıcıda kilit ekranı gösterilir. Güvenlik aktifken tüm API talepleri (dosya listeleme, yükleme, indirme, pano okuma/yazma) engellenir.
*   **📸 QR Kod ile Otomatik Giriş**: Kameranızla QR kodu tarattığınızda veya bağlantıyı kopyaladığınızda, PIN parametresi otomatik işlenir ve şifre yazma penceresi atlanarak giriş yapılır. URL'deki hassas PIN verileri tarayıcı adres barından otomatik silinir.
*   **📦 Klasör Sıkıştırma (ZIP) ve İlerleme Takibi**: Klasörlerinizi paylaşırken arayüzün donmasını önlemek için sıkıştırma işlemi arka planda asenkron iş parçacığı (thread) üzerinde gerçekleştirilir ve anlık yüzdelik ilerleme çubuğuyla takip edilir.
*   **🌐 Çoklu Ağ Arayüzü Desteği**: Windows Mobil Erişim Noktası (Hotspot), Wi-Fi veya Ethernet gibi aktif tüm ağ arayüzlerini ve IP adreslerini otomatik tanır ve etiketler.
*   **🚦 Canlı Son Aktivite Göstergesi**: Masaüstü arayüzünde sunucu başlatma butonunun hemen üstünde ağ hareketleri ("192.168.1.5 bağlandı", "belge.pdf indirildi", "pano güncellendi") tek satırlık canlı log olarak akar.

---

## 🛠️ Kurulum ve Çalıştırma

### Bağımlılık Yöneticisi (`uv` ile)
PyTransfer, hızlı ve kararlı paket yönetimi için modern Astral `uv` paket yöneticisini kullanır.

#### macOS / Linux Kurulumu:
Terminali açıp proje dizinindeyken kurulum scriptini çalıştırmanız yeterlidir:
```bash
chmod +x setup.sh
./setup.sh
```

#### Windows Kurulumu:
PowerShell veya CMD üzerinden `uv` ile bağımlılıkları senkronize edin:
```powershell
# uv yüklü değilse kurun:
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Bağımlılıkları senkronize edin:
uv sync
```

---

## 🚀 Uygulamayı Başlatma

Kurulum tamamlandıktan sonra uygulamayı başlatmak için:
```powershell
uv run main.py
```
veya standart Python kurulu ise:
```powershell
python main.py
```

---

## 📱 Kullanım Adımları

1.  **IP Adresi Seçimi**: Sol paneldeki ağ arayüzü listesinden cihazlarınızın bağlı olduğu IP adresini (Modem Wi-Fi IP'si veya Mobil Erişim Noktası IP'si) seçin.
2.  **Sunucuyu Başlatın**: "Sunucuyu Başlat" butonuna tıklayarak Flask sunucusunu aktif hale getirin.
3.  **QR Kodunu Taratın**: Telefonunuzun kamerasını kullanarak ekrandaki QR kodunu taratın veya "Kopyala" buonuyla URL'yi alarak tarayıcınıza yapıştırın. (QR kod veya kopyalanan URL otomatik oturum açmanızı sağlar).
4.  **Sürükle-Bırak**: Bilgisayarınızdan herhangi bir dosya veya klasörü pencereye bırakarak hızlıca paylaşıma açın.
5.  **Cihazları Yönetin**: "Bağlı Cihazlar" sekmesinden bağlanan IP adreslerini izleyin, istemediğiniz cihazların yanındaki "Engelle" butonuna basarak erişimlerini kesin.
6.  **Güvenlik Ayarlarını Yönetin**: Sağ taraftaki "Ayarlar" sekmesinden PIN korumasını ve Tek Kullanımlık PIN (OTP) özelliğini açıp kapatabilir, 4-6 haneli sayısal özel bir şifre belirleyebilirsiniz.

---

## 📦 Proje Dosya Yapısı

*   `main.py`: Uygulamanın ana giriş kapısı, Tkinter/Flask sinyal koordinatörü ve TkinterDnD2 entegrasyonu.
*   `server.py`: Dosya gönderme/alma, pano geçmişi, cihaz engelleme ve OTP kontrol API'lerini barındıran Flask sunucu arka planı.
*   `utils.py`: Ağ arayüzü tespiti, QR kod üretimi, dosya yönetimi, asenkron ZIP sıkıştırma mantığı ve sürükle-bırak yolu ayrıştırma yardımcısı.
*   `gui/`: CustomTkinter ile yazılmış masaüstü arayüz bileşenleri paketi.
    *   `left_panel.py`: Sunucu düğmesi, QR kod, premium şifre kartı ve tek satırlık canlı aktivite alanı.
    *   `right_panel.py`: Dosya paylaşım sekmeleri, gelen kutusu, pano geçmişi alanı, bağlı cihazlar sekmesi ve ayarlar paneli.
    *   `main_window.py`: Paneller arası iletişimi, sürükle-bırak yönetimini, periyodik sorguları ve veri akışını koordine eden ana GUI sınıfı.
*   `templates/` & `static/`: Web arayüzü HTML, CSS ve medya oynatıcı/kilit ekranı mantığını yöneten JavaScript dosyaları.
