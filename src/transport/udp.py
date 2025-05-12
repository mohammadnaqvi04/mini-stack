from dataclasses import dataclass
import struct
import socket

@dataclass
class UDPDatagram:
    src_port: int
    dest_port: int
    length: int
    checksum: int
    payload: bytes

    def serialize(self) -> bytes:
        header = struct.pack(
            '!HHHH',
            self.src_port,
            self.dest_port,
            self.length,
            self.checksum
        )
        return header + self.payload

    @classmethod
    def deserialize(cls, data: bytes) -> 'UDPDatagram':
        if len(data) < 8:
            raise ValueError("Invalid UDP datagram")

        src_port, dest_port, length, checksum = struct.unpack('!HHHH', data[:8])
        payload = data[8:length]

        return cls(
            src_port=src_port,
            dest_port=dest_port,
            length=length,
            checksum=checksum,
            payload=payload
        )

    def calculate_checksum(self, src_addr: str, dest_addr: str) -> int:
        pseudo_header = struct.pack(
            '!4s4sBBH',
            socket.inet_aton(src_addr),
            socket.inet_aton(dest_addr),
            0,
            socket.IPPROTO_UDP,
            self.length
        )

        data = pseudo_header + self.serialize()

        if len(data) % 2 != 0:
            data += b'\x00'

        checksum = 0
        for i in range(0, len(data), 2):
            word = (data[i] << 8) + data[i + 1]
            checksum += word

        checksum = (checksum >> 16) + (checksum & 0xFFFF)
        checksum += (checksum >> 16)

        return ~checksum & 0xFFFF

class UDPSocket:
    def __init__(self, port: int):
        self.port = port
        self.buffer = []
        self.max_buffer_size = 100

    def send(self, data: bytes, dest_port: int) -> UDPDatagram:
        length = len(data) + 8

        datagram = UDPDatagram(
            src_port=self.port,
            dest_port=dest_port,
            length=length,
            checksum=0,
            payload=data
        )

        datagram.checksum = 0

        return datagram

    def receive(self, datagram: UDPDatagram) -> bool:
        if datagram.dest_port != self.port:
            return False

        if len(self.buffer) < self.max_buffer_size:
            self.buffer.append(datagram)
            return True

        return False

    def read(self) -> bytes:
        if self.buffer:
            datagram = self.buffer.pop(0)
            return datagram.payload
        return b""