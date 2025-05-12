# Network Stack Architecture

## Overview

This implementation demonstrates a complete network stack following the OSI model layers.

## Layer Implementations

### Physical Layer
- **Signal Encoding**: Manchester and NRZI encoding schemes
- **Channel Simulation**: Error rates, latency, and Shannon capacity
- **Bit-level Operations**: Direct manipulation of binary data

### Data Link Layer
- **Framing**: Ethernet-style frame structure with addressing
- **Error Detection**: CRC-16, checksums, and Hamming codes
- **MAC Protocols**: CSMA/CD, Token Ring, and ALOHA implementations

### Network Layer
- **IP Packets**: Full IPv4 packet structure with headers
- **Routing Algorithms**:
  - Dijkstra's shortest path
  - Distance Vector (Bellman-Ford)
  - Link State routing

### Transport Layer
- **TCP**: Connection management, congestion control, flow control
- **UDP**: Connectionless datagram service
- **Reliability**: Sequence numbers, acknowledgments, retransmission

### Application Layer
- **HTTP Server**: Request/response handling
- **DNS Resolver**: Recursive and iterative resolution

## Key Features

1. **Modular Design**: Each layer operates independently
2. **Protocol Simulation**: Realistic protocol behavior
3. **Error Handling**: Built-in error detection and correction
4. **Performance Metrics**: Throughput, latency, and reliability measurements