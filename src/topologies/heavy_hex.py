r"""
Contemporary IBM-style Heavy-Hex topology model.

SCIENTIFIC / HARDWARE DISCLAIMER:
---------------------------------
This module models a finite, reproducible Heavy-Hex coupling graph inspired by
IBM Quantum's contemporary processor architectures (e.g., IBM Falcon/Montreal 27-qubit QPUs).
All simulations are executed on local classical simulators using Qiskit Aer noise models.
This model DOES NOT claim physical execution on a real IBM Quantum cryostat processor.

GEOMETRIC & ARCHITECTURAL PROPERTIES:
-------------------------------------
The Heavy-Hex lattice is designed specifically for superconducting transmon processors:
1. Low Vertex Degree:
   - "Corner/Code" qubits have degree at most 3.
   - "Edge/Bridge" qubits have degree 2 (or 1 at boundaries).
   - This low degree drastically suppresses frequency collision, parasitic ZZ crosstalk,
     and microwave routing congestion during multi-qubit gate operations.
2. Routing Trade-off:
   - The low degree and sparse connectivity mean non-adjacent qubits require significantly
     longer SWAP routing paths compared to higher-connectivity graphs.
   - Graph diameter is large (~12-15 hops across 27 qubits), resulting in cumulative gate noise.
"""

from typing import List, Tuple, Dict, Any, Optional
import rustworkx as rx
from qiskit.transpiler import CouplingMap


class HeavyHexTopology:
    """
    Represents an IBM-style 27-qubit Heavy-Hex coupling architecture.
    """

    # Canonical 28 undirected edges of the IBM 27-qubit Heavy-Hex lattice (Montreal/Falcon layout)
    CANONICAL_EDGES: List[Tuple[int, int]] = [
        (0, 1), (1, 2), (1, 4), (2, 3), (3, 5),
        (4, 7), (5, 8), (6, 7), (7, 10), (8, 9),
        (8, 11), (10, 12), (11, 14), (12, 13), (12, 15),
        (13, 14), (14, 16), (15, 18), (16, 19), (17, 18),
        (18, 21), (19, 20), (19, 22), (21, 23), (22, 25),
        (23, 24), (24, 25), (25, 26)
    ]

    def __init__(self, remote_pair: Optional[Tuple[int, int]] = (0, 14)):
        """
        Initialize the 27-qubit Heavy-Hex topology.

        Parameters:
            remote_pair: Default remote physical qubit pair for routing benchmarks (default: (0, 14)).
        """
        self.num_qubits = 27
        self.name = "contemporary_ibm_heavy_hex_27q"
        self._undirected_edges = list(self.CANONICAL_EDGES)
        self._remote_pair = tuple(remote_pair) if remote_pair is not None else (0, 14)

        # Build bidirectional edges for Qiskit CouplingMap
        self.directed_edges: List[List[int]] = []
        for u, v in self._undirected_edges:
            self.directed_edges.append([u, v])
            self.directed_edges.append([v, u])

        self.coupling_map = CouplingMap(self.directed_edges)

        # Build rustworkx graph for topological graph analysis
        self._rx_graph = rx.PyGraph()
        self._rx_graph.add_nodes_from(range(self.num_qubits))
        for u, v in self._undirected_edges:
            self._rx_graph.add_edge(u, v, None)

        self.description = (
            "Contemporary IBM-style 27-qubit Heavy-Hex topology (Falcon/Montreal architecture): "
            "Sparse hexagonal lattice with corner qubits (degree <= 3) and edge bridge qubits (degree 2), "
            "optimizing crosstalk suppression at the cost of increased routing path lengths."
        )

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
        """Return the designated reproducible remote physical qubit pair."""
        return self._remote_pair

    def get_ancilla_qubits(self) -> Tuple[int, int]:
        """
        Return designated physical ancilla qubits for stabilizer syndrome checking.
        Physical qubits 1 and 13 are immediate topological neighbors of remote data qubits 0 and 14.
        """
        return (1, 13)

    def get_node_degree(self, node: int) -> int:
        """Return the degree of a specific node."""
        return self._rx_graph.degree(node)

    def get_max_degree(self) -> int:
        """Return maximum degree across all qubits (3 in Heavy-Hex)."""
        return max(self.get_node_degree(i) for i in range(self.num_qubits))

    def get_diameter(self) -> int:
        """Return the diameter of the graph."""
        paths = rx.all_pairs_dijkstra_path_lengths(self._rx_graph, lambda _: 1)
        return int(max(paths[u][v] for u in range(self.num_qubits) for v in range(u + 1, self.num_qubits)))

    def get_layout_coordinates(self) -> Dict[int, Tuple[float, float]]:
        """
        Return 2D planar coordinates (x, y) for visualization matching
        the physical heavy-hex row/column structure.
        """
        # Canonical 2D grid coordinates for IBM 27Q Falcon layout
        coords = {
            0: (0.0, 4.0), 1: (1.0, 4.0), 2: (2.0, 4.0), 3: (3.0, 4.0), 5: (4.0, 4.0), 8: (5.0, 4.0), 9: (6.0, 4.0),
            4: (1.0, 3.0), 11: (5.0, 3.0),
            6: (0.0, 2.0), 7: (1.0, 2.0), 10: (2.0, 2.0), 12: (3.0, 2.0), 13: (4.0, 2.0), 14: (5.0, 2.0), 16: (6.0, 2.0),
            15: (3.0, 1.0), 19: (6.0, 1.0),
            17: (1.0, 0.0), 18: (2.0, 0.0), 21: (3.0, 0.0), 23: (4.0, 0.0), 24: (5.0, 0.0), 25: (6.0, 0.0), 26: (7.0, 0.0),
            20: (7.0, 1.0), 22: (6.0, 0.5),
        }
        # Fallback to spring layout for any missing node
        if len(coords) < self.num_qubits:
            spring = rx.spring_layout(self._rx_graph, seed=42)
            for i in range(self.num_qubits):
                if i not in coords:
                    coords[i] = (float(spring[i][0]), float(spring[i][1]))
        return coords

    def summary(self) -> Dict[str, Any]:
        """Return a dictionary summary of topology parameters."""
        remote_pair = self.get_remote_qubits()
        return {
            "name": self.name,
            "architecture_family": "Heavy-Hex (Contemporary IBM-style 27Q Subgraph)",
            "num_qubits": self.num_qubits,
            "num_edges": len(self._undirected_edges),
            "max_degree": self.get_max_degree(),
            "graph_diameter": self.get_diameter(),
            "undirected_edges": self._undirected_edges,
            "remote_qubits": list(remote_pair),
            "remote_qubit_distance": self.shortest_path_distance(*remote_pair),
            "description": self.description,
            "hardware_nature": "SIMULATED_AER_HARDWARE (Model inspired by IBM Heavy-Hex QPUs)",
        }


