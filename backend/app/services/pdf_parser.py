"""
Dedicated PDF text extraction service powered by PyMuPDF (fitz).
Provides safe document opening, robust multi-page extraction,
useful line-break preservation, duplicate suppression, and graceful corruption handling.
"""
from pathlib import Path
from typing import Union, Tuple
import logging
import pymupdf

logger = logging.getLogger(__name__)


class PDFParserError(Exception):
    """Base exception for PDF parsing failures."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class CorruptPDFError(PDFParserError):
    """Raised when PDF data cannot be parsed or is corrupted."""
    pass


class PDFNotFoundError(PDFParserError):
    """Raised when the requested PDF document does not exist."""
    def __init__(self, message: str = "PDF document not found in temporary storage."):
        super().__init__(message, status_code=404)


def clean_page_lines(raw_text: str) -> str:
    """
    Cleans extracted raw page text:
    - Strips non-printable null bytes
    - Normalizes non-breaking spaces (\u00a0 -> space)
    - Trims trailing whitespace from individual lines
    - Collapses runs of more than 2 consecutive blank lines into a single paragraph separator
    - Preserves logical bullet points, indentations, and list structures
    """
    if not raw_text:
        return ""

    # Normalize carriage returns and non-breaking spaces
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ")
    raw_lines = text.split("\n")

    cleaned_lines = []
    consecutive_empty = 0

    for raw_line in raw_lines:
        line = raw_line.replace("\x00", "").rstrip()
        if not line.strip():
            consecutive_empty += 1
            if consecutive_empty <= 1 and cleaned_lines:
                cleaned_lines.append("")
        else:
            consecutive_empty = 0
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


class PDFParserService:
    """
    Service responsible for loading and extracting clean text from PDF documents using PyMuPDF.
    """

    @staticmethod
    def extract_text(source: Union[str, Path, bytes]) -> Tuple[str, int]:
        """
        Safely opens a PDF document from a filepath or in-memory byte buffer,
        iterates through its pages, extracts textual content while preserving
        meaningful line breaks, and returns (extracted_text, page_count).

        Raises:
            PDFNotFoundError: If a provided filepath does not exist.
            CorruptPDFError: If the document is malformed or unreadable.
        """
        doc = None
        try:
            if isinstance(source, bytes):
                if len(source) == 0:
                    return "", 0
                doc = pymupdf.open(stream=source, filetype="pdf")
            else:
                path = Path(source)
                if not path.exists() or not path.is_file():
                    raise PDFNotFoundError(f"PDF document at path '{path.name}' does not exist.")
                if path.stat().st_size == 0:
                    return "", 0
                doc = pymupdf.open(str(path))

            # Inspect page count
            page_count = doc.page_count
            if page_count == 0:
                return "", 0

            # Security limit: Prevent PDF decompression bomb / CPU exhaustion
            MAX_ALLOWED_PAGES = 50
            if page_count > MAX_ALLOWED_PAGES:
                raise CorruptPDFError(
                    f"PDF document exceeds the safety limit of {MAX_ALLOWED_PAGES} pages ({page_count} pages detected)."
                )

            extracted_pages = []

            for page_index in range(page_count):
                try:
                    page = doc.load_page(page_index)
                    # Use 'text' mode which extracts in natural reading order
                    raw_page_text = page.get_text("text")
                    cleaned_page = clean_page_lines(raw_page_text)
                    if cleaned_page:
                        extracted_pages.append(cleaned_page)
                except Exception as page_err:
                    logger.warning("Error extracting text from page %d: %s", page_index, str(page_err))
                    continue

            # Join multi-page text with double newlines
            full_text = "\n\n".join(extracted_pages).strip()
            return full_text, page_count

        except (PDFNotFoundError, CorruptPDFError):
            raise
        except pymupdf.FileDataError as e:
            logger.error("PyMuPDF FileDataError: %s", str(e))
            raise CorruptPDFError(f"Malformed or corrupt PDF document: {str(e)}")
        except pymupdf.EmptyFileError:
            return "", 0
        except Exception as e:
            # Handle PyMuPDF runtime errors on invalid PDF structures
            err_msg = str(e).lower()
            if "format not recognized" in err_msg or "cannot open" in err_msg or "syntax error" in err_msg:
                raise CorruptPDFError(f"Unable to read PDF file format: {str(e)}")
            logger.error("Unexpected error during PDF extraction: %s", str(e))
            raise CorruptPDFError(f"Failed to extract text from PDF: {str(e)}")

        finally:
            if doc is not None:
                try:
                    doc.close()
                except Exception:
                    pass


# Singleton instance
pdf_parser_service = PDFParserService()
