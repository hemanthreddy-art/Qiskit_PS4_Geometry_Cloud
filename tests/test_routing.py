"""
Tests for topology routing and transpilation metrics.
"""

from src.circuits.bell_state import create_bell_pair_circuit
from src.topologies.star_t import StarTTopology
from src.routing.transpiler import route_bell_circuit


def test_routing_remote_pair_t_topology():
    topo = StarTTopology(variant="t")
    coupling_map = topo.get_coupling_map()
    bell_qc = create_bell_pair_circuit()

    # Remote pair (0, 4) with distance 3
    result = route_bell_circuit(
        bell_circuit=bell_qc,
        coupling_map=coupling_map,
        initial_layout=[0, 4],
        seed=42,
    )

    # SWAP count must be > 0 (strictly 2 for Yorktown T)
    assert result.swap_count == 2
    # Decomposed native CX count: 1 original + 2*3 from SWAPs = 7 CX gates
    assert result.native_cx_count == 7
    # Two-qubit depth
    assert result.depth_2q_native >= 2
    # Initial layout preserved
    assert result.initial_layout == [0, 4]
    # Check that final physical qubits are valid indices in [0, 4]
    assert len(result.final_physical_qubits) == 2
    for q in result.final_physical_qubits:
        assert 0 <= q < 5


def test_routing_adjacent_pair_zero_swaps():
    topo = StarTTopology(variant="t")
    coupling_map = topo.get_coupling_map()
    bell_qc = create_bell_pair_circuit()

    # Directly connected pair (0, 2)
    result = route_bell_circuit(
        bell_circuit=bell_qc,
        coupling_map=coupling_map,
        initial_layout=[0, 2],
        seed=42,
    )

    # Adjacent qubits require 0 SWAP gates
    assert result.swap_count == 0
    assert result.native_cx_count == 1
