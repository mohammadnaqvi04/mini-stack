#!/usr/bin/env python3

import sys
sys.path.insert(0, '..')

from src.physical.channel import PhysicalChannel, ManchesterEncoder, SignalParams
from src.datalink.frame import Frame
from src.datalink.error_detection import CRC, HammingCode
from src.datalink.mac import CSMACD, TokenRing
from src.network.packet import IPPacket
from src.network.routing import DijkstraRouter, DistanceVectorRouter
from src.transport.tcp import TCPConnection, TCPState
from src.transport.udp import UDPSocket, UDPDatagram
from src.application.http_server import create_example_server, HTTPRequest
from src.application.dns_resolver import DNSResolver, DNSRecordType

def demonstrate_physical_layer():
    print("=== Physical Layer Demonstration ===")

    channel = PhysicalChannel(error_rate=0.01, latency_ms=5.0)

    encoder = ManchesterEncoder()
    original_bits = [1, 0, 1, 1, 0, 0, 1, 0]
    encoded = encoder.encode(original_bits)
    print(f"Original bits: {original_bits}")
    print(f"Manchester encoded: {encoded}")

    received, latency = channel.transmit(encoded)
    print(f"Received (with possible errors): {received}")
    print(f"Transmission latency: {latency}ms")

    params = SignalParams(
        bandwidth=1000000,
        signal_power=1.0,
        noise_power=0.01,
        attenuation=0.1
    )
    print(f"Channel capacity (Shannon): {params.shannon_capacity/1e6:.2f} Mbps")
    print(f"SNR: {params.snr_db:.2f} dB\n")

def demonstrate_datalink_layer():
    print("=== Data Link Layer Demonstration ===")

    frame = Frame(
        src_addr=b'\x00\x11\x22\x33\x44\x55',
        dest_addr=b'\xAA\xBB\xCC\xDD\xEE\xFF',
        payload=b'Hello, Network!',
        frame_type=0x0800,
        sequence_num=1
    )

    serialized = frame.serialize()
    print(f"Frame size: {len(serialized)} bytes")

    crc = CRC()
    data = b"Important network data"
    crc_value = crc.compute(data)
    print(f"CRC-16 checksum: 0x{crc_value:04X}")
    print(f"Verification: {crc.verify(data, crc_value)}")

    hamming = HammingCode()
    data_bits = [1, 0, 1, 1]
    encoded = hamming.encode(data_bits)
    print(f"Hamming encoded ({len(data_bits)} -> {len(encoded)} bits): {encoded}")

    encoded[2] ^= 1
    corrected, error_pos = hamming.decode(encoded)
    print(f"Error detected at position: {error_pos}")
    print(f"Corrected data: {corrected}")

    def collision_detect():
        import random
        return random.random() < 0.2

    csmacd = CSMACD("Station-A", collision_detect)
    success = csmacd.transmit(b"Ethernet frame data")
    print(f"\nCSMA/CD transmission: {'Success' if success else 'Failed'}")
    print(f"Stats - Collisions: {csmacd.stats.collisions}, Success: {csmacd.stats.successful_transmissions}\n")

def demonstrate_network_layer():
    print("=== Network Layer Demonstration ===")

    # IP packet creation
    packet = IPPacket(
        src_addr="192.168.1.1",
        dest_addr="192.168.1.2",
        ttl=64,
        protocol=6,  # TCP
        payload=b"TCP segment data"
    )

    serialized = packet.serialize()
    print(f"IP packet size: {len(serialized)} bytes")
    print(f"Checksum: 0x{packet.calculate_checksum():04X}")

    # Dijkstra's routing algorithm
    print("\nDijkstra's Algorithm:")
    router = DijkstraRouter()
    router.add_link("A", "B", 1)
    router.add_link("A", "C", 4)
    router.add_link("B", "C", 2)
    router.add_link("B", "D", 5)
    router.add_link("C", "D", 1)

    paths = router.compute_shortest_paths("A")
    for dest, (cost, path) in paths.items():
        print(f"  A -> {dest}: Cost={cost:.1f}, Path={' -> '.join(path)}")

    # Distance vector routing
    print("\nDistance Vector Routing:")
    dv_router = DistanceVectorRouter("RouterA")
    dv_router.add_neighbor("RouterB", 2)
    dv_router.add_neighbor("RouterC", 5)

    # Simulate receiving updates
    dv_router.receive_update("RouterB", {"RouterD": 3, "RouterE": 1})
    print(f"Distance vector from RouterA: {dv_router.get_distance_vector()}\n")

def demonstrate_transport_layer():
    print("=== Transport Layer Demonstration ===")

    # TCP connection simulation
    print("TCP Three-way Handshake:")
    client = TCPConnection(src_port=12345, dest_port=80)
    server = TCPConnection(src_port=80, dest_port=12345)

    # Client initiates connection
    server.state = TCPState.LISTEN
    syn = client.connect()
    print(f"1. Client -> Server: SYN (seq={syn.seq_num})")

    # Server responds
    syn_ack = server.accept_connection(syn)
    print(f"2. Server -> Client: SYN-ACK (seq={syn_ack.seq_num}, ack={syn_ack.ack_num})")

    # Client completes handshake
    ack = client.complete_handshake(syn_ack)
    print(f"3. Client -> Server: ACK (seq={ack.seq_num}, ack={ack.ack_num})")
    print(f"Connection established: {client.state == TCPState.ESTABLISHED}")

    # Send data
    data = b"HTTP GET request data"
    segments = client.send_data(data)
    print(f"\nSent {len(segments)} TCP segments")
    print(f"Congestion window: {client.congestion_window} bytes")

    # UDP datagram
    print("\nUDP Communication:")
    udp_socket = UDPSocket(port=53)
    datagram = udp_socket.send(b"DNS query", dest_port=53)
    print(f"UDP datagram sent: {len(datagram.payload)} bytes payload")
    print(f"Total size with header: {datagram.length} bytes\n")

def demonstrate_application_layer():
    print("=== Application Layer Demonstration ===")

    # HTTP server
    print("HTTP Server:")
    server = create_example_server()

    # Simulate GET request
    request_data = b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
    request = HTTPRequest.parse(request_data)
    response = server.handle_request(request)
    print(f"Request: {request.method} {request.path}")
    print(f"Response: {response.status_code} {response.status_text}")

    # DNS resolution
    print("\nDNS Resolution:")
    resolver = DNSResolver()
    records = resolver.resolve("example.com", DNSRecordType.A)
    if records:
        for record in records:
            print(f"  {record.name} -> {record.data} (TTL: {record.ttl}s)")

    # Reverse DNS
    domain = resolver.reverse_lookup("93.184.216.34")
    if domain:
        print(f"  Reverse lookup: 93.184.216.34 -> {domain}")

def main():
    print("Network Stack Implementation Demonstration\n")
    print("This project demonstrates key networking concepts including:")
    print("- Physical layer encoding and channel characteristics")
    print("- Data link layer framing and error detection")
    print("- Network layer routing algorithms")
    print("- Transport layer protocols (TCP/UDP)")
    print("- Application layer services\n")

    demonstrate_physical_layer()
    demonstrate_datalink_layer()
    demonstrate_network_layer()
    demonstrate_transport_layer()
    demonstrate_application_layer()

    print("\n=== Simulation Complete ===")
    print("This implementation covers the fundamental concepts of computer networking")
    print("as taught in CSC 335, including all OSI layers and their interactions.")

if __name__ == "__main__":
    main()