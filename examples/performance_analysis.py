#!/usr/bin/env python3

import sys
sys.path.insert(0, '..')

import time
import matplotlib.pyplot as plt
import numpy as np
from src.physical.channel import PhysicalChannel
from src.datalink.mac import CSMACD, SlottedALOHA
from src.network.routing import DijkstraRouter

def analyze_channel_capacity():
    # Shannon capacity analysis
    bandwidths = np.logspace(3, 7, 50)  # 1 kHz to 10 MHz
    snr_values = [0.1, 1, 10, 100]  # Different SNR scenarios

    results = {}
    for snr in snr_values:
        capacities = []
        for bw in bandwidths:
            capacity = bw * np.log2(1 + snr)
            capacities.append(capacity / 1e6)  # Convert to Mbps
        results[snr] = capacities

    return bandwidths, results

def analyze_mac_protocols():
    # Compare different MAC protocols
    load_factors = np.linspace(0.1, 1.0, 10)
    protocols = {}

    # CSMA/CD simulation
    csmacd_throughput = []
    for load in load_factors:
        def collision_prob():
            return np.random.random() < load * 0.3

        csmacd = CSMACD("Station", collision_prob)
        success_count = 0
        for _ in range(100):
            if csmacd.transmit(b"data"):
                success_count += 1

        csmacd_throughput.append(success_count / 100)

    protocols['CSMA/CD'] = csmacd_throughput

    # Slotted ALOHA
    aloha_throughput = []
    for load in load_factors:
        aloha = SlottedALOHA("Station")
        success_count = 0
        for _ in range(100):
            if aloha.transmit(b"data"):
                success_count += 1
        aloha_throughput.append(success_count / 100)

    protocols['Slotted ALOHA'] = aloha_throughput

    return load_factors, protocols

def analyze_routing_scalability():
    # Test routing algorithm performance with different network sizes
    network_sizes = [10, 20, 30, 40, 50]
    dijkstra_times = []

    for size in network_sizes:
        router = DijkstraRouter()

        # Create random network topology
        for i in range(size):
            for j in range(i+1, min(i+4, size)):
                cost = np.random.uniform(1, 10)
                router.add_link(f"Node{i}", f"Node{j}", cost)

        # Measure computation time
        start = time.time()
        router.compute_shortest_paths("Node0")
        elapsed = time.time() - start
        dijkstra_times.append(elapsed * 1000)  # Convert to ms

    return network_sizes, dijkstra_times

def main():
    print("Network Performance Analysis\n")

    # Channel capacity analysis
    print("Analyzing channel capacity...")
    bandwidths, capacities = analyze_channel_capacity()
    print(f"  Bandwidth range: {bandwidths[0]/1e3:.1f} kHz - {bandwidths[-1]/1e6:.1f} MHz")
    print(f"  Max capacity (SNR=100): {max(capacities[100]):.1f} Mbps")

    # MAC protocol comparison
    print("\nComparing MAC protocols...")
    loads, protocols = analyze_mac_protocols()
    for name, throughput in protocols.items():
        avg_throughput = np.mean(throughput)
        print(f"  {name} average throughput: {avg_throughput:.2%}")

    # Routing scalability
    print("\nAnalyzing routing scalability...")
    sizes, times = analyze_routing_scalability()
    print(f"  Network sizes: {sizes[0]} - {sizes[-1]} nodes")
    print(f"  Computation time range: {min(times):.2f} - {max(times):.2f} ms")

    print("\nPerformance analysis complete.")

if __name__ == "__main__":
    main()