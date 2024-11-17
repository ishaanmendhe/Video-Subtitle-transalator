# src/file_manager.py
import os
from tempfile import NamedTemporaryFile


class FileManager:
    def __init__(self):
        self.temp_files = []

    def create_temp_file(self, suffix=".mp3"):
        temp_file = NamedTemporaryFile(suffix=suffix, delete=False)
        self.temp_files.append(temp_file)
        return temp_file

    def cleanup_temp_files(self):
        for temp_file in self.temp_files:
            try:
                os.remove(temp_file.name)
            except OSError:
                pass
        self.temp_files.clear()
