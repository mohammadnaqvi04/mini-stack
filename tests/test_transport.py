import sys
sys.path.insert(0, '..')

import pytest
from src.transport.tcp import TCPConnection, TCPSegment, TCPState
from src.transport.udp import UDPDatagram, UDPSocket

def test_tcp_three_way_handshake():
    client = TCPConnection(src_port=12345, dest_port=80)
    server = TCPConnection(src_port=80, dest_port=12345)

    # Server listens
    server.state = TCPState.LISTEN

    # Client initiates
    syn = client.connect()
    assert client.state == TCPState.SYN_SENT
    assert syn.flags & 0x02  # SYN flag

    # Server responds
    syn_ack = server.accept_connection(syn)
    assert server.state == TCPState.SYN_RECEIVED
    assert syn_ack.flags & 0x12  # SYN + ACK flags

    # Client completes
    ack = client.complete_handshake(syn_ack)
    assert client.state == TCPState.ESTABLISHED
    assert ack.flags & 0x10  # ACK flag

def test_tcp_segment_serialization():
    segment = TCPSegment(
        src_port=8080,
        dest_port=443,
        seq_num=1000,
        ack_num=2000,
        flags=0x18,  # PSH + ACK
        window_size=65535,
        payload=b"Test data"
    )

    serialized = segment.serialize()
    assert len(serialized) >= 20  # Minimum TCP header size

    deserialized = TCPSegment.deserialize(serialized)
    assert deserialized.src_port == 8080
    assert deserialized.dest_port == 443
    assert deserialized.seq_num == 1000
    assert deserialized.payload == b"Test data"

def test_tcp_data_transmission():
    conn = TCPConnection(src_port=12345, dest_port=80)
    conn.state = TCPState.ESTABLISHED

    data = b"HTTP GET / HTTP/1.1\r\n"
    segments = conn.send_data(data)

    assert len(segments) > 0
    assert segments[0].payload == data
    assert segments[0].seq_num in conn.unacked_segments

def test_tcp_congestion_control():
    conn = TCPConnection(src_port=12345, dest_port=80)
    conn.state = TCPState.ESTABLISHED

    initial_cwnd = conn.congestion_window

    # Simulate successful ACK
    ack_segment = TCPSegment(
        src_port=80,
        dest_port=12345,
        seq_num=0,
        ack_num=conn.seq_num + 100,
        flags=0x10,
        window_size=65535
    )

    conn.receive_ack(ack_segment)

    # Congestion window should increase (slow start)
    assert conn.congestion_window > initial_cwnd

def test_udp_datagram():
    socket = UDPSocket(port=53)

    data = b"DNS query packet"
    datagram = socket.send(data, dest_port=53)

    assert datagram.src_port == 53
    assert datagram.dest_port == 53
    assert datagram.payload == data
    assert datagram.length == len(data) + 8  # UDP header is 8 bytes

def test_udp_serialization():
    datagram = UDPDatagram(
        src_port=12345,
        dest_port=53,
        length=20,
        checksum=0,
        payload=b"Test payload"
    )

    serialized = datagram.serialize()
    assert len(serialized) >= 8

    deserialized = UDPDatagram.deserialize(serialized)
    assert deserialized.src_port == 12345
    assert deserialized.dest_port == 53

def test_udp_socket_buffer():
    socket = UDPSocket(port=8080)

    # Test receiving datagrams
    datagram1 = UDPDatagram(
        src_port=1234,
        dest_port=8080,
        length=10,
        checksum=0,
        payload=b"Message 1"
    )

    assert socket.receive(datagram1) == True
    assert len(socket.buffer) == 1

    # Read from buffer
    data = socket.read()
    assert data == b"Message 1"
    assert len(socket.buffer) == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])