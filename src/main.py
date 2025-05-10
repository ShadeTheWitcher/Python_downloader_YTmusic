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
        self.root.configure(padx=15, pady=15)

        # Fila 0: URL
        url_frame = tk.Frame(self.root)
        url_frame.grid(row=0, column=0, columnspan=2, pady=5, sticky="w")
        tk.Label(url_frame, text="🎥 URL de YouTube:").pack(side="left")
        self.url_entry = tk.Entry(url_frame, width=50)
        self.url_entry.pack(side="left", padx=(5, 0))
        tk.Button(url_frame, text="📋", command=self.paste_url).pack(side="left", padx=5)
        tk.Button(url_frame, text="Procesar URL🔍", command=self.fetch_info).pack(side="left")

        # Fila 1-3: Metadata
        self._add_label_entry("Título:", 1)
        self._add_label_entry("Artista:", 2)
        self._add_label_entry("Álbum:", 3)

        # Fila 4: Imagen
        img_frame = tk.Frame(self.root)
        img_frame.grid(row=4, column=0, columnspan=2, pady=10, sticky="w")
        tk.Label(img_frame, text="🎨 Carátula:").pack(side="left")
        self.image_label = tk.Label(img_frame)
        self.image_label.pack(side="left", padx=10)
        tk.Button(img_frame, text="Cambiar imagen", command=self.select_image).pack(side="left")

        # Fila 5: Botones de acción
        btn_frame = tk.Frame(self.root)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)
        tk.Button(btn_frame, text="⬇️Download MP3", command=self.start_download_thread, width=20).pack(side="left", padx=10)
        tk.Button(btn_frame, text="Buscar metadata oficial", command=self.fetch_metadata_from_musicbrainz, width=25).pack(side="left", padx=10)

        # Fila 6: Barra de progreso
        self.progress = ttk.Progressbar(self.root, length=500, mode='determinate')
        self.progress.grid(row=6, column=0, columnspan=2, pady=(5, 15))

        # Fila 7-8: Consola
        tk.Label(self.root, text="🖥 Consola:").grid(row=7, column=0, sticky='w')
        self.console = tk.Text(self.root, height=10, width=80, state='disabled', bg="#111", fg="#0f0")
        self.console.grid(row=8, column=0, columnspan=2)

        # Fila 9: Limpiar
        tk.Button(self.root, text="Limpiar", command=self.clear_fields, width=20).grid(row=9, column=0, columnspan=2, pady=15)

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
        # Limpiar los campos antes de cargar nueva información
        self.título_entry.delete(0, tk.END)
        self.artista_entry.delete(0, tk.END)
        self.álbum_entry.delete(0, tk.END)
        self.image_label.configure(image='')
        self.image_label.image = None
        self.thumb_data = None

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

            self.título_entry.insert(0, info.get("title", ""))
            self.artista_entry.insert(0, info.get("uploader", ""))
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

    def fetch_metadata_from_musicbrainz(self):
        title = self.título_entry.get().strip()
        artist = self.artista_entry.get().strip()

        if not title or not artist:
            messagebox.showerror("Error", "Debes ingresar un título y artista primero.")
            return

        self.log("🔍 Buscando metadata oficial...")
        
        try:
            # Configurar los headers con un User-Agent
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
            }
            
            # Consultar MusicBrainz API
            search_url = f"https://musicbrainz.org/ws/2/recording?query=artist:{artist}+recording:{title}&fmt=json"
            response = requests.get(search_url, headers=headers)

            # Verificar si la respuesta es correcta
            if response.status_code == 403:
                self.log(f"❌ Error 403: Acceso denegado por MusicBrainz.")
                messagebox.showerror("Error 403", "Acceso denegado por MusicBrainz. Intenta más tarde.")
                return

            if response.status_code != 200:
                self.log(f"❌ Error al consultar MusicBrainz: {response.status_code}")
                messagebox.showerror("Error", f"No se pudo obtener datos de MusicBrainz. Código de error: {response.status_code}")
                return

            data = response.json()

            if not data.get("recordings"):
                messagebox.showwarning("No encontrado", "No se encontró metadata oficial.")
                return

            recording = data["recordings"][0]
            mb_title = recording.get("title", title)
            mb_artist = recording.get("artist", artist)
            mb_album = recording.get("releases", [{}])[0].get("title", "Unknown")

            # Actualizar los campos de la UI
            self.título_entry.delete(0, tk.END)
            self.título_entry.insert(0, mb_title)
            self.artista_entry.delete(0, tk.END)
            self.artista_entry.insert(0, mb_artist)
            self.álbum_entry.delete(0, tk.END)
            self.álbum_entry.insert(0, mb_album)

            # Buscar portada en Cover Art Archive
            release_id = recording["releases"][0]["id"]
            cover_url = f"https://coverartarchive.org/release/{release_id}/front"
            cover_response = requests.get(cover_url)

            if cover_response.status_code == 200:
                self.thumb_data = cover_response.content
                img = Image.open(io.BytesIO(self.thumb_data)).resize((100, 100))
                img_tk = ImageTk.PhotoImage(img)
                self.image_label.configure(image=img_tk)
                self.image_label.image = img_tk

            self.log("✅ Metadata oficial encontrada y actualizada.")
        except Exception as e:
            self.log(f"❌ Error: {e}")
            messagebox.showerror("Error", f"No se pudo obtener la metadata: {e}")

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
        # Asegúrate de que la URL, título y artista estén presentes antes de continuar
        url = self.url_entry.get().strip()
        title = self.título_entry.get().strip()
        artist = self.artista_entry.get().strip()
        if not url or not title or not artist:
            messagebox.showerror("Error", "Faltan campos obligatorios.")
            return
        
        # Llamar a la función de descarga en otro hilo
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

            result = subprocess.run([FFMPEG_PATH, "-i", downloaded_file, mp3_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

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

    def clear_fields(self):
        """Limpia todos los campos para ingresar nueva música."""
        self.url_entry.delete(0, tk.END)
        self.título_entry.delete(0, tk.END)
        self.artista_entry.delete(0, tk.END)
        self.álbum_entry.delete(0, tk.END)
        self.image_label.configure(image='')
        self.image_label.image = None
        self.thumb_data = None
        self.progress['value'] = 0
        self.console.configure(state='normal')
        self.console.delete(1.0, tk.END)
        self.console.configure(state='disabled')

    def paste_url(self):
        try:
            clipboard_content = self.root.clipboard_get()
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, clipboard_content)
        except tk.TclError:
            messagebox.showerror("Error", "No se pudo acceder al portapapeles.")

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
