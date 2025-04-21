import yt_dlp
import os
import subprocess

def download_and_convert_audio(url, ffmpeg_path, output_folder="Mi_musica"):
    # Asegúrate de que exista la carpeta de salida
    os.makedirs(output_folder, exist_ok=True)

    # Configuración de yt-dlp
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_folder, '%(title)s.%(ext)s'),
        # si quieres, también puedes pasar 'ffmpeg_location': ffmpeg_path.rsplit('\\',1)[0]
        'quiet': False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Esto descarga y nos devuelve el dict con info del vídeo
        info = ydl.extract_info(url, download=True)
        # Aquí obtenemos el nombre exacto del archivo descargado
        downloaded_file = ydl.prepare_filename(info)

    # Construimos el nombre del MP3
    base, _ = os.path.splitext(downloaded_file)
    mp3_file = base + '.mp3'

    # Llamamos a ffmpeg pasando la ruta absoluta
    subprocess.run([
        ffmpeg_path,
        '-i', downloaded_file,
        mp3_file
    ], check=True)

    # (Opcional) eliminar el original .webm/.m4a
    # os.remove(downloaded_file)

    return mp3_file

if __name__ == '__main__':
    url = input("Introduce la URL del video de YouTube: ")
    ffmpeg_exe = r'E:\bibliotecas\Imagenes\Krita\ffmpeg-2025-04-17-git-7684243fbe-essentials_build\bin\ffmpeg.exe'
    mp3 = download_and_convert_audio(url, ffmpeg_exe)
    print(f"¡Conversión completada! MP3 guardado como:\n{mp3}")



# https://www.youtube.com/watch?v=hcJ9OKKWSG4


# librerias a instalar  pip install yt-dlp
