import random
import time
from typing import List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

class MACState(Enum):
    IDLE = 1
    TRANSMITTING = 2
    COLLISION = 3
    BACKOFF = 4

@dataclass
class MACStats:
    transmissions: int = 0
    collisions: int = 0
    successful_transmissions: int = 0
    backoff_time: float = 0.0

class CSMACD:
    def __init__(self, station_id: str, collision_detect_fn: Callable):
        self.station_id = station_id
        self.collision_detect_fn = collision_detect_fn
        self.state = MACState.IDLE
        self.stats = MACStats()
        self.max_retries = 16
        self.slot_time = 0.001

    def transmit(self, data: bytes) -> bool:
        retries = 0
        while retries < self.max_retries:
            if self._sense_channel():
                time.sleep(random.uniform(0, self.slot_time))
                continue

            self.state = MACState.TRANSMITTING
            self.stats.transmissions += 1

            if self._start_transmission(data):
                self.state = MACState.IDLE
                self.stats.successful_transmissions += 1
                return True

            self.state = MACState.COLLISION
            self.stats.collisions += 1
            self._jam_signal()

            self.state = MACState.BACKOFF
            backoff_slots = random.randint(0, min(2**retries - 1, 1023))
            backoff_time = backoff_slots * self.slot_time
            self.stats.backoff_time += backoff_time
            time.sleep(backoff_time)

            retries += 1
            self.state = MACState.IDLE

        return False

    def _sense_channel(self) -> bool:
        return random.random() < 0.3

    def _start_transmission(self, data: bytes) -> bool:
        transmission_time = len(data) * 0.00001
        time.sleep(transmission_time)
        return not self.collision_detect_fn()

    def _jam_signal(self):
        time.sleep(self.slot_time * 0.5)

class TokenRing:
    def __init__(self, stations: List[str]):
        self.stations = stations
        self.token_holder = 0
        self.ring_latency = 0.001

    def pass_token(self):
        self.token_holder = (self.token_holder + 1) % len(self.stations)
        time.sleep(self.ring_latency)

    def has_token(self, station_id: str) -> bool:
        return self.stations[self.token_holder] == station_id

    def transmit(self, station_id: str, data: bytes) -> bool:
        if not self.has_token(station_id):
            return False

        transmission_time = len(data) * 0.00001
        time.sleep(transmission_time)

        self.pass_token()
        return True

class ALOHA:
    def __init__(self, station_id: str):
        self.station_id = station_id
        self.stats = MACStats()

    def transmit(self, data: bytes) -> bool:
        self.stats.transmissions += 1

        if random.random() < 0.368:
            self.stats.successful_transmissions += 1
            return True

        self.stats.collisions += 1
        time.sleep(random.uniform(0, 0.01))
        return False

class SlottedALOHA:
    def __init__(self, station_id: str, slot_time: float = 0.001):
        self.station_id = station_id
        self.slot_time = slot_time
        self.stats = MACStats()

    def wait_for_slot(self):
        current_time = time.time()
        next_slot = ((current_time // self.slot_time) + 1) * self.slot_time
        time.sleep(next_slot - current_time)

    def transmit(self, data: bytes) -> bool:
        self.wait_for_slot()
        self.stats.transmissions += 1

        if random.random() < 0.368 * 2:
            self.stats.successful_transmissions += 1
            return True

        self.stats.collisions += 1
        return False