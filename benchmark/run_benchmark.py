#!/usr/bin/env python3
"""Benchmark QA model inference times across documents of varying length.

Uses docs/ and questions.json in this directory by default.
Run: uv run python benchmark/run_benchmark.py

Suite is split by model: each model is run across all docs, and results are
appended to CSV after each model completes. Timeouts on one model do not
affect others; partial results are preserved.
"""

import argparse
import csv
import json
import sys
import time
from pathlib import Path

# Add project root to path
BENCHMARK_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BENCHMARK_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import QA_MODELS
from app.extraction.extractor import extract_text
from app.qa.pipeline import answer_with_history

DOCS_DIR = BENCHMARK_DIR / "docs"
QUESTIONS_FILE = BENCHMARK_DIR / "questions.json"
CSV_HEADER = ["file", "char_count", "model_id", "avg_inference_s", "min_s", "max_s", "num_questions"]


def load_questions() -> dict[str, list[str]]:
    """Load questions per document from questions.json."""
    if not QUESTIONS_FILE.exists():
        return {}
    return json.loads(QUESTIONS_FILE.read_text(encoding="utf-8"))


def load_text(file_path: Path) -> tuple[str, int]:
    """Load text from file. Returns (text, char_count). Supports .txt, .pdf, .png, .jpg."""
    path = file_path.resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".txt":
        text = path.read_text(encoding="utf-8", errors="replace").strip()
    elif suffix in {".pdf", ".png", ".jpg", ".jpeg"}:
        text = extract_text(str(path)).strip()
    else:
        raise ValueError(
            f"Unsupported: {suffix}. Use .txt, .pdf, .png, .jpg"
        )

    return text, len(text)


def run_model_for_docs(
    model: dict,
    file_paths: list[Path],
    questions_map: dict[str, list[str]],
    num_questions: int,
) -> list[dict]:
    """Run one model across all docs. Returns list of result dicts for that model."""
    model_id = model["id"]
    results = []

    for fp in file_paths:
        try:
            text, char_count = load_text(fp)
        except Exception as e:
            print(f"  SKIP {fp.name}: {e}", file=sys.stderr)
            continue

        if not text:
            print(f"  SKIP {fp.name}: empty text", file=sys.stderr)
            continue

        questions = questions_map.get(fp.name)
        if not questions:
            print(f"  SKIP {fp.name}: no questions in questions.json", file=sys.stderr)
            continue
        questions = questions[:num_questions]

        print(f"  {fp.name} ({char_count:,} chars):", end=" ", flush=True)
        times = []

        for i, q in enumerate(questions):
            t0 = time.perf_counter()
            try:
                answer_with_history(q, text, [], model_id=model_id)
                elapsed = time.perf_counter() - t0
                times.append(elapsed)
            except Exception as e:
                times.append(-1.0)
                err_msg = str(e).lower()
                if "timeout" in err_msg or "timed out" in err_msg or "504" in err_msg or "503" in err_msg:
                    print(f"Q{i+1} TIMEOUT", end=" ", flush=True)
                else:
                    print(f"Q{i+1} ERROR", end=" ", flush=True)

        print(" ".join(f"{t:.2f}s" if t >= 0 else "FAIL" for t in times))

        valid_times = [t for t in times if t >= 0]
        avg_time = sum(valid_times) / len(valid_times) if valid_times else float("nan")

        results.append({
            "file": fp.name,
            "char_count": char_count,
            "model_id": model_id,
            "model_name": model["name"],
            "times": times,
            "avg_inference_s": avg_time,
            "min_s": min(valid_times) if valid_times else None,
            "max_s": max(valid_times) if valid_times else None,
        })

    return results


def append_csv_rows(rows: list[dict], out_path: Path, write_header: bool) -> None:
    """Append result rows to CSV. Write header only if write_header is True."""
    with out_path.open("a" if out_path.exists() else "w", newline="") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(CSV_HEADER)
        for r in rows:
            avg = r["avg_inference_s"]
            w.writerow([
                r["file"],
                r["char_count"],
                r["model_id"],
                f"{avg:.3f}" if avg == avg else "",
                r["min_s"] if r["min_s"] is not None else "",
                r["max_s"] if r["max_s"] is not None else "",
                len(r["times"]),
            ])


def plot_histogram(results: list[dict], out_path: Path, timeout_s: float = 120) -> None:
    """Plot avg inference time vs doc length per model."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("Install matplotlib for histogram: uv add matplotlib", file=sys.stderr)
        return

    by_model: dict[str, list[tuple[int, float]]] = {}
    for r in results:
        mid = r["model_id"]
        if mid not in by_model:
            by_model[mid] = []
        if r["avg_inference_s"] == r["avg_inference_s"]:
            by_model[mid].append((r["char_count"], r["avg_inference_s"]))

    fig, ax = plt.subplots(figsize=(10, 6))

    for model_id, points in by_model.items():
        if not points:
            continue
        chars, times = zip(*sorted(points))
        ax.plot(chars, times, marker="o", label=model_id, linewidth=2)

    ax.axhline(y=timeout_s, color="red", linestyle="--", label=f"Timeout ({timeout_s}s)")
    ax.set_xlabel("Document length (chars)")
    ax.set_ylabel("Average inference time (s)")
    ax.set_title("QA model inference time vs document length")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close()
    print(f"Saved histogram to {out_path}")


def load_existing_results(csv_path: Path) -> list[dict]:
    """Load existing results from CSV for plotting."""
    if not csv_path.exists():
        return []
    results = []
    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            avg = row.get("avg_inference_s", "").strip()
            min_s = row.get("min_s", "").strip()
            max_s = row.get("max_s", "").strip()
            results.append({
                "file": row["file"],
                "char_count": int(row["char_count"]),
                "model_id": row["model_id"],
                "avg_inference_s": float(avg) if avg and avg != "nan" else float("nan"),
                "min_s": float(min_s) if min_s else None,
                "max_s": float(max_s) if max_s else None,
                "times": [],
            })
    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Benchmark QA inference times across benchmark documents. "
        "Suite is split by model; CSV is appended after each model."
    )
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="Optional: specific files to benchmark (default: all docs in benchmark/docs/)",
    )
    parser.add_argument(
        "-m", "--model",
        action="append",
        dest="models",
        metavar="MODEL_ID",
        help="Run only these model(s). Can be repeated. Default: all models.",
    )
    parser.add_argument(
        "-n", "--num-questions",
        type=int,
        default=5,
        help="Number of questions per model per file (default: 5)",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=BENCHMARK_DIR / "results.csv",
        help="Output CSV path (default: benchmark/results.csv)",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to existing CSV instead of overwriting",
    )
    parser.add_argument(
        "--plot",
        type=Path,
        metavar="PATH",
        default=BENCHMARK_DIR / "inference_histogram.png",
        help="Save histogram to PATH (default: benchmark/inference_histogram.png)",
    )
    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Skip histogram generation",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120,
        help="Timeout (s) for reference line on plot (default: 120)",
    )
    args = parser.parse_args()

    questions_map = load_questions()
    if not questions_map:
        print("No questions found in questions.json", file=sys.stderr)
        return 1

    if args.files:
        file_paths = [Path(f).resolve() for f in args.files]
    else:
        file_paths = sorted(DOCS_DIR.glob("*.pdf"))
        if not file_paths:
            print(f"No PDFs found in {DOCS_DIR}", file=sys.stderr)
            return 1

    models_to_run = [
        m for m in QA_MODELS
        if not args.models or m["id"] in args.models
    ]
    if not models_to_run:
        print("No matching models. Available:", [m["id"] for m in QA_MODELS], file=sys.stderr)
        return 1

    # Prepare CSV: overwrite unless --append
    csv_path = args.output.resolve()
    if not args.append and csv_path.exists():
        csv_path.write_text("")  # truncate

    all_results: list[dict] = []
    write_header = not (args.append and csv_path.exists())

    for model in models_to_run:
        model_id = model["id"]
        print(f"\n--- {model_id} ---")
        try:
            rows = run_model_for_docs(model, file_paths, questions_map, args.num_questions)
        except KeyboardInterrupt:
            print("\nInterrupted. Partial results written.", file=sys.stderr)
            break
        except Exception as e:
            print(f"  {model_id}: FAILED {e}", file=sys.stderr)
            continue

        if rows:
            append_csv_rows(rows, csv_path, write_header)
            write_header = False
            all_results.extend(rows)
            print(f"  Wrote {len(rows)} rows to {csv_path}")

    if not all_results:
        print("No results.", file=sys.stderr)
        return 1

    # Plot from full CSV (includes pre-existing rows when --append)
    if not args.no_plot and args.plot and csv_path.exists():
        plot_results = load_existing_results(csv_path)
        if plot_results:
            plot_histogram(plot_results, args.plot, args.timeout)

    return 0


if __name__ == "__main__":
    sys.exit(main())
