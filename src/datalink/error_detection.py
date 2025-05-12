import numpy as np
from typing import List, Tuple

class CRC:
    def __init__(self, polynomial: int = 0x1021):
        self.polynomial = polynomial

    def compute(self, data: bytes) -> int:
        crc = 0xFFFF
        for byte in data:
            crc ^= byte << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ self.polynomial
                else:
                    crc <<= 1
                crc &= 0xFFFF
        return crc

    def verify(self, data: bytes, received_crc: int) -> bool:
        return self.compute(data) == received_crc

class HammingCode:
    @staticmethod
    def encode(data_bits: List[int]) -> List[int]:
        n = len(data_bits)
        r = 0
        while (2**r) < (n + r + 1):
            r += 1

        encoded = [0] * (n + r)
        j = 0
        for i in range(1, n + r + 1):
            if not (i & (i - 1)) == i:
                encoded[i - 1] = data_bits[j]
                j += 1

        # Calculate parity bits
        for i in range(r):
            parity_pos = 2**i
            parity = 0
            for j in range(1, n + r + 1):
                if j & parity_pos:
                    parity ^= encoded[j - 1]
            encoded[parity_pos - 1] = parity

        return encoded

    @staticmethod
    def decode(encoded: List[int]) -> Tuple[List[int], int]:
        n = len(encoded)
        r = 0
        while (2**r) < n:
            r += 1

        error_pos = 0
        for i in range(r):
            parity_pos = 2**i
            parity = 0
            for j in range(1, n + 1):
                if j & parity_pos:
                    parity ^= encoded[j - 1]
            if parity != 0:
                error_pos += parity_pos

        if error_pos > 0 and error_pos <= n:
            encoded[error_pos - 1] ^= 1

        data_bits = []
        for i in range(1, n + 1):
            if not (i & (i - 1)) == i:
                data_bits.append(encoded[i - 1])

        return data_bits, error_pos

class Checksum:
    @staticmethod
    def compute(data: bytes) -> int:
        if len(data) % 2 != 0:
            data += b'\x00'

        checksum = 0
        for i in range(0, len(data), 2):
            word = (data[i] << 8) + data[i + 1]
            checksum += word
            while checksum > 0xFFFF:
                checksum = (checksum & 0xFFFF) + (checksum >> 16)

        return ~checksum & 0xFFFF

    @staticmethod
    def verify(data: bytes, received_checksum: int) -> bool:
        return Checksum.compute(data) == received_checksum