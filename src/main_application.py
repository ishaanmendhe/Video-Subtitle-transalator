import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
from speech_to_text import SpeechToTextProcessor
from subtitle_burner import SubtitleBurner
from subtitle_translator import SubtitleTranslator


class VideoSubtitleApp:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Video Subtitle Translator")
        self.window.geometry("800x600")

        self.setup_gui()

    def setup_gui(self):
        # File selection
        file_frame = ttk.LabelFrame(self.window, text="Video Selection")
        file_frame.pack(fill="x", padx=10, pady=5)

        self.file_path = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.file_path, width=60).pack(
            side="left", padx=5, pady=5
        )
        ttk.Button(file_frame, text="Browse", command=self.browse_file).pack(
            side="left", padx=5
        )

        # Language selection
        lang_frame = ttk.LabelFrame(self.window, text="Translation Settings")
        lang_frame.pack(fill="x", padx=10, pady=5)

        self.source_lang = tk.StringVar(value="English")
        self.target_lang = tk.StringVar(value="Hindi")

        ttk.Label(lang_frame, text="Video Language:").pack(side="left", padx=5)
        ttk.Combobox(
            lang_frame,
            textvariable=self.source_lang,
            values=list(SubtitleTranslator().supported_languages.keys()),
            state="readonly",
        ).pack(side="left", padx=5)

        ttk.Label(lang_frame, text="Target Language:").pack(side="left", padx=5)
        ttk.Combobox(
            lang_frame,
            textvariable=self.target_lang,
            values=list(SubtitleTranslator().supported_languages.keys()),
            state="readonly",
        ).pack(side="left", padx=5)

        # Progress frame
        self.progress_frame = ttk.LabelFrame(self.window, text="Progress")
        self.progress_frame.pack(fill="x", padx=10, pady=5)

        self.progress_var = tk.StringVar(value="Ready")
        ttk.Label(self.progress_frame, textvariable=self.progress_var).pack(
            padx=5, pady=5
        )

        self.progress_bar = ttk.Progressbar(self.progress_frame, mode="indeterminate")
        self.progress_bar.pack(fill="x", padx=5, pady=5)

        # Process button
        ttk.Button(self.window, text="Process Video", command=self.process_video).pack(
            pady=10
        )

    def browse_file(self):
        filename = filedialog.askopenfilename(
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
        )
        if filename:
            self.file_path.set(filename)

    def process_video(self):
        if not self.file_path.get():
            messagebox.showerror("Error", "Please select a video file")
            return

        self.progress_bar.start()
        threading.Thread(target=self.process_video_thread, daemon=True).start()

    def process_video_thread(self):
        try:
            video_path = self.file_path.get()
            source_lang_code = SubtitleTranslator().supported_languages[
                self.source_lang.get()
            ]
            target_lang_code = SubtitleTranslator().supported_languages[
                self.target_lang.get()
            ]

            # Step 1: Speech to Text
            self.progress_var.set("Converting speech to text...")
            processor = SpeechToTextProcessor("13929b8e92cc44f18fdd295a286ab418")
            subtitle_file = processor.process_video(video_path, source_lang_code)

            # Step 2: Translate
            self.progress_var.set("Translating subtitles...")
            translator = SubtitleTranslator()
            translated_file = translator.translate_subtitles(
                subtitle_file, target_lang_code
            )

            # Step 3: Burn subtitles
            self.progress_var.set("Adding subtitles to video...")
            output_path = (
                video_path.rsplit(".", 1)[0] + f"_subtitled_{target_lang_code}.mp4"
            )
            burner = SubtitleBurner(video_path, translated_file)
            burner.process_video(output_path)

            self.progress_var.set("Complete!")
            messagebox.showinfo(
                "Success", f"Video processed successfully!\nSaved to: {output_path}"
            )

        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.progress_bar.stop()


if __name__ == "__main__":
    app = VideoSubtitleApp()
    app.window.mainloop()
