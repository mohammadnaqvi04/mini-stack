import heapq
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
import math

@dataclass
class RoutingEntry:
    destination: str
    next_hop: str
    cost: float
    interface: str

@dataclass(order=True)
class PriorityNode:
    cost: float
    node: str = field(compare=False)

class DijkstraRouter:
    def __init__(self):
        self.graph: Dict[str, Dict[str, float]] = {}
        self.routing_table: Dict[str, RoutingEntry] = {}

    def add_link(self, node1: str, node2: str, cost: float):
        if node1 not in self.graph:
            self.graph[node1] = {}
        if node2 not in self.graph:
            self.graph[node2] = {}

        self.graph[node1][node2] = cost
        self.graph[node2][node1] = cost

    def compute_shortest_paths(self, source: str) -> Dict[str, Tuple[float, List[str]]]:
        distances = {node: float('inf') for node in self.graph}
        distances[source] = 0
        parents = {node: None for node in self.graph}
        visited = set()

        pq = [PriorityNode(0, source)]

        while pq:
            current = heapq.heappop(pq)

            if current.node in visited:
                continue

            visited.add(current.node)

            for neighbor, weight in self.graph.get(current.node, {}).items():
                if neighbor in visited:
                    continue

                new_dist = distances[current.node] + weight

                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    parents[neighbor] = current.node
                    heapq.heappush(pq, PriorityNode(new_dist, neighbor))

        paths = {}
        for node in self.graph:
            if node == source:
                continue

            path = []
            current = node
            while current is not None:
                path.append(current)
                current = parents[current]

            path.reverse()
            paths[node] = (distances[node], path)

        return paths

    def build_routing_table(self, source: str):
        paths = self.compute_shortest_paths(source)
        self.routing_table.clear()

        for dest, (cost, path) in paths.items():
            if len(path) > 1:
                next_hop = path[1] if len(path) > 1 else dest
                self.routing_table[dest] = RoutingEntry(
                    destination=dest,
                    next_hop=next_hop,
                    cost=cost,
                    interface=f"eth{hash(next_hop) % 4}"
                )

class DistanceVectorRouter:
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.neighbors: Dict[str, float] = {}
        self.distance_vector: Dict[str, float] = {node_id: 0}
        self.next_hop: Dict[str, str] = {node_id: node_id}
        self.neighbor_tables: Dict[str, Dict[str, float]] = {}

    def add_neighbor(self, neighbor_id: str, cost: float):
        self.neighbors[neighbor_id] = cost
        self.distance_vector[neighbor_id] = cost
        self.next_hop[neighbor_id] = neighbor_id

    def receive_update(self, from_node: str, distance_vector: Dict[str, float]) -> bool:
        self.neighbor_tables[from_node] = distance_vector.copy()
        updated = False

        for dest, dist in distance_vector.items():
            if dest == self.node_id:
                continue

            new_cost = self.neighbors.get(from_node, float('inf')) + dist

            if dest not in self.distance_vector or new_cost < self.distance_vector[dest]:
                self.distance_vector[dest] = new_cost
                self.next_hop[dest] = from_node
                updated = True

        return updated

    def get_distance_vector(self) -> Dict[str, float]:
        return self.distance_vector.copy()

    def handle_link_failure(self, failed_neighbor: str):
        updated = False

        for dest in list(self.distance_vector.keys()):
            if self.next_hop.get(dest) == failed_neighbor:
                if dest == failed_neighbor:
                    del self.distance_vector[dest]
                    del self.next_hop[dest]
                else:
                    self.distance_vector[dest] = float('inf')
                updated = True

        if failed_neighbor in self.neighbors:
            del self.neighbors[failed_neighbor]

        if failed_neighbor in self.neighbor_tables:
            del self.neighbor_tables[failed_neighbor]

        self._recompute_routes()
        return updated

    def _recompute_routes(self):
        for dest in list(self.distance_vector.keys()):
            if dest == self.node_id:
                continue

            min_cost = float('inf')
            best_neighbor = None

            for neighbor, neighbor_table in self.neighbor_tables.items():
                if dest in neighbor_table:
                    cost = self.neighbors[neighbor] + neighbor_table[dest]
                    if cost < min_cost:
                        min_cost = cost
                        best_neighbor = neighbor

            if best_neighbor:
                self.distance_vector[dest] = min_cost
                self.next_hop[dest] = best_neighbor
            elif dest not in self.neighbors:
                del self.distance_vector[dest]
                del self.next_hop[dest]

class LinkStateRouter:
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.sequence_number = 0
        self.link_state_db: Dict[str, Dict[str, Tuple[float, int]]] = {}
        self.neighbors: Dict[str, float] = {}

    def add_neighbor(self, neighbor_id: str, cost: float):
        self.neighbors[neighbor_id] = cost

    def generate_lsa(self) -> Tuple[str, int, Dict[str, float]]:
        self.sequence_number += 1
        return (self.node_id, self.sequence_number, self.neighbors.copy())

    def receive_lsa(self, node_id: str, seq_num: int, neighbors: Dict[str, float]) -> bool:
        if node_id not in self.link_state_db:
            self.link_state_db[node_id] = {}

        for neighbor, cost in neighbors.items():
            if neighbor not in self.link_state_db[node_id] or \
               self.link_state_db[node_id][neighbor][1] < seq_num:
                self.link_state_db[node_id][neighbor] = (cost, seq_num)
                return True

        return False

    def compute_routing_table(self) -> Dict[str, RoutingEntry]:
        graph = {}
        for node, neighbors in self.link_state_db.items():
            if node not in graph:
                graph[node] = {}
            for neighbor, (cost, _) in neighbors.items():
                graph[node][neighbor] = cost

        if self.node_id not in graph:
            graph[self.node_id] = {}
        graph[self.node_id].update(self.neighbors)

        router = DijkstraRouter()
        router.graph = graph
        router.build_routing_table(self.node_id)

        return router.routing_table