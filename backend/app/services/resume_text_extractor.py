"""
Unified resume text extraction pipeline with intelligent OCR fallback.
Orchestrates PyMuPDF native extraction and Tesseract OCR based on
configurable text density thresholds.
"""
from pathlib import Path
from typing import Union, Dict, Any, List
import logging
from dataclasses import dataclass, field
import pymupdf

from backend.app.core.config import settings
from backend.app.services.pdf_parser import (
    clean_page_lines,
    PDFNotFoundError,
    CorruptPDFError,
)
from backend.app.services.ocr_service import (
    ocr_service,
    TesseractNotFoundError,
    OCRExecutionError,
)
from backend.app.services.text_cleaner import clean_resume_text

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """
    Standard container for text extraction outcome.
    """
    text: str
    page_count: int
    extraction_method: str  # 'pdf_text' | 'ocr' | 'mixed'
    warnings: List[str]
    original_char_count: int = 0
    cleaned_char_count: int = 0
    transformations_applied: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "page_count": self.page_count,
            "extraction_method": self.extraction_method,
            "warnings": self.warnings,
            "original_char_count": self.original_char_count,
            "cleaned_char_count": self.cleaned_char_count,
            "transformations_applied": self.transformations_applied,
        }


class ResumeTextExtractor:
    """
    Intelligent extraction orchestrator:
    1. Attempts fast PyMuPDF native text extraction first.
    2. Measures per-page text yield against configurable thresholds.
    3. Triggers OCR only for scanned/image-only pages.
    4. Handles mixed PDFs seamlessly.
    5. Gracefully degrades if Tesseract is not installed or encounters an error.
    """

    def __init__(self, min_chars_per_page: int = settings.OCR_MIN_CHARS_PER_PAGE):
        self.min_chars_per_page = min_chars_per_page

    def extract_resume_text(self, source: Union[str, Path, bytes]) -> ExtractionResult:
        """
        Unified extraction function. Opens the PDF, checks page text density,
        and conditionally routes through PyMuPDF and/or Tesseract OCR.
        """
        doc = None
        warnings: List[str] = []

        try:
            if isinstance(source, bytes):
                if len(source) == 0:
                    return ExtractionResult(text="", page_count=0, extraction_method="pdf_text", warnings=[])
                doc = pymupdf.open(stream=source, filetype="pdf")
            else:
                path = Path(source)
                if not path.exists() or not path.is_file():
                    raise PDFNotFoundError(f"PDF document at path '{path.name}' does not exist.")
                if path.stat().st_size == 0:
                    return ExtractionResult(text="", page_count=0, extraction_method="pdf_text", warnings=[])
                doc = pymupdf.open(str(path))

            page_count = doc.page_count
            if page_count == 0:
                return ExtractionResult(text="", page_count=0, extraction_method="pdf_text", warnings=[])

            final_page_texts: List[str] = []
            page_methods: List[str] = []  # tracks 'pdf_text' or 'ocr' per page

            for page_idx in range(page_count):
                page = doc.load_page(page_idx)

                # 1. Native text extraction via PyMuPDF
                native_raw = page.get_text("text")
                native_cleaned = clean_page_lines(native_raw)
                char_count = len(native_cleaned.strip())

                # 2. Decision: Is native text sufficient?
                if char_count >= self.min_chars_per_page:
                    # Sufficient native machine-readable text found -> skip OCR
                    final_page_texts.append(native_cleaned)
                    page_methods.append("pdf_text")
                    logger.debug("Page %d: native text sufficient (%d chars) -> pdf_text", page_idx + 1, char_count)
                else:
                    # Insufficient text: image/scanned page candidate
                    logger.info(
                        "Page %d has low native text density (%d chars < %d threshold). Evaluating OCR fallback.",
                        page_idx + 1,
                        char_count,
                        self.min_chars_per_page,
                    )

                    ocr_text = ""
                    ocr_successful = False

                    if settings.OCR_ENABLED:
                        if ocr_service.is_available():
                            try:
                                ocr_text = ocr_service.ocr_page(page)
                                # If OCR extracted more meaningful text than native
                                if len(ocr_text.strip()) > char_count:
                                    final_page_texts.append(ocr_text)
                                    page_methods.append("ocr")
                                    ocr_successful = True
                                    logger.info("Page %d: OCR succeeded (%d chars) -> ocr", page_idx + 1, len(ocr_text))
                                else:
                                    logger.info("Page %d: OCR produced no extra text. Retaining native output.", page_idx + 1)
                            except TesseractNotFoundError:
                                warn_msg = "Tesseract OCR binary not found. Scanned page OCR fallback skipped."
                                if warn_msg not in warnings:
                                    warnings.append(warn_msg)
                            except OCRExecutionError as ocr_err:
                                warn_msg = f"OCR execution failed on page {page_idx + 1}: {str(ocr_err)}"
                                logger.warning(warn_msg)
                                warnings.append(warn_msg)
                            except Exception as unexpected_ocr_err:
                                warn_msg = f"Unexpected OCR error on page {page_idx + 1}: {str(unexpected_ocr_err)}"
                                logger.error(warn_msg)
                                warnings.append(warn_msg)
                        else:
                            warn_msg = "Tesseract OCR is not installed or available on this system."
                            if warn_msg not in warnings:
                                warnings.append(warn_msg)

                    if not ocr_successful:
                        # Fallback to whatever native text exists (even if empty or minimal)
                        final_page_texts.append(native_cleaned)
                        page_methods.append("pdf_text")

            # Determine aggregate extraction method
            has_pdf_text = "pdf_text" in page_methods and any(
                len(t.strip()) >= self.min_chars_per_page
                for t, m in zip(final_page_texts, page_methods)
                if m == "pdf_text"
            )
            has_ocr = "ocr" in page_methods

            if has_ocr and has_pdf_text:
                overall_method = "mixed"
            elif has_ocr:
                overall_method = "ocr"
            else:
                overall_method = "pdf_text"

            combined_text = "\n\n".join(t for t in final_page_texts if t.strip()).strip()

            # Phase 5: Deterministic resume text preprocessing
            cleaned_outcome = clean_resume_text(combined_text)

            return ExtractionResult(
                text=cleaned_outcome.cleaned_text,
                page_count=page_count,
                extraction_method=overall_method,
                warnings=warnings,
                original_char_count=cleaned_outcome.original_char_count,
                cleaned_char_count=cleaned_outcome.cleaned_char_count,
                transformations_applied=cleaned_outcome.transformations_applied,
            )

        except (PDFNotFoundError, CorruptPDFError):
            raise
        except pymupdf.FileDataError as e:
            raise CorruptPDFError(f"Malformed or corrupt PDF document: {str(e)}")
        except pymupdf.EmptyFileError:
            return ExtractionResult(text="", page_count=0, extraction_method="pdf_text", warnings=[])
        except Exception as e:
            err_msg = str(e).lower()
            if "format not recognized" in err_msg or "cannot open" in err_msg or "syntax error" in err_msg:
                raise CorruptPDFError(f"Unable to read PDF file format: {str(e)}")
            logger.error("Unexpected error during resume text extraction: %s", str(e))
            raise CorruptPDFError(f"Failed to extract text from PDF: {str(e)}")

        finally:
            if doc is not None:
                try:
                    doc.close()
                except Exception:
                    pass


# Singleton instance
resume_text_extractor = ResumeTextExtractor()


def extract_resume_text(source: Union[str, Path, bytes]) -> ExtractionResult:
    """
    Convenience function exposing the unified text extraction pipeline.
    """
    return resume_text_extractor.extract_resume_text(source)
