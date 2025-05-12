# Network Stack Implementation

A simplified TCP/IP network stack implementation demonstrating core networking concepts including OSI layers, routing algorithms, transport protocols, and network applications.

## Overview

This project implements a modular network stack simulation that covers:
- Physical and Data Link Layer simulation
- Network Layer with routing algorithms (Dijkstra, Distance Vector)
- Transport Layer protocols (simplified TCP/UDP)
- Application Layer examples
- Network performance analysis tools

## Architecture

The implementation follows the OSI model with clear separation between layers:

```
Application Layer (HTTP Server, Chat, File Transfer)
     ↓
Transport Layer (TCP/UDP)
     ↓
Network Layer (IP, Routing)
     ↓
Data Link Layer (Error Detection, Framing)
     ↓
Physical Layer (Bit transmission simulation)
```

## Features

- **Error Detection & Correction**: CRC, Hamming codes, and checksums
- **Routing Algorithms**: Dijkstra's shortest path and Distance Vector routing
- **Congestion Control**: TCP-like sliding window and flow control
- **Medium Access Control**: CSMA/CD simulation for broadcast networks
- **Protocol Analysis**: Packet capture and analysis tools

## Getting Started

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Start example applications
python examples/network_simulation.py
```

## Project Structure

```
├── src/
│   ├── physical/       # Physical layer simulation
│   ├── datalink/       # Data link protocols
│   ├── network/        # IP and routing
│   ├── transport/      # TCP/UDP implementation
│   └── application/    # Application examples
├── examples/           # Usage examples
├── tests/             # Unit tests
└── docs/              # Documentation
```