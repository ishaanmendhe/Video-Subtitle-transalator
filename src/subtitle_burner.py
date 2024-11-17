from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import json
from typing import Dict, List
import threading
import queue


class SubtitleBurner:
    def __init__(self, video_path: str, subtitle_path: str):
        self.video_path = video_path
        self.subtitle_path = subtitle_path
        self.subtitle_queue = queue.Queue()
        self.current_subtitle = None

    def load_subtitles(self):
        with open(self.subtitle_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def create_subtitle_clip(self, text: str, start: float, duration: float):
        txt_clip = TextClip(
            text,
            fontsize=24,
            color="white",
            stroke_color="black",
            stroke_width=1,
            size=(self.video.w, None),
            method="caption",
        )
        return (
            txt_clip.set_position(("center", "bottom"))
            .set_start(start)
            .set_duration(duration)
        )

    def process_video(self, output_path: str):
        self.video = VideoFileClip(self.video_path)
        subtitles = self.load_subtitles()

        # Create subtitle clips
        subtitle_clips = []
        for sub in subtitles:
            start = sub["start"] / 1000  # Convert to seconds
            duration = (sub["end"] - sub["start"]) / 1000
            subtitle_clips.append(
                self.create_subtitle_clip(sub["text"], start, duration)
            )

        # Combine video with subtitles
        final_video = CompositeVideoClip([self.video] + subtitle_clips)

        # Write output video
        final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")

        self.video.close()
