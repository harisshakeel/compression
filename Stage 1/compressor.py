from __future__ import annotations

"""
Command-line interface around the Stage 1 LZSS core.

Usage (Stage 1, no arithmetic coding yet):

  python compressor.py compress --input in.txt --output out.lzss
  python compressor.py decompress --input out.lzss --output restored.txt --length 1234

The original length is stored in a small header during compression so that the
user does not need to pass it manually during decompression.
"""

import argparse
import struct
from pathlib import Path

from lzss_core import lzss_compress, lzss_decompress


HEADER_MAGIC = b"LZSS1\0"
HEADER_FMT = "<Q"  # unsigned long long: original length


def _write_stage1_file(output_path: Path, compressed: bytes, original_length: int) -> None:
    with output_path.open("wb") as f:
        f.write(HEADER_MAGIC)
        f.write(struct.pack(HEADER_FMT, original_length))
        f.write(compressed)


def _read_stage1_file(input_path: Path) -> tuple[bytes, int]:
    data = input_path.read_bytes()
    if not data.startswith(HEADER_MAGIC):
        raise ValueError("Input file is not a valid Stage 1 LZSS file")
    header_size = len(HEADER_MAGIC) + struct.calcsize(HEADER_FMT)
    (orig_len,) = struct.unpack(HEADER_FMT, data[len(HEADER_MAGIC) : header_size])
    return data[header_size:], orig_len


def cmd_compress(args: argparse.Namespace) -> None:
    input_path = Path(args.input)
    output_path = Path(args.output)
    raw = input_path.read_bytes()
    compressed, original_length = lzss_compress(raw)
    _write_stage1_file(output_path, compressed, original_length)
    ratio = len(raw) / len(compressed) if compressed else 0.0
    print(f"Compressed {len(raw)} -> {len(compressed)} bytes (ratio {ratio:.2f})")


def cmd_decompress(args: argparse.Namespace) -> None:
    input_path = Path(args.input)
    output_path = Path(args.output)
    compressed, original_length = _read_stage1_file(input_path)
    restored = lzss_decompress(compressed, original_length)
    output_path.write_bytes(restored)
    print(f"Decompressed to {len(restored)} bytes")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Track A LZSS compressor (Stage 1).")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_comp = subparsers.add_parser("compress", help="Compress a file with LZSS (Stage 1)")
    p_comp.add_argument("--input", "-i", required=True, help="Input file path")
    p_comp.add_argument("--output", "-o", required=True, help="Output compressed file path")
    p_comp.set_defaults(func=cmd_compress)

    p_decomp = subparsers.add_parser("decompress", help="Decompress a Stage 1 LZSS file")
    p_decomp.add_argument("--input", "-i", required=True, help="Input compressed file path")
    p_decomp.add_argument("--output", "-o", required=True, help="Output restored file path")
    p_decomp.set_defaults(func=cmd_decompress)

    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

