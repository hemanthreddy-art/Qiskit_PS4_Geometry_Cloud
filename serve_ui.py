"""
serve_ui.py - Research Interface Web Server for IBM Qiskit Fall Fest 2026 PS4.

Serves the scientific research interface and exposes read-only REST endpoints
delivering actual verified experimental data from results/checkpoint3_9case_benchmark.json
and topology models from src/topologies/.
"""

import os
import sys
import json
import mimetypes
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any

from src.topologies import (
    StarTTopology,
    HeavyHexTopology,
    HeavyHex127Topology,
    HyperbolicTopology,
    get_topology,
)
from src.circuits.bell_state import create_bell_pair_circuit
from src.routing.transpiler import route_bell_circuit

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UI_DIR = os.path.join(BASE_DIR, "ui")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
FIGURES_DIR = os.path.join(RESULTS_DIR, "figures")
BENCHMARK_JSON_PATH = os.path.join(RESULTS_DIR, "checkpoint3_9case_benchmark.json")


def load_benchmark_data() -> Dict[str, Any]:
    """Load the machine-readable 9-case benchmark results JSON."""
    if not os.path.exists(BENCHMARK_JSON_PATH):
        raise FileNotFoundError(f"Benchmark results not found at {BENCHMARK_JSON_PATH}")
    with open(BENCHMARK_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def build_topologies_payload() -> Dict[str, Any]:
    """Extract graph structures, coordinates, and properties for all architectures."""
    star = StarTTopology()
    heavy_hex_27 = HeavyHexTopology()
    heavy_hex_127 = HeavyHex127Topology()
    hyperbolic = HyperbolicTopology()

    def serialize_topology(topo, remote_pair, ancillas=None):
        coords = topo.get_layout_coordinates()
        edges = [[int(u), int(v)] for u, v in topo.undirected_edges]
        dist = int(topo.shortest_path_distance(*remote_pair))
        path = [int(x) for x in topo.shortest_path(*remote_pair)]
        return {
            "name": topo.name,
            "architecture_family": topo.summary().get("architecture_family", ""),
            "num_qubits": int(topo.num_qubits),
            "num_edges": len(edges),
            "max_degree": int(topo.get_max_degree()),
            "diameter": int(topo.get_diameter()),
            "undirected_edges": edges,
            "remote_qubits": [int(x) for x in remote_pair],
            "ancilla_qubits": [int(x) for x in ancillas] if ancillas else [],
            "shortest_path": path,
            "shortest_path_distance": dist,
            "coordinates": {str(k): [float(v[0]), float(v[1])] for k, v in coords.items()},
            "description": topo.description,
        }

    return {
        "star_t": serialize_topology(star, star.get_remote_qubits(), star.get_ancilla_qubits()),
        "heavy_hex_27": serialize_topology(
            heavy_hex_27, heavy_hex_27.get_remote_qubits(), heavy_hex_27.get_ancilla_qubits()
        ),
        "heavy_hex_127": serialize_topology(
            heavy_hex_127, heavy_hex_127.get_remote_qubits()
        ),
        "hyperbolic": serialize_topology(
            hyperbolic, hyperbolic.get_remote_qubits(), hyperbolic.get_ancilla_qubits()
        ),
    }


class ResearchInterfaceHandler(SimpleHTTPRequestHandler):
    """Custom HTTP handler serving UI static assets and read-only REST APIs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=UI_DIR, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # REST API endpoints
        if path == "/api/benchmark-9case":
            self.send_json_response(load_benchmark_data())
            return
        elif path == "/api/topologies":
            self.send_json_response(build_topologies_payload())
            return
        elif path == "/api/route":
            query = parse_qs(parsed.query)
            topo_key = query.get("topology", ["star_t"])[0].lower()
            qa_str = query.get("qubit_a", [None])[0]
            qb_str = query.get("qubit_b", [None])[0]

            try:
                topo = get_topology(topo_key)
            except ValueError as e:
                self.send_json_response({"status": "error", "message": str(e)}, status_code=400)
                return

            num_qubits = topo.num_qubits
            default_pair = topo.get_remote_qubits()

            try:
                qa = int(qa_str) if qa_str is not None else default_pair[0]
                qb = int(qb_str) if qb_str is not None else default_pair[1]
            except ValueError:
                self.send_json_response({"status": "error", "message": "qubit_a and qubit_b must be integers"}, status_code=400)
                return

            if qa < 0 or qa >= num_qubits or qb < 0 or qb >= num_qubits:
                self.send_json_response(
                    {"status": "error", "message": f"Qubit index out of bounds [0, {num_qubits - 1}]"},
                    status_code=400
                )
                return

            if qa == qb:
                self.send_json_response(
                    {"status": "error", "message": "qubit_a and qubit_b must be distinct physical qubits"},
                    status_code=400
                )
                return

            # Execute live topology-constrained Qiskit SABRE routing
            cmap = topo.get_coupling_map()
            bell = create_bell_pair_circuit()
            routing_res = route_bell_circuit(bell, cmap, initial_layout=[qa, qb], seed=42)
            shortest_path = [int(x) for x in topo.shortest_path(qa, qb)]
            distance = int(topo.shortest_path_distance(qa, qb))

            # Check if this matches the official benchmark pair
            is_benchmark_pair = set([qa, qb]) == set(default_pair)
            benchmark_data = None
            if is_benchmark_pair:
                try:
                    bench_data = load_benchmark_data()
                    matching_cases = [
                        c for c in bench_data.get("benchmark_cases", [])
                        if set(c.get("selected_physical_qubits", [])) == set([qa, qb])
                    ]
                    if matching_cases:
                        ideal_case = next((c for c in matching_cases if c.get("condition") == "ideal"), None)
                        noisy_case = next((c for c in matching_cases if c.get("condition") == "noisy"), None)
                        protected_case = next((c for c in matching_cases if c.get("condition") == "noisy_protection"), None)
                        benchmark_data = {
                            "ideal_fidelity": ideal_case.get("bell_fidelity") if ideal_case else 1.0,
                            "noisy_fidelity": noisy_case.get("bell_fidelity") if noisy_case else None,
                            "protected_fidelity": protected_case.get("bell_fidelity") if protected_case else None,
                            "survival_yield_percent": protected_case.get("survival_yield_percent") if protected_case else None,
                            "accepted_shots": protected_case.get("accepted_shots") if protected_case else None,
                            "total_shots_all_bases": protected_case.get("total_shots_all_bases") if protected_case else None,
                        }
                except Exception:
                    benchmark_data = None

            response_payload = {
                "status": "success",
                "topology": topo_key,
                "topology_name": topo.name,
                "num_qubits": num_qubits,
                "qubit_a": qa,
                "qubit_b": qb,
                "graph_distance": distance,
                "shortest_path": shortest_path,
                "swap_count": int(routing_res.swap_count),
                "native_cx_count": int(routing_res.native_cx_count),
                "depth_2q_native": int(routing_res.depth_2q_native),
                "total_depth_native": int(routing_res.total_depth_native),
                "final_physical_qubits": [int(x) for x in routing_res.final_physical_qubits],
                "is_benchmark_pair": is_benchmark_pair,
                "benchmark_data": benchmark_data,
            }
            self.send_json_response(response_payload)
            return
        elif path == "/api/health":
            self.send_json_response({
                "status": "online",
                "system": "PS4 Geometry-Aware Quantum Cloud Research Platform",
                "checkpoint": "CHECKPOINT_4",
                "benchmark_file": os.path.basename(BENCHMARK_JSON_PATH),
                "benchmark_loaded": os.path.exists(BENCHMARK_JSON_PATH),
            })
            return

        # Serve static figures from results/figures/
        if path.startswith("/figures/"):
            filename = path.replace("/figures/", "")
            file_path = os.path.join(FIGURES_DIR, filename)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                self.serve_file(file_path)
                return
            else:
                self.send_error(404, f"Figure '{filename}' not found")
                return

        # Fallback to serving static UI assets
        super().do_GET()

    def send_json_response(self, data: Dict[str, Any], status_code: int = 200):
        """Helper to send JSON payloads with CORS and cache-control headers."""
        payload = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(payload)

    def serve_file(self, filepath: str):
        """Helper to serve arbitrary binary/text files with correct MIME type."""
        mime_type, _ = mimetypes.guess_type(filepath)
        if not mime_type:
            mime_type = "application/octet-stream"

        try:
            with open(filepath, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "public, max-age=3600")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Error reading file: {str(e)}")


def run_server(host: str = "127.0.0.1", port: int = 8000):
    """Start the research interface HTTP server."""
    server_address = (host, port)
    httpd = HTTPServer(server_address, ResearchInterfaceHandler)
    print(f"================================================================================")
    print(f" PS4 Research Platform - Quantum Architecture Benchmark Server")
    print(f"================================================================================")
    print(f" Local URL:   http://{host}:{port}/")
    print(f" API Data:    http://{host}:{port}/api/benchmark-9case")
    print(f" Topologies:  http://{host}:{port}/api/topologies")
    print(f" Health:      http://{host}:{port}/api/health")
    print(f" Serving UI:  {UI_DIR}")
    print(f" Press Ctrl+C to terminate.")
    print(f"================================================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server gracefully...")
        httpd.server_close()


if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port=port)
