import os
import tempfile
import cv2
import numpy as np
from moviepy.editor import VideoFileClip


def compress_video_sync(input_path: str, output_path: str):
    clip = VideoFileClip(input_path)
    try:
        duration = clip.duration or 1  # fallback
        target_size_mb = 50
        bitrate = int((target_size_mb * 1024 * 1024 * 8) / duration)
        clip.write_videofile(
            output_path,
            codec="libx264",
            bitrate=f"{bitrate}",
            audio_codec="aac",
            preset="ultrafast",
            fps=clip.fps or 24,
            threads=os.cpu_count() or 4,
        )
    finally:
        clip.close()
        del clip


def is_horizontal_sync(video_path: str) -> bool:
    cap = cv2.VideoCapture(video_path)
    try:
        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        return width >= height
    finally:
        cap.release()


def gen_blur_sync(input_path: str, target_resolution=(1080, 1920)) -> str:
    output_width, output_height = target_resolution
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        output_path = tmp.name

    clip = VideoFileClip(input_path)
    width, height = clip.size

    scale_fg = min(output_width / width, output_height / height)
    scale_bg = max(output_width / width, output_height / height)

    def process_frame(frame: np.ndarray) -> np.ndarray:
        resized = cv2.resize(frame, (int(width * scale_fg), int(height * scale_fg)))
        background = cv2.resize(frame, (int(width * scale_bg), int(height * scale_bg)))

        y = (background.shape[0] - output_height) // 2
        x = (background.shape[1] - output_width) // 2
        background_cropped = background[y:y + output_height, x:x + output_width]

        small = cv2.resize(background_cropped, (output_width // 4, output_height // 4))
        blurred = cv2.GaussianBlur(small, (25, 25), 0)
        blurred = cv2.resize(blurred, (output_width, output_height))

        x_offset = (output_width - resized.shape[1]) // 2
        y_offset = (output_height - resized.shape[0]) // 2
        blurred[y_offset:y_offset + resized.shape[0], x_offset:x_offset + resized.shape[1]] = resized
        return blurred

    try:
        processed = clip.fl_image(process_frame)
        if clip.audio:
            processed = processed.set_audio(clip.audio)

        duration = clip.duration or 1
        bitrate = int((15 * 1024 * 1024 * 8) / duration)

        processed.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            fps=clip.fps or 24,
            bitrate=f"{bitrate}",
            threads=os.cpu_count() or 4,
            verbose=False,
            logger=None
        )
        return output_path

    finally:
        clip.close()
        if "processed" in locals():
            del processed
