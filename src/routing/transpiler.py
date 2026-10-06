"""
Topology-constrained routing and transpilation.

This module maps a 2-qubit logical circuit (e.g. Bell state preparation) onto
a specified coupling map with fixed remote physical qubit assignments.
It computes:
- SWAP gate count inserted by the router
- Two-qubit gate depth (both pre- and post-SWAP decomposition)
- Tracking of the active physical locations of the logical qubits.
"""

from dataclasses import dataclass
from typing import List, Tuple, Dict, Any, Optional
from qiskit import QuantumCircuit, transpile
from qiskit.transpiler import CouplingMap


@dataclass
class RoutingResult:
    """
    Encapsulates results from topology-constrained circuit routing.
    """
    routed_circuit: QuantumCircuit
    native_circuit: QuantumCircuit
    initial_layout: List[int]
    final_physical_qubits: Tuple[int, int]
    swap_count: int
    native_cx_count: int
    depth_2q_routed: int
    depth_2q_native: int
    total_depth_routed: int
    total_depth_native: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to a serializable dictionary."""
        return {
            "initial_layout": self.initial_layout,
            "final_physical_qubits": list(self.final_physical_qubits),
            "swap_count": self.swap_count,
            "native_cx_count": self.native_cx_count,
            "depth_2q_routed": self.depth_2q_routed,
            "depth_2q_native": self.depth_2q_native,
            "total_depth_routed": self.total_depth_routed,
            "total_depth_native": self.total_depth_native,
        }


def route_bell_circuit(
    bell_circuit: QuantumCircuit,
    coupling_map: CouplingMap,
    initial_layout: List[int],
    routing_method: str = "sabre",
    optimization_level: int = 1,
    seed: Optional[int] = 42
) -> RoutingResult:
    """
    Transpile a 2-qubit Bell circuit onto a hardware coupling map
    with explicit initial layout on two remote physical qubits.

    Parameters:
        bell_circuit: 2-qubit logical circuit.
        coupling_map: Hardware CouplingMap object.
        initial_layout: List of 2 physical qubit indices, e.g. [0, 4].
        routing_method: Router algorithm (e.g. 'sabre', 'lookahead', 'stochastic').
        optimization_level: Transpiler optimization level (default 1).
        seed: Random seed for deterministic SABRE routing.

    Returns:
        RoutingResult containing the routed circuits and metrics.
    """
    if len(initial_layout) != 2:
        raise ValueError(f"initial_layout must contain exactly 2 physical qubits, got {initial_layout}")

    # Transpile to hardware coupling map preserving SWAP gates
    routed_qc = transpile(
        bell_circuit,
        coupling_map=coupling_map,
        initial_layout=initial_layout,
        routing_method=routing_method,
        optimization_level=optimization_level,
        seed_transpiler=seed,
    )

    # Determine final physical locations of logical qubits 0 and 1
    if hasattr(routed_qc.layout, "final_index_layout"):
        final_indices = routed_qc.layout.final_index_layout()
        final_pair = (final_indices[0], final_indices[1])
    else:
        # Fallback if final_index_layout is not available
        final_pair = (initial_layout[0], initial_layout[1])

    # Operations in routed circuit
    ops_routed = routed_qc.count_ops()
    swap_count = ops_routed.get("swap", 0)

    # Two-qubit depth of the routed circuit (treating SWAP as 2-qubit operation)
    depth_2q_routed = routed_qc.depth(
        filter_function=lambda inst: inst.operation.num_qubits == 2
    )
    total_depth_routed = routed_qc.depth()

    # Decompose SWAP gates into native CX gates (each SWAP -> 3 CX)
    # This preserves the exact physical qubit routing without re-running layout
    native_qc = routed_qc.decompose("swap") if swap_count > 0 else routed_qc.copy()
    ops_native = native_qc.count_ops()
    native_cx_count = ops_native.get("cx", 0)
    depth_2q_native = native_qc.depth(
        filter_function=lambda inst: inst.operation.num_qubits == 2
    )
    total_depth_native = native_qc.depth()

    return RoutingResult(
        routed_circuit=routed_qc,
        native_circuit=native_qc,
        initial_layout=list(initial_layout),
        final_physical_qubits=final_pair,
        swap_count=swap_count,
        native_cx_count=native_cx_count,
        depth_2q_routed=depth_2q_routed,
        depth_2q_native=depth_2q_native,
        total_depth_routed=total_depth_routed,
        total_depth_native=total_depth_native,
    )
