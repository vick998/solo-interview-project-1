"""Generate test documents for extraction validation.

Uses PyMuPDF only (no Pillow): creates a PDF with known text, then renders
the first page to PNG for OCR validation.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

OUTPUT_DIR = project_root / "test_docs"
SAMPLE_PDF = OUTPUT_DIR / "sample.pdf"
SAMPLE_PNG = OUTPUT_DIR / "sample.png"

# Known text for validation assertions
PDF_KEYWORD = "expected_keyword"
PDF_CONTENT = f"""Sample Document for Extraction Testing

This PDF contains the {PDF_KEYWORD} for validation.

Contract details:
- The contract expires on March 15, 2025.
- The vendor is Acme Corp.
"""


def generate_pdf() -> None:
    """Create a PDF with known text using PyMuPDF."""
    import fitz

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), PDF_CONTENT, fontsize=12)
    doc.save(SAMPLE_PDF)
    doc.close()
    print(f"Created {SAMPLE_PDF}")


def generate_image() -> None:
    """Create a PNG by rendering the PDF page (PyMuPDF only, no Pillow)."""
    import fitz

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(SAMPLE_PDF)
    page = doc[0]
    pix = page.get_pixmap(dpi=150)
    pix.save(SAMPLE_PNG)
    doc.close()
    print(f"Created {SAMPLE_PNG}")


def main() -> None:
    generate_pdf()
    generate_image()
    print("Done. Run: uv run python scripts/validate_extraction.py")


if __name__ == "__main__":
    main()
