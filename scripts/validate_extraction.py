"""Validate document extraction (PDF and image)."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.extraction.exceptions import ExtractionError, UnsupportedFileTypeError
from app.extraction.extractor import extract_text


def main() -> int:
    """Run extraction validation. Returns 0 on success, 1 on failure."""
    test_docs = project_root / "test_docs"
    sample_pdf = test_docs / "sample.pdf"
    sample_png = test_docs / "sample.png"

    errors = []

    # PDF extraction
    if not sample_pdf.exists():
        errors.append(f"Missing {sample_pdf}. Run: uv run python scripts/generate_test_docs.py")
    else:
        try:
            pdf_text = extract_text(str(sample_pdf))
            if not pdf_text or len(pdf_text) == 0:
                errors.append("PDF extraction returned empty text")
            elif "expected_keyword" not in pdf_text.lower():
                errors.append(f"PDF missing expected keyword. Got: {pdf_text[:100]}...")
            else:
                print("OK: PDF extraction")
        except Exception as e:
            errors.append(f"PDF extraction failed: {e}")

    # Image extraction
    if not sample_png.exists():
        errors.append(f"Missing {sample_png}. Run: uv run python scripts/generate_test_docs.py")
    else:
        try:
            img_text = extract_text(str(sample_png))
            if not img_text or len(img_text) == 0:
                errors.append("Image extraction returned empty text")
            else:
                print("OK: Image extraction")
        except Exception as e:
            errors.append(f"Image extraction failed: {e}")

    # Unsupported file type
    try:
        extract_text("test_docs/foo.txt")
        errors.append("Expected UnsupportedFileTypeError for .txt")
    except UnsupportedFileTypeError:
        print("OK: Unsupported file type raises UnsupportedFileTypeError")
    except Exception as e:
        errors.append(f"Wrong exception for unsupported type: {e}")

    # Nonexistent file
    try:
        extract_text("nonexistent.pdf")
        errors.append("Expected ExtractionError for nonexistent file")
    except ExtractionError:
        print("OK: Nonexistent file raises ExtractionError")
    except Exception as e:
        errors.append(f"Wrong exception for nonexistent file: {e}")

    if errors:
        for err in errors:
            print(f"FAIL: {err}", file=sys.stderr)
        return 1
    print("All validations passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
