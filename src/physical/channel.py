import random
import numpy as np
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class SignalParams:
    bandwidth: float
    signal_power: float
    noise_power: float
    attenuation: float

    @property
    def snr_db(self) -> float:
        return 10 * np.log10(self.signal_power / self.noise_power)

    @property
    def shannon_capacity(self) -> float:
        return self.bandwidth * np.log2(1 + self.signal_power / self.noise_power)

class PhysicalChannel:
    def __init__(self, error_rate: float = 0.001, latency_ms: float = 10.0):
        self.error_rate = error_rate
        self.latency_ms = latency_ms
        self.transmitted_bits = 0
        self.error_bits = 0

    def transmit(self, bits: List[int]) -> Tuple[List[int], float]:
        transmitted = []
        errors = 0

        for bit in bits:
            if random.random() < self.error_rate:
                transmitted.append(1 - bit)
                errors += 1
                self.error_bits += 1
            else:
                transmitted.append(bit)
            self.transmitted_bits += 1

        return transmitted, self.latency_ms

    def get_ber(self) -> float:
        if self.transmitted_bits == 0:
            return 0
        return self.error_bits / self.transmitted_bits

class ManchesterEncoder:
    @staticmethod
    def encode(bits: List[int]) -> List[int]:
        encoded = []
        for bit in bits:
            if bit == 0:
                encoded.extend([0, 1])
            else:
                encoded.extend([1, 0])
        return encoded

    @staticmethod
    def decode(encoded: List[int]) -> List[int]:
        if len(encoded) % 2 != 0:
            raise ValueError("Invalid Manchester encoded data")

        decoded = []
        for i in range(0, len(encoded), 2):
            if encoded[i] == 0 and encoded[i+1] == 1:
                decoded.append(0)
            elif encoded[i] == 1 and encoded[i+1] == 0:
                decoded.append(1)
            else:
                raise ValueError(f"Invalid Manchester pattern at position {i}")

        return decoded

class NRZIEncoder:
    def __init__(self):
        self.last_level = 0

    def encode(self, bits: List[int]) -> List[int]:
        encoded = []
        level = self.last_level

        for bit in bits:
            if bit == 1:
                level = 1 - level
            encoded.append(level)

        self.last_level = level
        return encoded

    def decode(self, levels: List[int]) -> List[int]:
        if not levels:
            return []

        decoded = []
        for i in range(len(levels)):
            if i == 0:
                decoded.append(1 if levels[i] != self.last_level else 0)
            else:
                decoded.append(1 if levels[i] != levels[i-1] else 0)

        return decoded