class HeavyHex127Topology:
    """
    Contemporary IBM-style 127-qubit Heavy-Hex reference architecture.

    SCIENTIFIC & ARCHITECTURAL DOCUMENTATION:
    -----------------------------------------
    This class models the full 127-qubit coupling map corresponding to IBM's Eagle
    processor family (e.g., FakeBrisbane / ibm_brisbane).
    - Qubit count: 127
    - Undirected coupling edges: 144
    - Vertex degree: <= 3 (low degree suppresses crosstalk and frequency collisions)
    - Graph diameter: 26 hops

    RELATIONSHIP TO BENCHMARK SUBGRAPH:
    -----------------------------------
    The 9-case empirical benchmark was evaluated on the 27-qubit HeavyHexTopology
    (Falcon layout), which forms a canonical unit cell / snippet of the 127-qubit lattice.
    This companion class provides the full 127-qubit reference graph for architectural
    comparison and topological scaling analysis.
    """

    # Canonical 144 undirected coupling edges of IBM Eagle 127Q (FakeBrisbane)
    CANONICAL_EDGES_127: List[Tuple[int, int]] = [
        (0, 1), (0, 14), (1, 2), (2, 3), (3, 4), (4, 5), (4, 15), (5, 6), (6, 7),
        (7, 8), (8, 9), (8, 16), (9, 10), (10, 11), (11, 12), (12, 13), (12, 17),
        (14, 18), (15, 22), (16, 26), (17, 30), (18, 19), (19, 20), (20, 21),
        (20, 33), (21, 22), (22, 23), (23, 24), (24, 25), (24, 34), (25, 26),
        (26, 27), (27, 28), (28, 29), (28, 35), (29, 30), (30, 31), (31, 32),
        (32, 36), (33, 39), (34, 43), (35, 47), (36, 51), (37, 38), (37, 52),
        (38, 39), (39, 40), (40, 41), (41, 42), (41, 53), (42, 43), (43, 44),
        (44, 45), (45, 46), (45, 54), (46, 47), (47, 48), (48, 49), (49, 50),
        (49, 55), (50, 51), (52, 56), (53, 60), (54, 64), (55, 68), (56, 57),
        (57, 58), (58, 59), (58, 71), (59, 60), (60, 61), (61, 62), (62, 63),
        (62, 72), (63, 64), (64, 65), (65, 66), (66, 67), (66, 73), (67, 68),
        (68, 69), (69, 70), (70, 74), (71, 77), (72, 81), (73, 85), (74, 89),
        (75, 76), (75, 90), (76, 77), (77, 78), (78, 79), (79, 80), (79, 91),
        (80, 81), (81, 82), (82, 83), (83, 84), (83, 92), (84, 85), (85, 86),
        (86, 87), (87, 88), (87, 93), (88, 89), (90, 94), (91, 98), (92, 102),
        (93, 106), (94, 95), (95, 96), (96, 97), (96, 109), (97, 98), (98, 99),
        (99, 100), (100, 101), (100, 110), (101, 102), (102, 103), (103, 104),
        (104, 105), (104, 111), (105, 106), (106, 107), (107, 108), (108, 112),
        (109, 114), (110, 118), (111, 122), (112, 126), (113, 114), (114, 115),
        (115, 116), (116, 117), (117, 118), (118, 119), (119, 120), (120, 121),
        (121, 122), (122, 123), (123, 124), (124, 125), (125, 126)
    ]

    def __init__(self, remote_pair: Optional[Tuple[int, int]] = (0, 126)):
        """Initialize the 127-qubit Heavy-Hex reference architecture."""
        self.num_qubits = 127
        self.name = "contemporary_ibm_heavy_hex_127q_reference"
        self._undirected_edges = list(self.CANONICAL_EDGES_127)
        self._remote_pair = tuple(remote_pair) if remote_pair is not None else (0, 126)

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
            "Contemporary IBM 127-qubit Heavy-Hex reference model (Eagle / FakeBrisbane architecture): "
            "Full-scale superconducting transmon lattice with 144 coupling edges, maximum vertex degree 3, "
            "and graph diameter 26 hops."
        )

    @property
    def undirected_edges(self) -> List[Tuple[int, int]]:
        """Return unique undirected edges."""
        return list(self._undirected_edges)

    def get_coupling_map(self) -> CouplingMap:
        """Return the Qiskit CouplingMap object."""
        return self.coupling_map

    def shortest_path(self, source: int, target: int) -> List[int]:
        """Compute shortest path between two physical qubits."""
        return self.coupling_map.shortest_undirected_path(source, target)

    def shortest_path_distance(self, source: int, target: int) -> int:
        """Compute shortest path distance."""
        path = self.shortest_path(source, target)
        return len(path) - 1

    def get_remote_qubits(self) -> Tuple[int, int]:
        """Return the designated remote physical qubit pair."""
        return self._remote_pair

    def get_node_degree(self, node: int) -> int:
        """Return the degree of a specific node."""
        return self._rx_graph.degree(node)

    def get_max_degree(self) -> int:
        """Return maximum degree across all qubits (3 in Heavy-Hex)."""
        return max(self.get_node_degree(i) for i in range(self.num_qubits))

    def get_diameter(self) -> int:
        """Return the diameter of the graph."""
        paths = rx.all_pairs_dijkstra_path_lengths(self._rx_graph, lambda _: 1)
        return int(max(paths[u][v] for u in range(self.num_qubits) for v in range(u + 1, self.num_qubits)))

    def get_layout_coordinates(self) -> Dict[int, Tuple[float, float]]:
        """
        Generate 2D layout coordinates for visualization.
        Uses spring layout with a fixed random seed for reproducible graph rendering.
        """
        spring = rx.spring_layout(self._rx_graph, seed=42)
        return {i: (float(spring[i][0]), float(spring[i][1])) for i in range(self.num_qubits)}

    def summary(self) -> Dict[str, Any]:
        """Return a dictionary summary of topology parameters."""
        remote_pair = self.get_remote_qubits()
        return {
            "name": self.name,
            "architecture_family": "Heavy-Hex (Contemporary IBM 127Q Eagle Reference)",
            "num_qubits": self.num_qubits,
            "num_edges": len(self._undirected_edges),
            "max_degree": self.get_max_degree(),
            "graph_diameter": self.get_diameter(),
            "undirected_edges": self._undirected_edges,
            "remote_qubits": list(remote_pair),
            "remote_qubit_distance": self.shortest_path_distance(*remote_pair),
            "description": self.description,
            "hardware_nature": "REFERENCE_TOPOLOGY_MODEL (IBM Eagle / FakeBrisbane Coupling Map)",
        }
