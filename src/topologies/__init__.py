"""
Topologies module for IBM Qiskit Fall Fest 2026 PS4 project.
"""

from .star_t import StarTTopology
from .heavy_hex import HeavyHexTopology, HeavyHex127Topology
from .hyperbolic import HyperbolicTopology

SUPPORTED_TOPOLOGIES = {
    "star_t": StarTTopology,
    "heavy_hex": HeavyHexTopology,
    "heavy_hex_27": HeavyHexTopology,
    "hyperbolic": HyperbolicTopology,
    "heavy_hex_127": HeavyHex127Topology,
}


def get_topology(name: str, **kwargs):
    """
    Factory function to instantiate one of the architectures.

    Parameters:
        name: One of 'star_t', 'heavy_hex', 'hyperbolic', 'heavy_hex_127' (case-insensitive).
        **kwargs: Optional topology configuration parameters.

    Returns:
        Instance of StarTTopology, HeavyHexTopology, HeavyHex127Topology, or HyperbolicTopology.
    """
    key = name.lower()
    if key in {"star_t", "star", "t", "2016_star_t"}:
        return StarTTopology(**kwargs)
    elif key in {"heavy_hex", "heavyhex", "ibm_heavy_hex", "heavy_hex_27"}:
        return HeavyHexTopology(**kwargs)
    elif key in {"heavy_hex_127", "heavyhex127", "eagle_127", "brisbane_127"}:
        return HeavyHex127Topology(**kwargs)
    elif key in {"hyperbolic", "poincare", "finite_hyperbolic"}:
        return HyperbolicTopology(**kwargs)
    else:
        raise ValueError(
            f"Unknown topology '{name}'. Supported architectures: "
            f"{list(SUPPORTED_TOPOLOGIES.keys())}"
        )


__all__ = [
    "StarTTopology",
    "HeavyHexTopology",
    "HeavyHex127Topology",
    "HyperbolicTopology",
    "get_topology",
    "SUPPORTED_TOPOLOGIES",
]
