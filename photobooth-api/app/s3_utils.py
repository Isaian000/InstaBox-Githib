import io
import textwrap
import uuid

import boto3
from PIL import Image, ImageDraw, ImageFont

from .config import AWS_REGION, S3_BUCKET_NAME

s3_client = boto3.client("s3", region_name=AWS_REGION)

THUMB_SIZE = (128, 128)

# Polaroid: marco blanco alrededor de la foto + espacio abajo para el mensaje
POLAROID_MARGIN = 16
POLAROID_BOTTOM = 70
POLAROID_PHOTO_SIZE = (300, 300)


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def resize_thumbnail(image_bytes: bytes) -> bytes:
    """Reduce la foto original a 128x128 (para pictures/)."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img.thumbnail(THUMB_SIZE)
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=90)
    return out.getvalue()


def build_polaroid(image_bytes: bytes, message: str) -> bytes:
    """Compone la foto en formato Polaroid: marco blanco + mensaje escrito abajo."""
    photo = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    photo = photo.resize(POLAROID_PHOTO_SIZE)

    canvas_w = POLAROID_PHOTO_SIZE[0] + 2 * POLAROID_MARGIN
    canvas_h = POLAROID_PHOTO_SIZE[1] + POLAROID_MARGIN + POLAROID_BOTTOM
    canvas = Image.new("RGB", (canvas_w, canvas_h), "white")
    canvas.paste(photo, (POLAROID_MARGIN, POLAROID_MARGIN))

    draw = ImageDraw.Draw(canvas)
    font = _load_font(16)
    wrapped = textwrap.wrap(message, width=28)[:3]  # máximo 3 líneas
    text_y = POLAROID_PHOTO_SIZE[1] + POLAROID_MARGIN + 8
    for line in wrapped:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        x = (canvas_w - line_w) / 2
        draw.text((x, text_y), line, fill="black", font=font)
        text_y += (bbox[3] - bbox[1]) + 6

    out = io.BytesIO()
    canvas.save(out, format="JPEG", quality=92)
    return out.getvalue()


def upload_bytes(data: bytes, key: str) -> str:
    s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=key, Body=data, ContentType="image/jpeg")
    return key


def upload_original_and_polaroid(event_id: str, image_bytes: bytes, message: str):
    file_id = str(uuid.uuid4())

    thumb_bytes = resize_thumbnail(image_bytes)
    original_key = f"pictures/{event_id}/{file_id}.jpg"
    upload_bytes(thumb_bytes, original_key)

    polaroid_bytes = build_polaroid(image_bytes, message)
    polaroid_key = f"polaroids/{event_id}/{file_id}.jpg"
    upload_bytes(polaroid_bytes, polaroid_key)

    return original_key, polaroid_key


def download_bytes(key: str) -> bytes:
    obj = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=key)
    return obj["Body"].read()


def delete_object(key: str) -> None:
    s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=key)
