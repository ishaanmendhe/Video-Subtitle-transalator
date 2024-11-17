import requests
import sys
from tempfile import NamedTemporaryFile
from moviepy.editor import VideoFileClip
import os
import json
from pydub import AudioSegment, silence


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


class SpeechToTextProcessor:
    def __init__(self, api_key):
        self.upload_endpoint = "https://api.assemblyai.com/v2/upload"
        self.transcript_endpoint = "https://api.assemblyai.com/v2/transcript"
        self.headers = {"authorization": api_key}
        self.file_manager = FileManager()

    def process_video(self, video_path, language_code):
        audio_url = self.upload(video_path)
        transcript_data = self.get_timestamped_transcript(audio_url, language_code)
        output_path = os.path.join(
            "timestamps", os.path.basename(video_path).split(".")[0] + ".json"
        )
        self.save_transcript(transcript_data, output_path)
        return output_path

    def upload(self, filename):
        """
        Uploads the audio extracted from the video to AssemblyAI's API.
        """
        video_clip = VideoFileClip(filename)
        audio_clip = video_clip.audio
        temp_audio = self.file_manager.create_temp_file()

        try:
            audio_clip.write_audiofile(temp_audio.name)

            def read_file(filename, chunk_size=524880):
                with open(filename, "rb") as f:
                    while True:
                        data = f.read(chunk_size)
                        if not data:
                            break
                        yield data

            upload_response = requests.post(
                self.upload_endpoint,
                headers=self.headers,
                data=read_file(temp_audio.name),
            )

            return upload_response.json()["upload_url"]
        finally:
            audio_clip.close()
            video_clip.close()
            self.file_manager.cleanup_temp_files()

    def get_timestamped_transcript(self, audio_url, language_code):
        """
        Fetches the transcript with timestamps from AssemblyAI's API.
        """
        transcript_request = {
            "audio_url": audio_url,
            "language_code": language_code,
            "content_safety": True,
        }

        try:
            # Make the initial transcript request
            response = requests.post(
                self.transcript_endpoint,
                json=transcript_request,
                headers=self.headers,
            )

            # Check if the response is successful
            response.raise_for_status()

            # Print the full response for debugging
            # print("API Response:", response.text)

            response_json = response.json()

            # Check if 'id' exists in the response
            if "id" not in response_json:
                print("Error: No transcript ID in response")
                print("Full response:", response_json)
                if "error" in response_json:
                    print("API Error:", response_json["error"])
                raise ValueError("No transcript ID returned from API")

            transcript_id = response_json["id"]
            print(f"Transcript ID: {transcript_id}")

            while True:
                # Check transcript status
                transcript_status = requests.get(
                    f"{self.transcript_endpoint}/{transcript_id}",
                    headers=self.headers,
                )
                transcript_status.raise_for_status()

                status_json = transcript_status.json()
                print("Status:", status_json.get("status"))

                if status_json.get("status") == "error":
                    print("Transcription failed:", status_json.get("error"))
                    raise ValueError(
                        f"Transcription failed: {status_json.get('error')}"
                    )

                if status_json.get("status") == "completed":
                    break

                import time

                time.sleep(5)  # Add delay between status checks

            # Get the sentences
            transcript_result = requests.get(
                f"{self.transcript_endpoint}/{transcript_id}/sentences",
                headers=self.headers,
            )
            transcript_result.raise_for_status()

            result_json = transcript_result.json()
            if "sentences" not in result_json:
                print("Error: No sentences in response")
                print("Full result:", result_json)
                raise ValueError("No sentences returned from API")

            subtitle_data = []
            for sentence in result_json["sentences"]:
                subtitle_data.append(
                    {
                        "start": sentence["start"],
                        "end": sentence["end"],
                        "text": sentence["text"],
                    }
                )

            return subtitle_data

        except requests.exceptions.RequestException as e:
            print(f"API Request failed: {str(e)}")
            print(
                f"Response content: {e.response.text if hasattr(e, 'response') else 'No response'}"
            )
            raise

        except KeyError as e:
            print(f"Key error in response: {str(e)}")
            raise

        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            raise

    def save_transcript(self, transcript_data, output_path):

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(transcript_data, f, ensure_ascii=False, indent=2)

        print(f"Transcript saved as JSON in '{output_path}'")

    @staticmethod
    def format_timestamp(ms):
        """
        Formats timestamps in milliseconds into HH:MM:SS,mmm format.
        """
        hours, remainder = divmod(ms // 1000, 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = ms % 1000
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02},{int(milliseconds):03}"


if __name__ == "__main__":
    API_KEY = "13929b8e92cc44f18fdd295a286ab418"
    processor = SpeechToTextProcessor(API_KEY)

    if len(sys.argv) != 2:
        print("Usage: python script.py <video_file_path>")
        sys.exit(1)

    try:
        subtitle_file = processor.process_video(sys.argv[1])
        print(f"Subtitles saved to: {subtitle_file}")
    finally:
        processor.file_manager.cleanup_temp_files()
