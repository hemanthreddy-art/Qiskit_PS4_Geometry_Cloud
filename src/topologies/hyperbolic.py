r"""
Finite Hyperbolic-inspired topology model.

SCIENTIFIC / HARDWARE DISCLAIMER:
---------------------------------
This module models a finite, reproducible quantum coupling graph inspired by
hyperbolic tessellations and non-Euclidean connectivity (Poincaré disk model).
All experiments are executed on local classical simulators using Qiskit Aer.
This model DOES NOT represent a currently available physical quantum processor,
but rather evaluates theoretical non-Euclidean quantum cloud architectures.

GEOMETRIC & ARCHITECTURAL PROPERTIES:
-------------------------------------
1. Negative Gaussian Curvature (K < 0):
   In hyperbolic geometry, the circumference and area of a disc grow exponentially
   with radius: C(r) = 2*pi*sinh(r) ~ e^r.
   On a discrete graph, this corresponds to an exponential expansion of available
   nodes with graph distance from the bulk center.
2. Finite Graph Diameter & Geodesics:
   In this finite 21-node patch, concentric branching gives a small diameter (4 hops).
   Remote qubits across opposite sides of the boundary can communicate via geodesics
   that cut through the central bulk. (Note: Asymptotic scaling across varying graph
   sizes N is an active theoretical research topic and is not claimed from this single
   finite benchmark instance).
3. Trade-off:
   Achieving this tree-like hyperbolic connectivity in physical planar superconducting
   circuits requires 3D multi-layer interconnects or through-silicon vias (TSVs) to
   prevent planar wire-crossing crosstalk.
"""

import math
from typing import List, Tuple, Dict, Any, Optional
import rustworkx as rx
from qiskit.transpiler import CouplingMap


