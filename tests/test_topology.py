"""
Tests for 2016-inspired Star/T topology representation.
"""

import pytest
from src.topologies.star_t import StarTTopology


def test_star_t_initialization():
    topo_t = StarTTopology(variant="t")
    assert topo_t.num_qubits == 5
    assert topo_t.variant == "t"
    assert len(topo_t.undirected_edges) == 4

    topo_star = StarTTopology(variant="star")
    assert topo_star.num_qubits == 5
    assert topo_star.variant == "star"
    assert len(topo_star.undirected_edges) == 4


def test_invalid_variant():
    with pytest.raises(ValueError, match="Unknown Star/T variant"):
        StarTTopology(variant="hexagonal")


def test_t_topology_distances_and_remote_pair():
    topo = StarTTopology(variant="t")

    # Direct edges have distance 1
    assert topo.shortest_path_distance(0, 2) == 1
    assert topo.shortest_path_distance(1, 2) == 1
    assert topo.shortest_path_distance(2, 3) == 1
    assert topo.shortest_path_distance(3, 4) == 1

    # 2-hop distances
    assert topo.shortest_path_distance(0, 1) == 2
    assert topo.shortest_path_distance(0, 3) == 2
    assert topo.shortest_path_distance(2, 4) == 2

    # 3-hop remote distance (0 to 4 or 1 to 4)
    assert topo.shortest_path_distance(0, 4) == 3
    assert topo.shortest_path_distance(1, 4) == 3

    # Remote pair identification
    remote = topo.get_remote_qubits()
    assert remote in [(0, 4), (4, 0), (1, 4), (4, 1)]
    assert topo.shortest_path_distance(*remote) == 3


def test_star_topology_distances_and_remote_pair():
    topo = StarTTopology(variant="star")

    # Center is qubit 2
    for leaf in [0, 1, 3, 4]:
        assert topo.shortest_path_distance(2, leaf) == 1

    # Any two leaves have distance 2
    assert topo.shortest_path_distance(0, 1) == 2
    assert topo.shortest_path_distance(0, 4) == 2

    remote = topo.get_remote_qubits()
    assert topo.shortest_path_distance(*remote) == 2
