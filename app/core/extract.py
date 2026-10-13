"""Local document extraction for LedgerLens.
Processes PDFs and image files (PNG, JPG, TIFF) strictly on-device.
Zero cloud OCR endpoints.
"""

from __future__ import annotations
import base64
import io
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    Image = None
    HAS_PIL = False

try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    PdfReader = None
    HAS_PYPDF = False

from app.utils.logging import logger
from app.utils.crypto import compute_file_sha256

def extract_text_from_pdf(pdf_path: Union[str, Path]) -> str:
    """Extract embedded text from PDF pages locally using PyPDF."""
    if not HAS_PYPDF or not PdfReader:
        return "[PDF extracted in text fallback mode]"
    text_chunks = []
    try:
        reader = PdfReader(str(pdf_path))
        for idx, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            text_chunks.append(page_text.strip())
        return "\n--- PAGE BREAK ---\n".join(text_chunks)
    except Exception as e:
        logger.warning("PyPDF extraction failed for %s: %s", pdf_path, e)
        return ""

def load_image_and_encode_base64(image_path: Union[str, Path], max_size: int = 1600) -> Tuple[str, str]:
    """Load image, downscale if needed to fit VLM memory floor, and return base64 string.
    Returns: (base64_string, mime_type)
    """
    path = Path(image_path)
    suffix = path.suffix.lower()
    mime = "image/jpeg" if suffix in (".jpg", ".jpeg") else "image/png"

    if not HAS_PIL or not Image:
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        return encoded, mime

    with Image.open(path) as img:
        img = img.convert("RGB")
        width, height = img.size
        if max(width, height) > max_size:
            scaling = max_size / float(max(width, height))
            new_size = (int(width * scaling), int(height * scaling))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return encoded, mime

def extract_document(file_path: Union[str, Path]) -> Dict[str, Union[str, Path]]:
    """Primary extraction entrypoint: calculates sha256 and extracts local text/image payload."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    file_hash = compute_file_sha256(str(path))
    suffix = path.suffix.lower()

    extracted_text = ""
    image_base64 = ""

    if suffix == ".pdf":
        extracted_text = extract_text_from_pdf(path)
        # If PDF has minimal embedded text (e.g. scanned), note that VLM pass or OCR is needed
        if len(extracted_text.strip()) < 20:
            extracted_text = f"[Scanned PDF: {path.name}. Text layer minimal.]"
    elif suffix in (".png", ".jpg", ".jpeg", ".webp", ".bmp"):
        image_base64, _ = load_image_and_encode_base64(path)
        extracted_text = f"[Image Document: {path.name}]"
    elif suffix in (".txt", ".csv"):
        extracted_text = path.read_text(encoding="utf-8", errors="replace")
    else:
        raise ValueError(f"Unsupported file format: {suffix}")

    return {
        "file_path": str(path),
        "filename": path.name,
        "file_hash": file_hash,
        "suffix": suffix,
        "extracted_text": extracted_text,
        "image_base64": image_base64
    }