class HyperbolicTopology:
    """
    Represents a 21-qubit finite hyperbolic-inspired coupling architecture
    constructed as a 2-shell Poincaré disk patch.
    """

    def __init__(
        self,
        num_shell1: int = 5,
        children_per_node: int = 3,
        remote_pair: Optional[Tuple[int, int]] = (6, 13),
    ):
        """
        Initialize the finite Hyperbolic topology.

        Parameters:
            num_shell1: Number of nodes in intermediate shell 1 (default: 5).
            children_per_node: Branching factor from shell 1 to shell 2 (default: 3).
            remote_pair: Default remote physical qubit pair across the boundary (default: (6, 13)).
        """
        self.num_shell1 = num_shell1
        self.children_per_node = children_per_node
        self.name = "finite_hyperbolic_poincare_21q"

        # Build node indices:
        # Node 0: Bulk center (Shell 0)
        # Nodes 1..num_shell1: Shell 1
        # Nodes (num_shell1 + 1) .. (num_shell1 + num_shell1 * children): Shell 2
        self.num_shell2 = self.num_shell1 * self.children_per_node
        self.num_qubits = 1 + self.num_shell1 + self.num_shell2

        self._undirected_edges: List[Tuple[int, int]] = []
        self._build_hyperbolic_edges()

        # Remote pair default: opposite boundary nodes across the Poincaré disk
        self._remote_pair = tuple(remote_pair) if remote_pair is not None else (6, 13)

        # Build bidirectional edges for Qiskit CouplingMap
        self.directed_edges: List[List[int]] = []
        for u, v in self._undirected_edges:
            self.directed_edges.append([u, v])
            self.directed_edges.append([v, u])

        self.coupling_map = CouplingMap(self.directed_edges)

        # Build rustworkx graph for topological analysis
        self._rx_graph = rx.PyGraph()
        self._rx_graph.add_nodes_from(range(self.num_qubits))
        for u, v in self._undirected_edges:
            self._rx_graph.add_edge(u, v, None)

        self.description = (
            f"Finite Hyperbolic-inspired {self.num_qubits}-qubit topology (Poincaré disk patch): "
            "Negative-curvature concentric tessellation with exponential branch expansion, "
            "providing ultra-short geodesic routing paths through the central bulk."
        )

    def _build_hyperbolic_edges(self):
        """Construct radial and lateral tessellation edges."""
        edges_set = set()

        # 1. Radial edges: Shell 0 (Center 0) -> Shell 1 (1..5)
        for i in range(1, self.num_shell1 + 1):
            edges_set.add(tuple(sorted((0, i))))

        # 2. Lateral ring edges within Shell 1
        for i in range(1, self.num_shell1 + 1):
            next_i = 1 if i == self.num_shell1 else i + 1
            edges_set.add(tuple(sorted((i, next_i))))

        # 3. Branching radial edges: Shell 1 -> Shell 2
        shell2_start = self.num_shell1 + 1
        shell2_nodes = []
        for p_idx, parent in enumerate(range(1, self.num_shell1 + 1)):
            for c in range(self.children_per_node):
                child_id = shell2_start + p_idx * self.children_per_node + c
                edges_set.add(tuple(sorted((parent, child_id))))
                shell2_nodes.append(child_id)

        # 4. Lateral perimeter ring edges along Shell 2 (boundary cycle)
        total_s2 = len(shell2_nodes)
        for idx in range(total_s2):
            n1 = shell2_nodes[idx]
            n2 = shell2_nodes[(idx + 1) % total_s2]
            edges_set.add(tuple(sorted((n1, n2))))

        self._undirected_edges = sorted(list(edges_set))

    @property
    def undirected_edges(self) -> List[Tuple[int, int]]:
        """Return unique undirected edges."""
        return list(self._undirected_edges)

    def get_coupling_map(self) -> CouplingMap:
        """Return the Qiskit CouplingMap object."""
        return self.coupling_map

    def shortest_path(self, source: int, target: int) -> List[int]:
        """Compute the shortest path (list of node indices) between two physical qubits."""
        return self.coupling_map.shortest_undirected_path(source, target)

    def shortest_path_distance(self, source: int, target: int) -> int:
        """Compute the graph distance (number of edges/hops) between two physical qubits."""
        path = self.shortest_path(source, target)
        return len(path) - 1

    def get_remote_qubits(self) -> Tuple[int, int]:
        """Return designated remote physical qubit pair across the boundary."""
        return self._remote_pair

    def get_ancilla_qubits(self) -> Tuple[int, int]:
        """
        Return designated physical ancilla qubits for stabilizer syndrome checking.
        Physical qubits 1 and 3 are intermediate shell-1 nodes connecting boundary data qubits 6 and 13.
        """
        return (1, 3)

    def get_node_degree(self, node: int) -> int:
        """Return the degree of a specific node."""
        return self._rx_graph.degree(node)

    def get_max_degree(self) -> int:
        """Return maximum degree across all qubits."""
        return max(self.get_node_degree(i) for i in range(self.num_qubits))

    def get_diameter(self) -> int:
        """Return the graph diameter (4 hops)."""
        paths = rx.all_pairs_dijkstra_path_lengths(self._rx_graph, lambda _: 1)
        return int(max(paths[u][v] for u in range(self.num_qubits) for v in range(u + 1, self.num_qubits)))

    def get_layout_coordinates(self) -> Dict[int, Tuple[float, float]]:
        """
        Return exact Poincaré disk coordinates (x, y) with radius r < 1:
        x = r * cos(theta), y = r * sin(theta)
        """
        coords: Dict[int, Tuple[float, float]] = {}

        # Shell 0: origin
        coords[0] = (0.0, 0.0)

        # Shell 1: radius r1 = 0.45
        r1 = 0.45
        for i in range(1, self.num_shell1 + 1):
            angle = (2.0 * math.pi * (i - 1)) / self.num_shell1
            coords[i] = (round(r1 * math.cos(angle), 4), round(r1 * math.sin(angle), 4))

        # Shell 2: radius r2 = 0.82
        r2 = 0.82
        shell2_start = self.num_shell1 + 1
        total_s2 = self.num_shell2
        for idx in range(total_s2):
            node_id = shell2_start + idx
            angle = (2.0 * math.pi * idx) / total_s2
            coords[node_id] = (round(r2 * math.cos(angle), 4), round(r2 * math.sin(angle), 4))

        return coords

    def summary(self) -> Dict[str, Any]:
        """Return a dictionary summary of topology parameters."""
        remote_pair = self.get_remote_qubits()
        return {
            "name": self.name,
            "architecture_family": "Finite Hyperbolic (Poincaré Disk Patch)",
            "num_qubits": self.num_qubits,
            "num_edges": len(self._undirected_edges),
            "max_degree": self.get_max_degree(),
            "graph_diameter": self.get_diameter(),
            "undirected_edges": self._undirected_edges,
            "remote_qubits": list(remote_pair),
            "remote_qubit_distance": self.shortest_path_distance(*remote_pair),
            "description": self.description,
            "hardware_nature": "SIMULATED_AER_HARDWARE (Model inspired by hyperbolic tessellations)",
        }
