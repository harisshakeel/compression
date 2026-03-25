from __future__ import annotations

import os

from lzss_core import lzss_compress, lzss_decompress


def roundtrip(data: bytes) -> None:
    compressed, length = lzss_compress(data)
    restored = lzss_decompress(compressed, length)
    assert restored == data


def test_empty():
    roundtrip(b"")


def test_small_literal_only():
    roundtrip(b"abc")
    roundtrip(b"hello world")


def test_repetitive_patterns():
    roundtrip(b"aaaaaa")
    roundtrip(b"abababababababab")


def test_long_randomish():
    data = os.urandom(2048)
    roundtrip(data)

