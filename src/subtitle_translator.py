from googletrans import Translator
import json
from typing import List, Dict
from moviepy.editor import VideoFileClip
import moviepy.config as conf
import os

# Configure ImageMagick path
if os.name == "nt":  # for Windows
    IMAGEMAGICK_BINARY = r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"
    conf.change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_BINARY})


class SubtitleTranslator:
    def __init__(self):
        self.translator = Translator()
        self.supported_languages = {
            "English": "en",
            "Hindi": "hi",
            "French": "fr",
            "German": "de",
            "Korean": "ko",
        }

    def translate_subtitles(self, subtitle_file, target_lang):
        # Read subtitle file
        print(f"Reading file: {subtitle_file}")
        try:
            with open(subtitle_file, "r", encoding="utf-8") as f:
                subtitles = json.load(f)

            # Translate each subtitle
            translated_subtitles = []
            for subtitle in subtitles:
                text = subtitle.get("text", "")
                if text:
                    try:
                        translation = self.translator.translate(text, dest=target_lang)
                        translated_subtitles.append(
                            {
                                "start": subtitle["start"],
                                "end": subtitle["end"],
                                "text": translation.text,
                            }
                        )
                    except Exception as e:
                        print(f"Translation error: {e}")
                        translated_subtitles.append(subtitle)
                        continue

            # Save translated subtitles
            output_path = subtitle_file.rsplit(".", 1)[0] + f"_{target_lang}.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(translated_subtitles, f, ensure_ascii=False, indent=2)

            return output_path

        except Exception as e:
            print(f"Error processing file: {e}")
            return None


# Usage example
if __name__ == "__main__":
    try:
        translator = SubtitleTranslator()
        result = translator.translate_subtitles("your_input_file.json", "fr")
        if result:
            print(f"Translation completed. Output saved to: {result}")
        else:
            print("Translation failed")
    except Exception as e:
        print(f"Main execution error: {e}")
