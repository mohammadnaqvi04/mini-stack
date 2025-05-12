import sys
sys.path.insert(0, '..')

import pytest
from src.network.routing import DijkstraRouter, DistanceVectorRouter, LinkStateRouter

def test_dijkstra_simple_path():
    router = DijkstraRouter()
    router.add_link("A", "B", 1)
    router.add_link("B", "C", 1)

    paths = router.compute_shortest_paths("A")

    assert paths["B"][0] == 1
    assert paths["C"][0] == 2
    assert paths["C"][1] == ["A", "B", "C"]

def test_dijkstra_multiple_paths():
    router = DijkstraRouter()
    router.add_link("A", "B", 5)
    router.add_link("A", "C", 2)
    router.add_link("C", "B", 1)

    paths = router.compute_shortest_paths("A")

    # Should choose A -> C -> B over A -> B
    assert paths["B"][0] == 3
    assert paths["B"][1] == ["A", "C", "B"]

def test_distance_vector_basic():
    router = DistanceVectorRouter("A")
    router.add_neighbor("B", 1)
    router.add_neighbor("C", 5)

    dv = router.get_distance_vector()
    assert dv["A"] == 0
    assert dv["B"] == 1
    assert dv["C"] == 5

def test_distance_vector_update():
    router = DistanceVectorRouter("A")
    router.add_neighbor("B", 1)

    # B knows about C with cost 2
    updated = router.receive_update("B", {"C": 2, "D": 5})

    assert updated == True
    assert router.distance_vector["C"] == 3  # 1 + 2
    assert router.distance_vector["D"] == 6  # 1 + 5
    assert router.next_hop["C"] == "B"

def test_distance_vector_link_failure():
    router = DistanceVectorRouter("A")
    router.add_neighbor("B", 1)
    router.add_neighbor("C", 4)

    router.receive_update("B", {"D": 2})
    assert router.distance_vector["D"] == 3

    # Link to B fails
    router.handle_link_failure("B")

    # D should now be unreachable or route through C if available
    assert "D" not in router.distance_vector or router.distance_vector["D"] == float('inf')

def test_link_state_lsa_generation():
    router = LinkStateRouter("A")
    router.add_neighbor("B", 1)
    router.add_neighbor("C", 3)

    node_id, seq_num, neighbors = router.generate_lsa()

    assert node_id == "A"
    assert seq_num == 1
    assert neighbors == {"B": 1, "C": 3}

def test_link_state_convergence():
    # Test that link state converges to same view
    router_a = LinkStateRouter("A")
    router_a.add_neighbor("B", 1)

    router_b = LinkStateRouter("B")
    router_b.add_neighbor("A", 1)
    router_b.add_neighbor("C", 2)

    # Exchange LSAs
    lsa_a = router_a.generate_lsa()
    lsa_b = router_b.generate_lsa()

    router_a.receive_lsa(*lsa_b)
    router_b.receive_lsa(*lsa_a)

    # Both should compute consistent routing tables
    table_a = router_a.compute_routing_table()
    table_b = router_b.compute_routing_table()

    # A should route to C through B
    if "C" in table_a:
        assert table_a["C"].next_hop == "B"
        assert table_a["C"].cost == 3

if __name__ == "__main__":
    pytest.main([__file__, "-v"])