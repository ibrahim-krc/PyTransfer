import os
import urllib.request

icons = {
    "video": "https://img.icons8.com/ios-filled/50/ffffff/video.png",
    "audio": "https://img.icons8.com/ios-filled/50/ffffff/musical-notes.png",
    "image": "https://img.icons8.com/ios-filled/50/ffffff/image.png",
    "archive": "https://img.icons8.com/ios-filled/50/ffffff/archive.png",
    "document": "https://img.icons8.com/ios-filled/50/ffffff/document.png",
    "default": "https://img.icons8.com/ios-filled/50/ffffff/file.png"
}

os.makedirs("assets/icons", exist_ok=True)

for name, url in icons.items():
    path = f"assets/icons/{name}.png"
    print(f"Downloading {name}...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response, open(path, 'wb') as out_file:
        data = response.read()
        out_file.write(data)
print("Done!")
