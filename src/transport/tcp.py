from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple
from enum import Enum
import struct
import time
import random

class TCPState(Enum):
    CLOSED = 1
    LISTEN = 2
    SYN_SENT = 3
    SYN_RECEIVED = 4
    ESTABLISHED = 5
    FIN_WAIT_1 = 6
    FIN_WAIT_2 = 7
    CLOSE_WAIT = 8
    CLOSING = 9
    LAST_ACK = 10
    TIME_WAIT = 11

@dataclass
class TCPSegment:
    src_port: int
    dest_port: int
    seq_num: int
    ack_num: int
    flags: int
    window_size: int
    checksum: int = 0
    urgent_ptr: int = 0
    payload: bytes = b""

    def serialize(self) -> bytes:
        data_offset = 5 << 4

        header = struct.pack(
            '!HHLLBBHHH',
            self.src_port,
            self.dest_port,
            self.seq_num,
            self.ack_num,
            data_offset,
            self.flags,
            self.window_size,
            self.checksum,
            self.urgent_ptr
        )

        return header + self.payload

    @classmethod
    def deserialize(cls, data: bytes) -> 'TCPSegment':
        if len(data) < 20:
            raise ValueError("Invalid TCP segment")

        (src_port, dest_port, seq_num, ack_num,
         data_offset_flags, flags, window_size,
         checksum, urgent_ptr) = struct.unpack('!HHLLBBHHH', data[:20])

        data_offset = (data_offset_flags >> 4) * 4
        payload = data[data_offset:]

        return cls(
            src_port=src_port,
            dest_port=dest_port,
            seq_num=seq_num,
            ack_num=ack_num,
            flags=flags,
            window_size=window_size,
            checksum=checksum,
            urgent_ptr=urgent_ptr,
            payload=payload
        )

class TCPConnection:
    def __init__(self, src_port: int, dest_port: int):
        self.src_port = src_port
        self.dest_port = dest_port
        self.state = TCPState.CLOSED

        self.seq_num = random.randint(0, 2**32 - 1)
        self.ack_num = 0
        self.expected_seq = 0

        self.send_window = 65536
        self.recv_window = 65536
        self.congestion_window = 1460
        self.ssthresh = 65536

        self.send_buffer: List[bytes] = []
        self.recv_buffer: List[bytes] = []
        self.unacked_segments: Dict[int, Tuple[TCPSegment, float]] = {}

        self.srtt = 0.5
        self.rttvar = 0.25
        self.rto = 1.0

    def connect(self) -> TCPSegment:
        if self.state != TCPState.CLOSED:
            raise Exception("Connection not in CLOSED state")

        self.state = TCPState.SYN_SENT
        syn_segment = TCPSegment(
            src_port=self.src_port,
            dest_port=self.dest_port,
            seq_num=self.seq_num,
            ack_num=0,
            flags=0x02,
            window_size=self.recv_window
        )

        return syn_segment

    def accept_connection(self, syn_segment: TCPSegment) -> TCPSegment:
        if self.state != TCPState.LISTEN:
            raise Exception("Not listening for connections")

        self.state = TCPState.SYN_RECEIVED
        self.expected_seq = syn_segment.seq_num + 1

        syn_ack = TCPSegment(
            src_port=self.src_port,
            dest_port=syn_segment.src_port,
            seq_num=self.seq_num,
            ack_num=self.expected_seq,
            flags=0x12,
            window_size=self.recv_window
        )

        return syn_ack

    def complete_handshake(self, syn_ack: TCPSegment) -> TCPSegment:
        if self.state != TCPState.SYN_SENT:
            raise Exception("Invalid state for completing handshake")

        self.state = TCPState.ESTABLISHED
        self.ack_num = syn_ack.seq_num + 1

        ack = TCPSegment(
            src_port=self.src_port,
            dest_port=self.dest_port,
            seq_num=self.seq_num + 1,
            ack_num=self.ack_num,
            flags=0x10,
            window_size=self.recv_window
        )

        return ack

    def send_data(self, data: bytes) -> List[TCPSegment]:
        if self.state != TCPState.ESTABLISHED:
            raise Exception("Connection not established")

        segments = []
        mss = 1460
        offset = 0

        while offset < len(data):
            if len(self.unacked_segments) * mss >= self.congestion_window:
                break

            chunk = data[offset:offset + mss]
            segment = TCPSegment(
                src_port=self.src_port,
                dest_port=self.dest_port,
                seq_num=self.seq_num,
                ack_num=self.ack_num,
                flags=0x18,
                window_size=self.recv_window,
                payload=chunk
            )

            segments.append(segment)
            self.unacked_segments[self.seq_num] = (segment, time.time())
            self.seq_num += len(chunk)
            offset += mss

        return segments

    def receive_ack(self, ack_segment: TCPSegment):
        acked_seq = ack_segment.ack_num

        for seq_num in list(self.unacked_segments.keys()):
            if seq_num < acked_seq:
                segment, send_time = self.unacked_segments.pop(seq_num)

                sample_rtt = time.time() - send_time
                self.rttvar = 0.75 * self.rttvar + 0.25 * abs(self.srtt - sample_rtt)
                self.srtt = 0.875 * self.srtt + 0.125 * sample_rtt
                self.rto = self.srtt + 4 * self.rttvar

                if self.congestion_window < self.ssthresh:
                    self.congestion_window += 1460
                else:
                    self.congestion_window += 1460 * 1460 // self.congestion_window

        self.send_window = ack_segment.window_size

    def handle_timeout(self):
        current_time = time.time()
        retransmitted = []

        for seq_num, (segment, send_time) in self.unacked_segments.items():
            if current_time - send_time > self.rto:
                retransmitted.append(segment)
                self.unacked_segments[seq_num] = (segment, current_time)

                self.ssthresh = max(self.congestion_window // 2, 2 * 1460)
                self.congestion_window = 1460

        return retransmitted

    def close_connection(self) -> TCPSegment:
        if self.state != TCPState.ESTABLISHED:
            raise Exception("Connection not established")

        self.state = TCPState.FIN_WAIT_1

        fin = TCPSegment(
            src_port=self.src_port,
            dest_port=self.dest_port,
            seq_num=self.seq_num,
            ack_num=self.ack_num,
            flags=0x11,
            window_size=self.recv_window
        )

        return fin