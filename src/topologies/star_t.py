r"""
2016-inspired 5-qubit Star/T coupling graph implementation.

Context:
In 2016, IBM deployed early cloud-accessible superconducting transmon chips,
notably the 5-qubit IBM Quantum Experience processors (such as ibmqx2 / Yorktown).
These chips were characterized by asymmetric or branching connectivity:
a central junction/hub qubit with peripheral qubits forming a Star/T graph.

Graph Topology (Yorktown T layout):
       0       1
        \     /
           2  (Junction)
           |
           3
           |
           4  (Remote Leaf)

Direct connections (undirected):
(0, 2), (1, 2), (2, 3), (3, 4)

Maximum distance is between leaf qubit 0 (or 1) and leaf qubit 4:
Shortest path: 0 -> 2 -> 3 -> 4 (Graph distance = 3 hops).
Interactions between these remote qubits strictly require intermediate SWAP routing.
"""

from typing import List, Tuple, Dict
from qiskit.transpiler import CouplingMap


class StarTTopology:
    """
    Represents the 2016-inspired 5-qubit Star/T coupling architecture.
    """

    def __init__(self, variant: str = "t"):
        """
        Initialize the Star/T topology.

        Parameters:
            variant: "t" for the Yorktown T-branch graph (edges: 0-2, 1-2, 2-3, 3-4),
                     or "star" for pure star graph (center 2 connected to 0, 1, 3, 4).
        """
        self.variant = variant.lower()
        self.num_qubits = 5
        self.name = f"2016_5qubit_{self.variant.upper()}"

        if self.variant == "t":
            # Yorktown T-topology edges (undirected)
            self._undirected_edges = [(0, 2), (1, 2), (2, 3), (3, 4)]
            self.description = (
                "2016 IBM-inspired 5-qubit T-topology (Yorktown/ibmqx2 style): "
                "Hub at Q2 connected to wings Q0, Q1 and stem Q3; stem Q3 connects to leaf Q4."
            )
        elif self.variant == "star":
            # Pure star topology edges with central hub at qubit 2
            self._undirected_edges = [(2, 0), (2, 1), (2, 3), (2, 4)]
            self.description = (
                "2016 IBM-inspired 5-qubit pure Star topology: "
                "Central hub at Q2 connected directly to leaves Q0, Q1, Q3, Q4."
            )
        else:
            raise ValueError(f"Unknown Star/T variant '{variant}'. Must be 't' or 'star'.")

        # Build bidirectional edges for Qiskit CouplingMap
        self.directed_edges: List[List[int]] = []
        for u, v in self._undirected_edges:
            self.directed_edges.append([u, v])
            self.directed_edges.append([v, u])

        self.coupling_map = CouplingMap(self.directed_edges)

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
        """
        Return the physical qubit pair with the greatest graph distance.
        For T-topology, this is (0, 4) with distance 3.
        For Star-topology, this is (0, 4) with distance 2.
        """
        max_dist = -1
        best_pair = (0, 1)
        for i in range(self.num_qubits):
            for j in range(i + 1, self.num_qubits):
                dist = self.shortest_path_distance(i, j)
                if dist > max_dist:
                    max_dist = dist
                    best_pair = (i, j)
        return best_pair

    def get_ancilla_qubits(self) -> Tuple[int, int]:
        """
        Return designated physical ancilla qubits for stabilizer syndrome checking.
        Qubits 1 and 2 are adjacent to junction qubit 2.
        """
        return (1, 2)

    def get_max_degree(self) -> int:
        """Return maximum degree across all qubits (3 at junction node 2)."""
        degrees = [0] * self.num_qubits
        for u, v in self._undirected_edges:
            degrees[u] += 1
            degrees[v] += 1
        return max(degrees)

    def get_diameter(self) -> int:
        """Return the diameter of the graph (3 for T-topology)."""
        max_dist = 0
        for i in range(self.num_qubits):
            for j in range(i + 1, self.num_qubits):
                dist = self.shortest_path_distance(i, j)
                if dist > max_dist:
                    max_dist = dist
        return max_dist

    def get_layout_coordinates(self) -> Dict[int, Tuple[float, float]]:
        """Return 2D planar coordinates (x, y) for visualization of Yorktown T layout."""
        if self.variant == "t":
            return {
                0: (-1.0, 1.0),
                1: (1.0, 1.0),
                2: (0.0, 0.0),
                3: (0.0, -1.0),
                4: (0.0, -2.0),
            }
        else:
            return {
                2: (0.0, 0.0),
                0: (-1.0, 1.0),
                1: (1.0, 1.0),
                3: (-1.0, -1.0),
                4: (1.0, -1.0),
            }

    def summary(self) -> Dict:
        """Return a dictionary summary of topology parameters."""
        remote_pair = self.get_remote_qubits()
        return {
            "name": self.name,
            "architecture_family": f"2016-inspired 5-qubit {self.variant.upper()}",
            "variant": self.variant,
            "num_qubits": self.num_qubits,
            "num_edges": len(self._undirected_edges),
            "max_degree": self.get_max_degree(),
            "graph_diameter": self.get_diameter(),
            "undirected_edges": self._undirected_edges,
            "remote_qubits": list(remote_pair),
            "remote_qubit_distance": self.shortest_path_distance(*remote_pair),
            "description": self.description,
            "hardware_nature": "SIMULATED_AER_HARDWARE (Model inspired by 2016 IBM Yorktown)",
        }
