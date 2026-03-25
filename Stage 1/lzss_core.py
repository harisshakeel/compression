from __future__ import annotations

"""
Stage 1: LZSS core encoder/decoder for Track A.

Format (bit-level, simple and self-contained):

- A sequence of tokens:
  - Literal token:
      flag bit = 0
      8 bits: literal byte
  - Match token:
      flag bit = 1
      4 bits: match length  (stored as length - 3, so actual length = stored + 3, range 3..18)
      12 bits: distance     (1..4096, distance back from current position)

There is no explicit EOF marker; the caller is responsible for knowing the
original input size and using it during decoding.
"""

from dataclasses import dataclass
from typing import Tuple

from bitstream import BitWriter, BitReader


WINDOW_SIZE = 8 * 1024  # 8KB, as required
MIN_MATCH_LEN = 3
MAX_MATCH_LEN = MIN_MATCH_LEN + (1 << 4) - 1  # 3 + 15 = 18
MAX_DISTANCE = 1 << 12  # encoded on 12 bits


@dataclass
class Match:
    length: int
    distance: int


def _find_longest_match(data: bytes, pos: int) -> Match:
    """Find the longest match up to MAX_MATCH_LEN within WINDOW_SIZE behind pos."""
    end = min(len(data), pos + MAX_MATCH_LEN)
    best_len = 0
    best_dist = 0

    window_start = max(0, pos - WINDOW_SIZE)

    for candidate_start in range(window_start, pos):
        max_len_here = min(end - pos, pos - candidate_start)
        length = 0
        while length < max_len_here and data[candidate_start + length] == data[pos + length]:
            length += 1
        if length >= MIN_MATCH_LEN and length > best_len:
            best_len = length
            best_dist = pos - candidate_start
            if best_len == MAX_MATCH_LEN:
                break

    # Enforce maximum distance constraint
    if best_dist > MAX_DISTANCE:
        best_len = 0
        best_dist = 0

    return Match(best_len, best_dist)


def lzss_compress(raw: bytes) -> Tuple[bytes, int]:
    """
    Compress raw bytes using LZSS and return (compressed_bytes, original_length).

    original_length is needed by the decoder to know when to stop.
    """
    writer = BitWriter()
    i = 0
    n = len(raw)

    while i < n:
        match = _find_longest_match(raw, i)
        if match.length >= MIN_MATCH_LEN:
            # Output match token
            writer.write_flag(1)
            stored_len = match.length - MIN_MATCH_LEN
            writer.write_bits(stored_len, 4)
            writer.write_bits(match.distance, 12)
            i += match.length
        else:
            # Output literal token
            writer.write_flag(0)
            writer.write_bits(raw[i], 8)
            i += 1

    return writer.flush(), n


def lzss_decompress(compressed: bytes, original_length: int) -> bytes:
    """
    Decompress bytes produced by lzss_compress, using original_length as a stop condition.
    """
    reader = BitReader(compressed)
    out = bytearray()

    while len(out) < original_length:
        flag = reader.read_flag()
        if flag is None:
            # Ran out of bits unexpectedly
            break
        if flag == 0:
            literal = reader.read_bits(8)
            if literal is None:
                raise ValueError("Unexpected end of stream while reading literal")
            out.append(literal)
        else:
            stored_len = reader.read_bits(4)
            distance = reader.read_bits(12)
            if stored_len is None or distance is None:
                raise ValueError("Unexpected end of stream while reading match")
            length = stored_len + MIN_MATCH_LEN
            if distance <= 0 or distance > len(out):
                raise ValueError(f"Invalid match distance {distance}")
            start = len(out) - distance
            for _ in range(length):
                if len(out) >= original_length:
                    break
                out.append(out[start])
                start += 1

    if len(out) != original_length:
        raise ValueError(
            f"Decompression size mismatch: expected {original_length}, got {len(out)}"
        )

    return bytes(out)

