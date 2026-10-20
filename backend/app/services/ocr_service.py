"""
Dedicated Optical Character Recognition (OCR) service powered by Tesseract and Pillow.
Renders PDF pages as high-resolution images and extracts text when native PDF text
is absent, corrupted, or insufficient (scanned/photographed documents).
"""
import io
import shutil
import logging
from typing import Optional, Union
from PIL import Image
import pytesseract
import pymupdf

from backend.app.core.config import settings
from backend.app.services.pdf_parser import clean_page_lines

logger = logging.getLogger(__name__)


class OCRError(Exception):
    """Base exception for OCR processing failures."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class TesseractNotFoundError(OCRError):
    """Raised when Tesseract OCR binary is not installed or not located in PATH."""
    def __init__(self, message: str = "Tesseract OCR binary is not installed or accessible on this system."):
        super().__init__(message, status_code=503)


class OCRExecutionError(OCRError):
    """Raised when Tesseract encounters an unrecoverable failure during character recognition."""
    pass


class OCRService:
    """
    Dedicated OCR service for rendering PDF pages and executing Tesseract OCR.
    """

    def __init__(self):
        self._tesseract_available: Optional[bool] = None
        self._configure_tesseract()

    def _configure_tesseract(self) -> None:
        """Configures Tesseract binary path if explicitly specified in settings."""
        if settings.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

    def is_available(self) -> bool:
        """
        Verifies if Tesseract binary is available and operational on the host system.
        Caches the result to avoid spawning subprocesses repeatedly.
        """
        if self._tesseract_available is not None:
            return self._tesseract_available

        # Check binary presence via shutil.which or pytesseract version query
        cmd = getattr(pytesseract.pytesseract, "tesseract_cmd", "tesseract")
        if not shutil.which(cmd) and cmd == "tesseract":
            logger.warning("Tesseract binary not found in system PATH.")
            self._tesseract_available = False
            return False

        try:
            version = pytesseract.get_tesseract_version()
            logger.info("Tesseract OCR is available. Version: %s", version)
            self._tesseract_available = True
            return True
        except Exception as e:
            logger.warning("Tesseract availability check failed: %s", str(e))
            self._tesseract_available = False
            return False

    def ocr_page(self, page: pymupdf.Page, dpi: int = settings.OCR_DPI, lang: str = settings.OCR_LANGUAGE) -> str:
        """
        Renders a single PyMuPDF page to an image and performs Tesseract OCR on it.
        """
        if not self.is_available():
            raise TesseractNotFoundError()

        try:
            # Render page to high-res pixmap (default 200 DPI for high recognition accuracy)
            pix = page.get_pixmap(dpi=dpi)
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))

            # Run Tesseract OCR
            raw_text = pytesseract.image_to_string(img, lang=lang)
            cleaned = clean_page_lines(raw_text)
            return cleaned
        except pytesseract.TesseractNotFoundError:
            self._tesseract_available = False
            raise TesseractNotFoundError()
        except Exception as e:
            logger.error("OCR execution error on page: %s", str(e))
            raise OCRExecutionError(f"Failed to execute OCR on PDF page: {str(e)}")

    def ocr_document(
        self,
        doc: pymupdf.Document,
        dpi: int = settings.OCR_DPI,
        lang: str = settings.OCR_LANGUAGE,
    ) -> str:
        """
        Renders all pages of a document and performs OCR across the entire document.
        """
        if not self.is_available():
            raise TesseractNotFoundError()

        page_texts = []
        for idx in range(doc.page_count):
            page = doc.load_page(idx)
            page_text = self.ocr_page(page, dpi=dpi, lang=lang)
            if page_text:
                page_texts.append(page_text)

        return "\n\n".join(page_texts).strip()


# Singleton instance
ocr_service = OCRService()
