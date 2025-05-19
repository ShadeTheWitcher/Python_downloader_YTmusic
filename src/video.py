import os
import sys
import yt_dlp

# Carpeta de salida
OUTPUT_FOLDER = "Downloaded Videos"

# Detectar si está corriendo como exe (PyInstaller)
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.abspath(".")

# Ruta a ffmpeg dentro de la carpeta ffmpeg
FFMPEG_PATH = os.path.join(base_path, "ffmpeg", "ffmpeg.exe")

def download_youtube_audio(url):
    if not url.strip():
        print("❌ URL vacía.")
        return

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio/best',
        'ffmpeg_location': FFMPEG_PATH,
        'outtmpl': os.path.join(OUTPUT_FOLDER, '%(title)s.%(ext)s'),
        'noplaylist': True,
        'quiet': False,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("🔍 Procesando URL...")
            info = ydl.extract_info(url, download=True)
            print(f"✅ Descarga completada: {info.get('title')}.mp3")
    except Exception as e:
        print(f"❌ Error al descargar: {e}")

if __name__ == "__main__":
    print("🎬 Descargador de YouTube (escribí 'salir' para terminar)\n")

    while True:
        url = input("🎥 Pegá la URL de YouTube (o escribí 'salir'): ").strip()
        if url.lower() == 'salir':
            print("👋 Saliendo...")
            break
        download_youtube_audio(url)
        print()
