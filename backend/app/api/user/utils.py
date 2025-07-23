import io

from fastapi import UploadFile
from PIL import Image

from app.core.logging import get_logger

logger = get_logger()


def process_image(file: UploadFile) -> bytes:
    logger.info("Uploading pfp")
    img = Image.open(file.file).convert("RGB")
    width, height = img.size
    min_dim = min(width, height)
    left = (width - min_dim) // 2
    top = (height - min_dim) // 2
    right = left + min_dim
    bottom = top + min_dim
    img = img.crop((left, top, right, bottom))
    img = img.resize((512, 512))

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer
