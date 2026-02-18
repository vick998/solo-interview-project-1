# QA Inference Benchmark

Benchmark QA model inference times across documents of varying length to find the sweet spot for doc length vs inference timeout.

The suite is **split by model**: each model is run across all docs, and results are appended to the CSV after each model completes. Timeouts or failures on one model do not affect others; partial results are preserved.

## Structure

```
benchmark/
├── docs/                    # PDF documents (varying lengths)
│   ├── orwell-political-english.pdf
│   ├── mcs1825wb-vacuum-manual.pdf
│   ├── lakeland-cordless-vacuum.pdf
│   └── miele-hs23-vacuum.pdf
├── questions.json           # 5 questions per document
├── run_benchmark.py         # Benchmark script
├── results.csv             # Output (after run)
└── inference_histogram.png  # Output (after run, requires matplotlib)
```

## Usage

```bash
# Run benchmark on all models and docs (CSV overwritten)
uv run python benchmark/run_benchmark.py

# Append to existing CSV (e.g. resume after timeout)
uv run python benchmark/run_benchmark.py --append

# Run only specific model(s)
uv run python benchmark/run_benchmark.py -m tinybert -m distilbert

# Custom output paths
uv run python benchmark/run_benchmark.py -o my_results.csv --plot chart.png

# Skip histogram
uv run python benchmark/run_benchmark.py --no-plot

# Specific files only
uv run python benchmark/run_benchmark.py benchmark/docs/orwell-political-english.pdf
```

## Requirements

- `HF_TOKEN` environment variable (Hugging Face API)
- Optional: `uv add matplotlib` for histogram generation
