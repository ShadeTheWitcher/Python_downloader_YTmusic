import os
import io
import requests
import yt_dlp
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
import subprocess

FFMPEG_PATH = r'E:\bibliotecas\Imagenes\Krita\ffmpeg-2025-04-17-git-7684243fbe-essentials_build\bin\ffmpeg.exe'
OUTPUT_FOLDER = "Mi_musica"

class YouTubeMP3Downloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube MP3 Downloader")

        # URL
        tk.Label(root, text="URL de YouTube:").grid(row=0, column=0, sticky='e')
        self.url_entry = tk.Entry(root, width=60)
        self.url_entry.grid(row=0, column=1, columnspan=3)

        # Botón de carga
        self.load_btn = tk.Button(root, text="Cargar info", command=self.fetch_info)
        self.load_btn.grid(row=0, column=4, padx=5)

        # Campos de metadatos
        self._add_label_entry("Título:", 1)
        self._add_label_entry("Artista:", 2)
        self._add_label_entry("Álbum:", 3)

        # Imagen
        tk.Label(root, text="Carátula:").grid(row=4, column=0, sticky='e')
        self.image_label = tk.Label(root)
        self.image_label.grid(row=4, column=1, columnspan=2)
        self.change_image_btn = tk.Button(root, text="Cambiar imagen", command=self.select_image)
        self.change_image_btn.grid(row=4, column=3)

        # Botón de descarga
        self.download_btn = tk.Button(root, text="Descargar MP3", command=self.download_audio)
        self.download_btn.grid(row=5, column=1, columnspan=2, pady=10)

        # Estado
        self.status = tk.Label(root, text="")
        self.status.grid(row=6, column=0, columnspan=5)

        # Inicializar
        self.thumb_data = None
        self.info_dict = None

    def _add_label_entry(self, label_text, row):
        tk.Label(self.root, text=label_text).grid(row=row, column=0, sticky='e')
        entry = tk.Entry(self.root, width=50)
        entry.grid(row=row, column=1, columnspan=3)
        setattr(self, f"{label_text[:-1].lower()}_entry", entry)

    def fetch_info(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Por favor, introduce una URL válida.")
            return

        try:
            self.status.config(text="Obteniendo información...")
            self.root.update_idletasks()
            ydl_opts = {'quiet': True, 'skip_download': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                self.info_dict = info

            title = info.get("title", "")
            artist = info.get("uploader", "")
            album = info.get("album", "")

            self.título_entry.delete(0, tk.END)
            self.título_entry.insert(0, title)
            self.artista_entry.delete(0, tk.END)
            self.artista_entry.insert(0, artist)
            self.álbum_entry.delete(0, tk.END)
            self.álbum_entry.insert(0, album or "YouTube")

            # Descargar thumbnail
            thumb_url = info.get("thumbnail")
            if thumb_url:
                response = requests.get(thumb_url)
                self.thumb_data = response.content
                img = Image.open(io.BytesIO(self.thumb_data)).resize((100, 100))
                img_tk = ImageTk.PhotoImage(img)
                self.image_label.configure(image=img_tk)
                self.image_label.image = img_tk

            self.status.config(text="Información cargada correctamente.")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo obtener la info del video:\n{e}")
            self.status.config(text="")

    def select_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Imágenes", "*.jpg *.jpeg *.png")])
        if file_path:
            with open(file_path, "rb") as f:
                self.thumb_data = f.read()
            img = Image.open(io.BytesIO(self.thumb_data)).resize((100, 100))
            img_tk = ImageTk.PhotoImage(img)
            self.image_label.configure(image=img_tk)
            self.image_label.image = img_tk

    def download_audio(self):
        url = self.url_entry.get().strip()
        title = self.título_entry.get().strip()
        artist = self.artista_entry.get().strip()
        album = self.álbum_entry.get().strip()

        if not all([url, title, artist]):
            messagebox.showerror("Error", "Faltan campos obligatorios.")
            return

        try:
            self.status.config(text="Descargando audio...")
            self.root.update_idletasks()

            os.makedirs(OUTPUT_FOLDER, exist_ok=True)

            # yt-dlp descarga
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(OUTPUT_FOLDER, '%(title)s.%(ext)s'),
                'quiet': True
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                downloaded_file = ydl.prepare_filename(info)

            # Convertir a mp3
            base, _ = os.path.splitext(downloaded_file)
            mp3_file = base + ".mp3"
            subprocess.run([
                FFMPEG_PATH,
                "-i", downloaded_file,
                mp3_file
            ], check=True)

            # Escribir metadatos
            audio = EasyID3(mp3_file)
            audio["title"] = title
            audio["artist"] = artist
            audio["album"] = album
            audio.save()

            # Agregar imagen
            if self.thumb_data:
                audio = ID3(mp3_file)
                audio["APIC"] = APIC(
                    encoding=3,
                    mime="image/jpeg",
                    type=3, desc="Cover",
                    data=self.thumb_data
                )
                audio.save()

            # Eliminar archivo original
            os.remove(downloaded_file)

            self.status.config(text=f"¡Descarga y conversión completadas!\nArchivo: {mp3_file}")
            messagebox.showinfo("Éxito", f"MP3 guardado en:\n{mp3_file}")

        except Exception as e:
            messagebox.showerror("Error", f"Error en la descarga o conversión:\n{e}")
            self.status.config(text="")

# Lanzar app
if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeMP3Downloader(root)
    root.mainloop()



# https://www.youtube.com/watch?v=hcJ9OKKWSG4


# librerias a instalar  
# pip install yt-dlp  
# pip install requests
# pip install mutagen pillow


