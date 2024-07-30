import customtkinter as ctk
from tkinter import messagebox, ttk
from pytube import YouTube
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
from PIL import Image
import requests
from io import BytesIO
import os
import traceback
import threading

def fetch_video_details():
    url = url_entry.get()
    spinner.grid(row=6, columnspan=3, pady=10)  # Mostra la rotellina di caricamento
    spinner.start()
    fetch_button.configure(state=ctk.DISABLED)  # Disabilita il bottone durante il caricamento

    def fetch():
        try:
            yt = YouTube(url)
            video_title.set(yt.title)
            video_thumbnail_url.set(yt.thumbnail_url)
            channel_name.set(yt.author)

            # Caricare la miniatura del video
            response = requests.get(yt.thumbnail_url)
            img_data = response.content
            img = Image.open(BytesIO(img_data))
            
            # Ridimensionare l'immagine con un rapporto di 16:9
            width, height = img.size
            new_width = 480  # Aumenta la larghezza della miniatura
            new_height = int(new_width * 9 / 16)  # Altezza della miniatura per mantenere il rapporto 16:9
            img = img.resize((new_width, new_height), Image.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img, size=(new_width, new_height))
            thumbnail_label.configure(image=ctk_img, text="")
            thumbnail_label.image = ctk_img

            # Ottenere le lingue dei sottotitoli
            video_id = yt.video_id
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            subtitle_languages = [(t.language, t.language_code) for t in transcript_list]

            subtitle_menu.configure(values=[lang for lang, code in subtitle_languages])
            if subtitle_languages:
                selected_language.set(subtitle_languages[0][1])  # Seleziona la prima lingua per default
                download_button.configure(state=ctk.NORMAL)  # Abilita il bottone "Scarica Sottotitoli"
            else:
                selected_language.set("")  # Reset se nessuna lingua è disponibile
                download_button.configure(state=ctk.DISABLED)  # Disabilita il bottone "Scarica Sottotitoli"

            # Mostra gli altri campi
            details_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=10)
        except Exception as e:
            messagebox.showerror("Errore", str(e))
            print(traceback.format_exc())  # Stampa l'errore in console
        finally:
            spinner.stop()
            spinner.grid_forget()  # Nasconde la rotellina di caricamento
            fetch_button.configure(state=ctk.NORMAL)  # Abilita il bottone

    threading.Thread(target=fetch).start()

def download_subtitles():
    url = url_entry.get()
    lang = selected_language.get()
    if not lang:
        messagebox.showwarning("Attenzione", "Seleziona una lingua per i sottotitoli")
        return

    yt = YouTube(url)
    video_id = yt.video_id
    video_title = yt.title
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
        subtitles = "\n".join([f"{t['start']} --> {t['start'] + t['duration']}\n{t['text']}" for t in transcript])

        filename = f"{video_title}_{lang}_subs.txt".replace(" ", "_")
        download_path = os.path.join(os.getcwd(), 'download', filename)
        os.makedirs(os.path.dirname(download_path), exist_ok=True)
        with open(download_path, 'w', encoding='utf-8') as file:
            file.write(subtitles)

        messagebox.showinfo("Successo", f"Sottotitoli scaricati: {download_path}")
    except NoTranscriptFound as e:
        messagebox.showerror("Errore", f"Non è stato possibile trovare i sottotitoli per la lingua selezionata: {lang}")
        print(traceback.format_exc())  # Stampa l'errore in console
    except Exception as e:
        messagebox.showerror("Errore", str(e))
        print(traceback.format_exc())  # Stampa l'errore in console

# Configurazione dell'interfaccia grafica
ctk.set_appearance_mode("dark")  # Imposta il tema dark
ctk.set_default_color_theme("blue")  # Imposta il tema blu

root = ctk.CTk()
root.title("YouTube Subtitle Downloader")

# Frame per i dettagli del video (nascosto all'avvio)
details_frame = ctk.CTkFrame(root)

# URL Input
ctk.CTkLabel(root, text="Inserisci l'URL del video YouTube:").grid(row=0, column=0, padx=10, pady=5)
url_entry = ctk.CTkEntry(root, width=400)
url_entry.grid(row=0, column=1, padx=10, pady=5)

# Button to fetch video details
fetch_button = ctk.CTkButton(root, text="Carica Dettagli", command=fetch_video_details)
fetch_button.grid(row=0, column=2, padx=10, pady=5)

# Video Details in details_frame
ctk.CTkLabel(details_frame, text="Titolo:").grid(row=0, column=0, padx=10, pady=5, sticky='e')
video_title = ctk.StringVar()
ctk.CTkLabel(details_frame, textvariable=video_title).grid(row=0, column=1, padx=10, pady=5, sticky='w')

ctk.CTkLabel(details_frame, text="Thumbnail:").grid(row=1, column=0, padx=10, pady=5, sticky='e')
video_thumbnail_url = ctk.StringVar()
thumbnail_label = ctk.CTkLabel(details_frame, text="")  # Inizializza senza testo
thumbnail_label.grid(row=1, column=1, padx=10, pady=5)

ctk.CTkLabel(details_frame, text="Nome del Canale:").grid(row=2, column=0, padx=10, pady=5, sticky='e')
channel_name = ctk.StringVar()
ctk.CTkLabel(details_frame, textvariable=channel_name, wraplength=400).grid(row=2, column=1, padx=10, pady=5, sticky='w')

# Subtitle Language Selection
ctk.CTkLabel(details_frame, text="Lingua dei Sottotitoli:").grid(row=3, column=0, padx=10, pady=5, sticky='e')
selected_language = ctk.StringVar()
subtitle_menu = ctk.CTkOptionMenu(details_frame, variable=selected_language)
subtitle_menu.grid(row=3, column=1, padx=10, pady=5, sticky='w')

# Download Button
download_button = ctk.CTkButton(details_frame, text="Scarica Sottotitoli", command=download_subtitles, state=ctk.DISABLED)
download_button.grid(row=4, columnspan=2, pady=20)

# Loading Spinner
spinner = ttk.Progressbar(root, mode='indeterminate', length=250)
spinner.grid(row=5, columnspan=3, pady=10)
spinner.grid_forget()

# Avvio dell'interfaccia grafica
root.mainloop()
