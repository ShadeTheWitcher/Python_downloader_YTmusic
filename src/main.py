import os
import io
import sys
import requests
import yt_dlp
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
import subprocess
from threading import Thread

# Ruta al ffmpeg
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.abspath(".")

FFMPEG_PATH = os.path.join(base_path, "ffmpeg", "ffmpeg.exe")  # Ruta relativa a la carpeta "ffmpeg"
OUTPUT_FOLDER = "Downloaded Music"

class YouTubeMP3Downloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube MP3 Downloader")

        # GUI
        self._build_gui()

        # Inicializar variables
        self.thumb_data = None
        self.info_dict = None

    def _build_gui(self):
        # Campos
        tk.Label(self.root, text="URL de YouTube:").grid(row=0, column=0, sticky='e')
        self.url_entry = tk.Entry(self.root, width=60)
        self.url_entry.grid(row=0, column=1, columnspan=3)
        self.load_btn = tk.Button(self.root, text="Cargar info", command=self.fetch_info)
        self.load_btn.grid(row=0, column=4, padx=5)

        self._add_label_entry("Título:", 1)
        self._add_label_entry("Artista:", 2)
        self._add_label_entry("Álbum:", 3)

        tk.Label(self.root, text="Carátula:").grid(row=4, column=0, sticky='e')
        self.image_label = tk.Label(self.root)
        self.image_label.grid(row=4, column=1, columnspan=2)
        self.change_image_btn = tk.Button(self.root, text="Cambiar imagen", command=self.select_image)
        self.change_image_btn.grid(row=4, column=3)

        self.download_btn = tk.Button(self.root, text="Descargar MP3", command=self.start_download_thread)
        self.download_btn.grid(row=5, column=1, columnspan=2, pady=10)

        # Barra de progreso
        self.progress = ttk.Progressbar(self.root, length=400, mode='determinate')
        self.progress.grid(row=6, column=0, columnspan=5, pady=(0, 10))

        # Consola
        tk.Label(self.root, text="Consola:").grid(row=7, column=0, sticky='nw')
        self.console = tk.Text(self.root, height=10, width=80, state='disabled', bg="#111", fg="#0f0")
        self.console.grid(row=8, column=0, columnspan=5, padx=5, pady=5)

    def _add_label_entry(self, label_text, row):
        tk.Label(self.root, text=label_text).grid(row=row, column=0, sticky='e')
        entry = tk.Entry(self.root, width=50)
        entry.grid(row=row, column=1, columnspan=3)
        setattr(self, f"{label_text[:-1].lower()}_entry", entry)

    def log(self, msg):
        self.console.configure(state='normal')
        self.console.insert(tk.END, msg + '\n')
        self.console.configure(state='disabled')
        self.console.see(tk.END)

    def fetch_info(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Introduce una URL válida.")
            return
        try:
            self.log("🔍 Obteniendo información del video...")
            ydl_opts = {'quiet': True, 'skip_download': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                self.info_dict = info

            self.título_entry.delete(0, tk.END)
            self.título_entry.insert(0, info.get("title", ""))
            self.artista_entry.delete(0, tk.END)
            self.artista_entry.insert(0, info.get("uploader", ""))
            self.álbum_entry.delete(0, tk.END)
            self.álbum_entry.insert(0, info.get("album", "YouTube"))

            thumb_url = info.get("thumbnail")
            if thumb_url:
                response = requests.get(thumb_url)
                self.thumb_data = response.content
                img = Image.open(io.BytesIO(self.thumb_data)).resize((100, 100))
                img_tk = ImageTk.PhotoImage(img)
                self.image_label.configure(image=img_tk)
                self.image_label.image = img_tk

            self.log("✅ Información cargada correctamente.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def select_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Imágenes", "*.jpg *.jpeg *.png")])
        if file_path:
            with open(file_path, "rb") as f:
                self.thumb_data = f.read()
            img = Image.open(io.BytesIO(self.thumb_data)).resize((100, 100))
            img_tk = ImageTk.PhotoImage(img)
            self.image_label.configure(image=img_tk)
            self.image_label.image = img_tk

    def start_download_thread(self):
        thread = Thread(target=self.download_audio)
        thread.start()

    def download_audio(self):
        url = self.url_entry.get().strip()
        title = self.título_entry.get().strip()
        artist = self.artista_entry.get().strip()
        album = self.álbum_entry.get().strip()

        if not all([url, title, artist]):
            messagebox.showerror("Error", "Faltan campos obligatorios.")
            return

        self.progress['value'] = 0
        self.log("🚀 Iniciando descarga...")

        try:
            os.makedirs(OUTPUT_FOLDER, exist_ok=True)

            def progress_hook(d):
                if d['status'] == 'downloading':
                    percent = d.get('_percent_str', '0.0%').replace('%', '').strip()
                    try:
                        self.progress['value'] = float(percent)
                    except ValueError:
                        pass
                elif d['status'] == 'finished':
                    self.progress['value'] = 100
                    self.log("✅ Descarga completada. Iniciando conversión...")

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(OUTPUT_FOLDER, '%(title)s.%(ext)s'),
                'progress_hooks': [progress_hook],
                'quiet': True,
                'noplaylist': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                downloaded_file = ydl.prepare_filename(info)

            base, _ = os.path.splitext(downloaded_file)
            mp3_file = base + ".mp3"

            result = subprocess.run([
                FFMPEG_PATH, "-i", downloaded_file, mp3_file
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            self.log(result.stdout)
            self.log(result.stderr)

            # Metadata
            audio = EasyID3(mp3_file)
            audio["title"] = title
            audio["artist"] = artist
            audio["album"] = album
            audio.save()

            if self.thumb_data:
                audio = ID3(mp3_file)
                audio["APIC"] = APIC(
                    encoding=3,
                    mime="image/jpeg",
                    type=3, desc="Cover",
                    data=self.thumb_data
                )
                audio.save()

            os.remove(downloaded_file)
            self.log(f"🎵 ¡MP3 guardado como: {mp3_file}")
            messagebox.showinfo("Éxito", f"MP3 creado:\n{mp3_file}")
        except Exception as e:
            self.log(f"❌ Error: {e}")
            messagebox.showerror("Error", str(e))

# Lanzar la app
if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeMP3Downloader(root)
    root.mainloop()




# https://www.youtube.com/watch?v=hcJ9OKKWSG4


# librerias a instalar  
# pip install yt-dlp  
# pip install requests
# pip install mutagen pillow


#pip install -r requirements.txt
