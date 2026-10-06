"""
Validation tests for scientific integrity, circuit extraction, and graph properties.
"""

import math
import pytest
import rustworkx as rx
from src.topologies.star_t import StarTTopology
from src.topologies.heavy_hex import HeavyHexTopology
from src.topologies.hyperbolic import HyperbolicTopology
from src.circuits.bell_state import create_bell_pair_circuit
from src.routing.transpiler import route_bell_circuit
from src.metrics.fidelity import compute_bell_fidelity


def test_validation_hyperbolic_connectivity_and_degree():
    """Validate Hyperbolic graph connectivity, diameter, and degree 6 origin."""
    topo = HyperbolicTopology()

    # 1. Connectedness
    assert rx.is_connected(topo._rx_graph), "Hyperbolic graph must be connected!"

    # 2. Qubit count & edge count
    assert topo.num_qubits == 21
    assert len(topo.undirected_edges) == 40

    # 3. Exact degree distribution
    # Center node 0: connected to 5 shell 1 nodes -> degree 5
    assert topo.get_node_degree(0) == 5

    # Shell 1 nodes (1..5): 1 to center + 2 ring neighbors + 3 children in shell 2 -> degree 6
    for s1 in range(1, 6):
        assert topo.get_node_degree(s1) == 6, f"Shell 1 node {s1} must have degree 6!"

    # Shell 2 nodes (6..20): 1 to parent in shell 1 + 2 ring neighbors in shell 2 -> degree 3
    for s2 in range(6, 21):
        assert topo.get_node_degree(s2) == 3, f"Shell 2 node {s2} must have degree 3!"

    # 4. Max degree is strictly 6
    assert topo.get_max_degree() == 6

    # 5. Diameter is 4
    assert topo.get_diameter() == 4

    # 6. Poincaré disk coordinates strictly inside unit disk r < 1
    coords = topo.get_layout_coordinates()
    for n, (x, y) in coords.items():
        r = math.sqrt(x**2 + y**2)
        assert r < 1.0, f"Node {n} at radius {r} is outside Poincaré disk!"


def test_validation_heavy_hex_connectivity_and_degree():
    """Validate Heavy-Hex graph connectivity and maximum degree 3."""
    topo = HeavyHexTopology()

    # 1. Connectedness
    assert rx.is_connected(topo._rx_graph), "Heavy-Hex graph must be connected!"

    # 2. Qubit count & edge count
    assert topo.num_qubits == 27
    assert len(topo.undirected_edges) == 28

    # 3. Maximum degree is strictly 3 (no node exceeds degree 3)
    assert topo.get_max_degree() == 3
    for node in range(27):
        assert topo.get_node_degree(node) <= 3


def test_validation_actual_transpiled_circuit_metrics():
    """
    Validate that reported SWAP counts, CX counts, and depths are extracted
    directly from actual Qiskit QuantumCircuit data and not from shortcut formulas.
    """
    topologies = [
        StarTTopology(variant="t"),
        HeavyHexTopology(remote_pair=(0, 14)),
        HyperbolicTopology(remote_pair=(6, 13)),
    ]
    bell_qc = create_bell_pair_circuit()

    for topo in topologies:
        pair = list(topo.get_remote_qubits())
        res = route_bell_circuit(bell_qc, topo.get_coupling_map(), pair, seed=42)

        # Count actual 'swap' gates in the routed circuit data
        actual_swaps_in_circuit = sum(
            1 for inst in res.routed_circuit.data if inst.operation.name == "swap"
        )
        assert res.swap_count == actual_swaps_in_circuit

        # Count actual 'cx' gates in the native circuit data
        actual_cxs_in_circuit = sum(
            1 for inst in res.native_circuit.data if inst.operation.name == "cx"
        )
        assert res.native_cx_count == actual_cxs_in_circuit
        assert res.native_cx_count == (res.swap_count * 3 + 1)

        # Depth calculations from circuit methods
        assert res.total_depth_native == res.native_circuit.depth()
        actual_2q_depth = res.native_circuit.depth(
            filter_function=lambda inst: inst.operation.num_qubits == 2
        )
        assert res.depth_2q_native == actual_2q_depth


def test_validation_fidelity_formula():
    """Validate strict mathematical fidelity computation."""
    # Test cases: (XX, YY, ZZ, expected_fidelity)
    test_cases = [
        (1.0, -1.0, 1.0, 1.0),            # Ideal |Phi+>
        (0.0, 0.0, 0.0, 0.25),            # Maximally mixed state
        (0.8837, -0.8503, 0.8886, 0.90565),   # Star/T measured values
        (0.7692, -0.7090, 0.8525, 0.832675),  # Heavy-Hex measured values
        (0.8482, -0.8132, 0.8872, 0.88715),   # Hyperbolic measured values
    ]
    for xx, yy, zz, exp_f in test_cases:
        f, _ = compute_bell_fidelity(xx, yy, zz)
        assert math.isclose(f, exp_f, rel_tol=1e-5)
