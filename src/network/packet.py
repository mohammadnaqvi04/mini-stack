from dataclasses import dataclass
from typing import Optional
import struct
import socket

@dataclass
class IPPacket:
    version: int = 4
    header_length: int = 5
    tos: int = 0
    total_length: int = 0
    identification: int = 0
    flags: int = 0
    fragment_offset: int = 0
    ttl: int = 64
    protocol: int = 6  # TCP by default
    checksum: int = 0
    src_addr: str = "0.0.0.0"
    dest_addr: str = "0.0.0.0"
    payload: bytes = b""

    def serialize(self) -> bytes:
        version_ihl = (self.version << 4) | self.header_length
        flags_fragoff = (self.flags << 13) | self.fragment_offset

        header = struct.pack(
            '!BBHHHBBH4s4s',
            version_ihl,
            self.tos,
            self.total_length,
            self.identification,
            flags_fragoff,
            self.ttl,
            self.protocol,
            self.checksum,
            socket.inet_aton(self.src_addr),
            socket.inet_aton(self.dest_addr)
        )

        return header + self.payload

    @classmethod
    def deserialize(cls, data: bytes) -> 'IPPacket':
        if len(data) < 20:
            raise ValueError("Invalid IP packet")

        (version_ihl, tos, total_length, identification,
         flags_fragoff, ttl, protocol, checksum,
         src_addr, dest_addr) = struct.unpack('!BBHHHBBH4s4s', data[:20])

        version = version_ihl >> 4
        header_length = version_ihl & 0x0F
        flags = flags_fragoff >> 13
        fragment_offset = flags_fragoff & 0x1FFF

        header_bytes = header_length * 4
        payload = data[header_bytes:]

        return cls(
            version=version,
            header_length=header_length,
            tos=tos,
            total_length=total_length,
            identification=identification,
            flags=flags,
            fragment_offset=fragment_offset,
            ttl=ttl,
            protocol=protocol,
            checksum=checksum,
            src_addr=socket.inet_ntoa(src_addr),
            dest_addr=socket.inet_ntoa(dest_addr),
            payload=payload
        )

    def calculate_checksum(self) -> int:
        # IP header checksum calculation
        header = self.serialize()[:20]
        # Zero out checksum field
        header = header[:10] + b'\x00\x00' + header[12:]

        checksum = 0
        for i in range(0, 20, 2):
            word = (header[i] << 8) + header[i + 1]
            checksum += word

        checksum = (checksum >> 16) + (checksum & 0xFFFF)
        checksum += (checksum >> 16)
        return ~checksum & 0xFFFF