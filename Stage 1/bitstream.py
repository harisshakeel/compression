from __future__ import annotations

"""
Simple bit-level reader/writer built on top of bytes.

Used by both the LZSS core (Stage 1) and the arithmetic coder (Stage 2).
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class BitWriter:
    _buffer: bytearray
    _current_byte: int
    _bit_pos: int  # number of bits already filled (0-7)

    def __init__(self) -> None:
        self._buffer = bytearray()
        self._current_byte = 0
        self._bit_pos = 0

    def write_bits(self, value: int, num_bits: int) -> None:
        if num_bits < 0:
            raise ValueError("num_bits must be non-negative")
        for i in reversed(range(num_bits)):
            bit = (value >> i) & 1
            self._current_byte = (self._current_byte << 1) | bit
            self._bit_pos += 1
            if self._bit_pos == 8:
                self._buffer.append(self._current_byte & 0xFF)
                self._current_byte = 0
                self._bit_pos = 0

    def write_flag(self, bit: int) -> None:
        self.write_bits(1 if bit else 0, 1)

    def flush(self) -> bytes:
        """Flush remaining bits (pad with zeros on the right) and return bytes."""
        if self._bit_pos > 0:
            self._current_byte <<= 8 - self._bit_pos
            self._buffer.append(self._current_byte & 0xFF)
            self._current_byte = 0
            self._bit_pos = 0
        return bytes(self._buffer)


@dataclass
class BitReader:
    _data: bytes
    _byte_pos: int
    _bit_pos: int  # next bit index within current byte (0-7)

    def __init__(self, data: bytes) -> None:
        self._data = data
        self._byte_pos = 0
        self._bit_pos = 0

    def _ensure_byte_available(self) -> bool:
        return self._byte_pos < len(self._data)

    def read_bits(self, num_bits: int) -> Optional[int]:
        """Read num_bits as an integer. Returns None if not enough bits remain."""
        if num_bits < 0:
            raise ValueError("num_bits must be non-negative")
        value = 0
        for _ in range(num_bits):
            if not self._ensure_byte_available():
                return None
            current_byte = self._data[self._byte_pos]
            bit = (current_byte >> (7 - self._bit_pos)) & 1
            value = (value << 1) | bit
            self._bit_pos += 1
            if self._bit_pos == 8:
                self._bit_pos = 0
                self._byte_pos += 1
        return value

    def read_flag(self) -> Optional[int]:
        return self.read_bits(1)

