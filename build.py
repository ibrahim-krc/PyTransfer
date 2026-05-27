"""
PyTransfer - EXE Build Scripti
Kullanim: uv run python build.py
       veya: python build.py
"""
import os
import sys
import shutil
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))


def run(cmd_list):
    """Komut listesini subprocess ile calistirir."""
    print(f"\n>>> {' '.join(cmd_list)}\n")
    result = subprocess.run(cmd_list)
    if result.returncode != 0:
        print(f"HATA: Komut basarisiz oldu (kod {result.returncode})")
        sys.exit(result.returncode)


def find_package_path(pkg_name):
    """Kurulu bir paketin dizin yolunu bulur."""
    import importlib.util
    spec = importlib.util.find_spec(pkg_name)
    if spec and spec.submodule_search_locations:
        return list(spec.submodule_search_locations)[0]
    return None


def main():
    print("=" * 55)
    print("  PyTransfer EXE Build")
    print("=" * 55)

    try:
        import PyInstaller
        print(f"PyInstaller {PyInstaller.__version__} bulundu.")
    except ImportError:
        print("PyInstaller bulunamadi, yukleniyor...")
        run([sys.executable, "-m", "pip", "install", "pyinstaller"])

    ctk_path   = find_package_path("customtkinter")
    tkdnd_path = find_package_path("tkinterdnd2")

    if not ctk_path:
        print("HATA: customtkinter paketi bulunamadi.")
        sys.exit(1)
    if not tkdnd_path:
        print("HATA: tkinterdnd2 paketi bulunamadi.")
        sys.exit(1)

    print(f"customtkinter : {ctk_path}")
    print(f"tkinterdnd2   : {tkdnd_path}")

    for d in ["build", "dist"]:
        if os.path.exists(d):
            shutil.rmtree(d)
            print(f"Temizlendi: {d}/")

    spec_file = os.path.join(ROOT, "pytransfer.spec")
    if os.path.exists(spec_file):
        os.remove(spec_file)

    sep = ";" if sys.platform == "win32" else ":"

    add_data = [
        f"templates{sep}templates",
        f"static{sep}static",
        f"assets{sep}assets",
        f"{ctk_path}{sep}customtkinter",
        f"{tkdnd_path}{sep}tkinterdnd2",
    ]

    hidden = [
        "customtkinter",
        "tkinterdnd2",
        "PIL._tkinter_finder",
        "zeroconf._utils.ipaddress",
        "zeroconf._dns",
        "zeroconf._services",
        "flask",
        "werkzeug",
        "qrcode",
        "qrcode.image.pil",
    ]

    args = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "Py Transfer",
    ]

    if os.path.exists(os.path.join("assets", "logo.ico")):
        args += ["--icon", os.path.join("assets", "logo.ico")]

    for d in add_data:
        args += ["--add-data", d]

    for h in hidden:
        args += ["--hidden-import", h]

    args.append("main.py")

    run(args)

    exe_path = os.path.join(ROOT, "dist", "PyTransfer.exe")
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print("\n" + "=" * 55)
        print(f"  BASARILI! EXE olusturuldu:")
        print(f"  dist\\PyTransfer.exe  ({size_mb:.1f} MB)")
        print("=" * 55)
    else:
        print("\nHATA: EXE olusturulamadi, yukaridaki hatalari kontrol edin.")
        sys.exit(1)


if __name__ == "__main__":
    main()
