import flet as ft

def main(page: ft.Page):
    # Sayfa genel ayarları (Modern ve Premium his için)
    page.title = "PyTransfer Flet Test"
    page.window_width = 900
    page.window_height = 650
    page.padding = 30
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#f8fafc" # Ana arka plan (Sade grimsi beyaz)
    
    # Animasyonlu Buton Tıklama Fonksiyonu
    def toggle_server(e):
        if server_btn.content == "Sunucuyu Başlat":
            server_btn.content = "Sunucuyu Durdur"
            server_btn.bgcolor = ft.Colors.RED_500
            status_indicator.value = "● Sunucu Aktif | PIN: 1234"
            status_indicator.color = ft.Colors.GREEN_500
            status_container.bgcolor = ft.Colors.GREEN_50
        else:
            server_btn.content = "Sunucuyu Başlat"
            server_btn.bgcolor = ft.Colors.GREEN_500
            status_indicator.value = "● Durduruldu"
            status_indicator.color = ft.Colors.RED_500
            status_container.bgcolor = ft.Colors.RED_50
        page.update()

    # --- SOL PANEL (Left Panel Benzeri) ---
    
    # 1. Logo ve Başlık
    logo = ft.Row(
        controls=[
            ft.Icon(ft.Icons.UPLOAD_FILE, color=ft.Colors.INDIGO_500, size=32),
            ft.Text("PyTransfer", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_500)
        ]
    )
    subtitle = ft.Text("Yerel ağ üzerinden hızlı veri transferi", color=ft.Colors.GREY_500, size=12)
    
    # 2. Durum Göstergesi (Status Frame)
    status_indicator = ft.Text("● Durduruldu", color=ft.Colors.RED_500, weight=ft.FontWeight.BOLD)
    status_container = ft.Container(
        content=status_indicator,
        bgcolor=ft.Colors.RED_50,
        padding=10,
        border_radius=8,
        width=300
    )

    # 3. Ayarlar
    ip_dropdown = ft.Dropdown(
        label="Ağ Arayüzü (IP)",
        width=300,
        options=[
            ft.dropdown.Option("192.168.1.5 (Wi-Fi)"),
            ft.dropdown.Option("127.0.0.1 (Localhost)")
        ],
        value="192.168.1.5 (Wi-Fi)",
        border_color=ft.Colors.GREY_300
    )
    
    tunnel_switch = ft.Switch(label="İnternete Aç (Dış Ağ)", value=False)
    
    dropzone_btn = ft.ElevatedButton(
        "Dosya İsteği Linki Oluştur",
        icon="upload",
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.BLUE_500,
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
        width=300,
        height=45
    )

    server_btn = ft.ElevatedButton(
        "Sunucuyu Başlat",
        on_click=toggle_server,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.GREEN_500,
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
        width=300,
        height=50
    )

    left_panel = ft.Column(
        controls=[
            logo, subtitle, 
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            status_container,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            ip_dropdown,
            tunnel_switch,
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            dropzone_btn,
            server_btn
        ],
        width=320,
        spacing=10
    )

    # --- SAĞ PANEL (Right Panel Benzeri) ---
    
    # 1. Dropzone Kutusu (Sürükle Bırak)
    upload_zone = ft.Container(
        content=ft.Column(
            controls=[
                ft.Icon(ft.Icons.UPLOAD_FILE, size=50, color=ft.Colors.GREY_400),
                ft.Text("Dosyaları Sürükle veya Seç", size=16, weight=ft.FontWeight.W_500, color=ft.Colors.BLUE_GREY_700),
                ft.Text("Maksimum 5GB", size=12, color=ft.Colors.GREY_500)
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ),
        width=450,
        height=250,
        bgcolor=ft.Colors.WHITE,
        border_radius=12,
        alignment=ft.MainAxisAlignment.CENTER,
        ink=True,
        on_hover=lambda e: setattr(e.control, 'bgcolor', ft.Colors.BLUE_50 if e.data == "true" else ft.Colors.WHITE) or page.update()
    )

    right_panel = ft.Column(
        controls=[
            ft.Text("Dosya Gönder", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
            ft.Text("Aynı ağdaki bilgisayara dosya yollayın", size=13, color=ft.Colors.GREY_500),
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            upload_zone
        ],
        alignment=ft.MainAxisAlignment.START,
    )

    # --- ANA YERLEŞİM ---
    main_layout = ft.Row(
        controls=[
            left_panel,
            ft.VerticalDivider(width=40, color=ft.Colors.GREY_200),
            right_panel
        ],
        vertical_alignment=ft.CrossAxisAlignment.START
    )

    page.add(main_layout)

if __name__ == "__main__":
    ft.app(target=main)
