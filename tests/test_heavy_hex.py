"""
Tests for Contemporary IBM-style Heavy-Hex topology.
"""

import pytest
from src.topologies.heavy_hex import HeavyHexTopology
from src.circuits.bell_state import create_bell_pair_circuit
from src.routing.transpiler import route_bell_circuit


def test_heavy_hex_graph_construction():
    topo = HeavyHexTopology()
    assert topo.num_qubits == 27
    assert len(topo.undirected_edges) == 28
    assert topo.get_max_degree() == 3

    # Check that corner vertices have degree 3
    corner_vertices = [1, 7, 8, 12, 14, 18, 19, 25]
    for v in corner_vertices:
        assert topo.get_node_degree(v) == 3

    # Check that bridge qubits have degree <= 2
    bridge_qubits = [0, 2, 3, 4, 5, 6, 9, 10, 11, 13, 15, 16, 17, 20, 21, 22, 23, 24, 26]
    for b in bridge_qubits:
        assert topo.get_node_degree(b) <= 2


def test_heavy_hex_connectivity_and_distances():
    topo = HeavyHexTopology()

    # Shortest path direct edge
    assert topo.shortest_path_distance(0, 1) == 1
    assert topo.shortest_path_distance(1, 4) == 1

    # Remote pair distance
    remote_pair = topo.get_remote_qubits()
    assert remote_pair == (0, 14)
    dist = topo.shortest_path_distance(*remote_pair)
    assert dist == 7

    # Graph diameter
    diameter = topo.get_diameter()
    assert diameter >= 12


def test_heavy_hex_coordinates():
    topo = HeavyHexTopology()
    coords = topo.get_layout_coordinates()
    assert len(coords) == 27
    for node, (x, y) in coords.items():
        assert isinstance(x, (int, float))
        assert isinstance(y, (int, float))


def test_heavy_hex_routing_and_metrics():
    topo = HeavyHexTopology()
    bell_qc = create_bell_pair_circuit()

    routing_res = route_bell_circuit(
        bell_circuit=bell_qc,
        coupling_map=topo.get_coupling_map(),
        initial_layout=list(topo.get_remote_qubits()),
        seed=42,
    )

    assert routing_res.swap_count == 6
    assert routing_res.native_cx_count == 19
    assert routing_res.depth_2q_native >= 10
    assert len(routing_res.final_physical_qubits) == 2


def test_heavy_hex_127_reference_model():
    from src.topologies.heavy_hex import HeavyHex127Topology
    topo = HeavyHex127Topology()
    assert topo.num_qubits == 127
    assert len(topo.undirected_edges) == 144
    assert topo.get_max_degree() == 3
    assert topo.get_diameter() == 26
    summary = topo.summary()
    assert summary["num_qubits"] == 127
    assert summary["max_degree"] == 3
    coords = topo.get_layout_coordinates()
    assert len(coords) == 127
