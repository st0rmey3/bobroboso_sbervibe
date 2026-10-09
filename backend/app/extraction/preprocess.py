"""File → page images (+ text layer for PDFs). Detects real type by magic bytes, not by extension."""

import io
from dataclasses import dataclass

import pypdfium2 as pdfium
from PIL import Image, UnidentifiedImageError

MAX_PAGES = 4
MAX_SIDE = 1800

ALLOWED_MIME = {"application/pdf", "image/jpeg", "image/png"}


class UnreadableFile(Exception):
    """Honest refusal: the file content can't be turned into something the model can read."""


@dataclass
class Pages:
    images: list[bytes]  # JPEG bytes, one per page
    text: str  # PDF text layer if any


def sniff_mime(data: bytes) -> str | None:
    if data.startswith(b"%PDF-"):
        return "application/pdf"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    return None


def _to_jpeg(img: Image.Image) -> bytes:
    img = img.convert("RGB")
    img.thumbnail((MAX_SIDE, MAX_SIDE))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=88)
    return buf.getvalue()


def load(data: bytes, mime: str) -> Pages:
    if mime == "application/pdf":
        try:
            pdf = pdfium.PdfDocument(data)
        except pdfium.PdfiumError as e:
            raise UnreadableFile("PDF повреждён или защищён паролем") from e
        images, texts = [], []
        for i in range(min(len(pdf), MAX_PAGES)):
            page = pdf[i]
            texts.append(page.get_textpage().get_text_range())
            images.append(_to_jpeg(page.render(scale=2).to_pil()))
        if not images:
            raise UnreadableFile("PDF не содержит страниц")
        return Pages(images, "\n".join(texts).strip())
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except (UnidentifiedImageError, OSError) as e:
        raise UnreadableFile("Изображение повреждено") from e
    if min(img.size) < 200:
        raise UnreadableFile("Слишком низкое разрешение изображения")
    return Pages([_to_jpeg(img)], "")
