## Data Compression Project – Track A (LZSS + Arithmetic)

This repository implements the **Track A** variant of the data compression project:

- **Stage 1**: LZSS encoder/decoder (dictionary-based core)
- **Stage 2**: Full compression pipeline with static arithmetic coding
- **Stage 3**: Evaluation scripts and report scaffold

### Tech stack

- **Language**: Python 3.10+
- **Dependencies**: Only the standard library plus `pytest` for tests.

### Layout

- `lzss_core.py` – Stage 1 LZSS encoder/decoder (no arithmetic coding)
- `arith_codec.py` – Stage 2 static arithmetic coder
- `compressor.py` – High-level CLI and pipeline glue
- `tests/` – Unit tests for core components

### Quickstart

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate  # on Windows
pip install -r requirements.txt
```

2. Run tests:

```bash
pytest
```

3. Compress and decompress a file with the Stage 1 LZSS-only pipeline:

```bash
python compressor.py compress --input small.txt --output small.lzss
python compressor.py decompress --input small.lzss --output small.out.txt
```

Later, once Stage 2 is complete, additional modes (e.g. arithmetic-coded) will be available via flags.

