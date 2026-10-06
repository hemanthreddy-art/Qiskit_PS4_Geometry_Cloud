"""
Tests for Finite Hyperbolic-inspired topology.
"""

import math
import pytest
from src.topologies.hyperbolic import HyperbolicTopology
from src.circuits.bell_state import create_bell_pair_circuit
from src.routing.transpiler import route_bell_circuit


def test_hyperbolic_graph_construction():
    topo = HyperbolicTopology()
    assert topo.num_qubits == 21
    assert len(topo.undirected_edges) == 40
    assert topo.get_diameter() == 4

    # Bulk center node 0 connected to 5 shell 1 nodes
    assert topo.get_node_degree(0) == 5

    # Shell 1 nodes have degree 6 (1 to center + 2 ring neighbors + 3 children in shell 2)
    for s1 in range(1, 6):
        assert topo.get_node_degree(s1) == 6


def test_hyperbolic_connectivity_and_distances():
    topo = HyperbolicTopology()

    # Center to any shell 1 node
    for s1 in range(1, 6):
        assert topo.shortest_path_distance(0, s1) == 1

    # Remote pair (6, 13)
    remote = topo.get_remote_qubits()
    assert remote == (6, 13)
    dist = topo.shortest_path_distance(*remote)
    assert dist == 4


def test_hyperbolic_poincare_coordinates():
    topo = HyperbolicTopology()
    coords = topo.get_layout_coordinates()
    assert len(coords) == 21

    # In Poincaré disk, all points must satisfy r = sqrt(x^2 + y^2) < 1.0
    for node, (x, y) in coords.items():
        radius = math.sqrt(x**2 + y**2)
        assert radius < 1.0, f"Node {node} radius {radius} exceeds Poincaré disk boundary!"


def test_hyperbolic_routing_and_metrics():
    topo = HyperbolicTopology()
    bell_qc = create_bell_pair_circuit()

    routing_res = route_bell_circuit(
        bell_circuit=bell_qc,
        coupling_map=topo.get_coupling_map(),
        initial_layout=list(topo.get_remote_qubits()),
        seed=42,
    )

    assert routing_res.swap_count == 3
    assert routing_res.native_cx_count == 10
    assert routing_res.depth_2q_native >= 4
    assert len(routing_res.final_physical_qubits) == 2
