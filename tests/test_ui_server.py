"""
tests/test_ui_server.py - Tests for UI Server and API Data Endpoints.
"""

import os
import json
import urllib.request
import threading
from http.server import HTTPServer
import pytest

from serve_ui import (
    load_benchmark_data,
    build_topologies_payload,
    ResearchInterfaceHandler,
)


def test_load_benchmark_data():
    data = load_benchmark_data()
    assert "metadata" in data
    assert "noise_model" in data
    assert "benchmark_cases" in data
    assert len(data["benchmark_cases"]) == 9
    assert "protection_analysis" in data


def test_build_topologies_payload():
    topos = build_topologies_payload()
    assert "star_t" in topos
    assert "heavy_hex_27" in topos
    assert "heavy_hex_127" in topos
    assert "hyperbolic" in topos

    # Check 5-qubit Star/T
    assert topos["star_t"]["num_qubits"] == 5
    assert topos["star_t"]["num_edges"] == 4
    assert topos["star_t"]["remote_qubits"] == [0, 4]

    # Check 27-qubit Heavy-Hex Subgraph
    assert topos["heavy_hex_27"]["num_qubits"] == 27
    assert topos["heavy_hex_27"]["num_edges"] == 28
    assert topos["heavy_hex_27"]["max_degree"] == 3
    assert topos["heavy_hex_27"]["remote_qubits"] == [0, 14]

    # Check 127-qubit Heavy-Hex Reference
    assert topos["heavy_hex_127"]["num_qubits"] == 127
    assert topos["heavy_hex_127"]["num_edges"] == 144
    assert topos["heavy_hex_127"]["max_degree"] == 3
    assert topos["heavy_hex_127"]["diameter"] == 26

    # Check 21-qubit Hyperbolic
    assert topos["hyperbolic"]["num_qubits"] == 21
    assert topos["hyperbolic"]["num_edges"] == 40
    assert topos["hyperbolic"]["max_degree"] == 6
    assert topos["hyperbolic"]["remote_qubits"] == [6, 13]


def test_http_server_endpoints():
    """Integration test verifying HTTP server routes, static files, and JSON APIs."""
    # Spin up server on an ephemeral free port
    server = HTTPServer(("127.0.0.1", 0), ResearchInterfaceHandler)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{port}"

    try:
        # 1. Test Root HTML
        with urllib.request.urlopen(f"{base_url}/") as res:
            assert res.status == 200
            html = res.read().decode("utf-8")
            assert "Geometry-Aware Quantum Cloud" in html
            assert "PS4 RESEARCH PLATFORM" in html

        # 2. Test CSS and JS static assets
        with urllib.request.urlopen(f"{base_url}/css/styles.css") as res:
            assert res.status == 200
            css = res.read().decode("utf-8")
            assert "--accent-blue" in css

        with urllib.request.urlopen(f"{base_url}/js/app.js") as res:
            assert res.status == 200
            js = res.read().decode("utf-8")
            assert "renderBenchmarkTable" in js

        # 3. Test API Health
        with urllib.request.urlopen(f"{base_url}/api/health") as res:
            assert res.status == 200
            health_data = json.loads(res.read().decode("utf-8"))
            assert health_data["status"] == "online"
            assert health_data["benchmark_loaded"] is True

        # 4. Test API Benchmark 9-Case
        with urllib.request.urlopen(f"{base_url}/api/benchmark-9case") as res:
            assert res.status == 200
            bench_data = json.loads(res.read().decode("utf-8"))
            assert len(bench_data["benchmark_cases"]) == 9

        # 5. Test API Topologies
        with urllib.request.urlopen(f"{base_url}/api/topologies") as res:
            assert res.status == 200
            topos_data = json.loads(res.read().decode("utf-8"))
            assert "star_t" in topos_data
            assert "heavy_hex_27" in topos_data
            assert "heavy_hex_127" in topos_data
            assert "hyperbolic" in topos_data

        # 6. Test All 9 Publication Figures
        figures = [
            "benchmark_9case_dashboard.png",
            "bell_fidelity_by_topology.png",
            "fidelity_improvement_from_protection.png",
            "fidelity_vs_survival_tradeoff.png",
            "protection_overhead_comparison.png",
            "survival_yield_by_topology.png",
            "swap_count_by_topology.png",
            "native_two_qubit_depth_by_topology.png",
            "topology_graphs.png",
        ]
        for fig in figures:
            with urllib.request.urlopen(f"{base_url}/figures/{fig}") as res:
                assert res.status == 200
                content = res.read()
                assert len(content) > 1000, f"Figure {fig} is empty or too small"

        # 7. Test Live Routing API /api/route
        # 7a. Star/T default benchmark pair (0, 4)
        with urllib.request.urlopen(f"{base_url}/api/route?topology=star_t&qubit_a=0&qubit_b=4") as res:
            assert res.status == 200
            route_data = json.loads(res.read().decode("utf-8"))
            assert route_data["status"] == "success"
            assert route_data["graph_distance"] == 3
            assert route_data["swap_count"] == 2
            assert route_data["native_cx_count"] == 7
            assert route_data["shortest_path"] == [0, 2, 3, 4]
            assert route_data["is_benchmark_pair"] is True
            assert route_data["benchmark_data"]["noisy_fidelity"] is not None

        # 7b. Heavy-Hex direct neighbor (0, 1) -> 0 SWAPs, 1 CX
        with urllib.request.urlopen(f"{base_url}/api/route?topology=heavy_hex_27&qubit_a=0&qubit_b=1") as res:
            assert res.status == 200
            route_data = json.loads(res.read().decode("utf-8"))
            assert route_data["status"] == "success"
            assert route_data["graph_distance"] == 1
            assert route_data["swap_count"] == 0
            assert route_data["native_cx_count"] == 1
            assert route_data["shortest_path"] == [0, 1]
            assert route_data["is_benchmark_pair"] is False

        # 7c. Heavy-Hex max distance (0, 26) -> 12 hops, 11 SWAPs, 34 CX
        with urllib.request.urlopen(f"{base_url}/api/route?topology=heavy_hex_27&qubit_a=0&qubit_b=26") as res:
            assert res.status == 200
            route_data = json.loads(res.read().decode("utf-8"))
            assert route_data["status"] == "success"
            assert route_data["graph_distance"] == 12
            assert route_data["swap_count"] == 11
            assert route_data["native_cx_count"] == 34

        # 7d. Error on identical qubits
        try:
            urllib.request.urlopen(f"{base_url}/api/route?topology=star_t&qubit_a=2&qubit_b=2")
            pytest.fail("Expected HTTP 400 error for identical qubits")
        except urllib.error.HTTPError as e:
            assert e.code == 400
    finally:
        server.shutdown()
        server.server_close()
