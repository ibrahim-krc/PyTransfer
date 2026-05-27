#!/bin/bash

# Hata durumunda scripti sonlandır
set -e

echo "=== PyTransfer Kurulum Sihirbazı ==="

# 1. Python 3 kontrolü
if ! command -v python3 &> /dev/null; then
    echo "Hata: Python 3 yüklü değil! Lütfen sisteminize Python 3 kurup tekrar deneyin."
    exit 1
fi

# 2. UV paket yöneticisi kontrolü ve kurulumu
if ! command -v uv &> /dev/null; then
    echo "Bilgi: Astral 'uv' bulunamadı. Kuruluyor..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Yol tanımlamasını yükle
    if [ -f "$HOME/.local/bin/env" ]; then
        source "$HOME/.local/bin/env"
    fi
else
    echo "Bilgi: Astral 'uv' zaten yüklü."
fi

# 3. Bağımlılıkları senkronize et
echo "Bilgi: Sanal ortam kuruluyor ve bağımlılıklar senkronize ediliyor..."
uv sync

echo "=== Kurulum Başarıyla Tamamlandı! ==="
echo "Uygulamayı başlatmak için şu komutu çalıştırabilirsiniz:"
echo "  uv run main.py"
