from dataclasses import dataclass
from typing import List, Optional
import struct

@dataclass
class Frame:
    src_addr: bytes
    dest_addr: bytes
    payload: bytes
    frame_type: int
    sequence_num: int = 0
    ack_num: int = 0
    checksum: Optional[int] = None

    def serialize(self) -> bytes:
        header = struct.pack(
            '!6s6sHII',
            self.dest_addr,
            self.src_addr,
            self.frame_type,
            self.sequence_num,
            self.ack_num
        )
        return header + self.payload

    @classmethod
    def deserialize(cls, data: bytes) -> 'Frame':
        if len(data) < 22:
            raise ValueError("Invalid frame data")

        dest_addr, src_addr, frame_type, seq_num, ack_num = struct.unpack(
            '!6s6sHII', data[:22]
        )
        payload = data[22:]

        return cls(
            src_addr=src_addr,
            dest_addr=dest_addr,
            payload=payload,
            frame_type=frame_type,
            sequence_num=seq_num,
            ack_num=ack_num
        )

    def calculate_checksum(self) -> int:
        data = self.serialize()
        checksum = 0
        for i in range(0, len(data), 2):
            if i + 1 < len(data):
                word = (data[i] << 8) + data[i + 1]
            else:
                word = data[i] << 8
            checksum += word
            checksum = (checksum & 0xFFFF) + (checksum >> 16)
        return ~checksum & 0xFFFF