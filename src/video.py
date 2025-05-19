import os
import sys
import yt_dlp

# Detectar la ruta al ejecutable de ffmpeg
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.abspath(".")

FFMPEG_PATH = os.path.join(base_path, "ffmpeg", "ffmpeg.exe")
OUTPUT_FOLDER = os.path.join(os.getcwd(), "Downloaded Videos")

def descargar_video(url):
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    opciones = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': os.path.join(OUTPUT_FOLDER, '%(title)s.%(ext)s'),
        'ffmpeg_location': FFMPEG_PATH,
        'merge_output_format': 'mp4',
        'noplaylist': True,
    }

    with yt_dlp.YoutubeDL(opciones) as ydl:
        info = ydl.extract_info(url, download=True)
        print(f"✅ Descarga completada: {info['title']}")

if __name__ == "__main__":
    print("🎬 Descargador de YouTube (escribí 'salir' para terminar)\n")
    while True:
        url = input("🎥 Pegá la URL de YouTube (o escribí 'salir'): ").strip()
        if url.lower() == 'salir':
            break
        if url:
            try:
                descargar_video(url)
            except Exception as e:
                print(f"❌ Error al descargar el video: {e}")

