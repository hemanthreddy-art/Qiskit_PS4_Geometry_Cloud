"""
Multi-topology comparison pipeline for Checkpoint 2.
Coordinates rigorous, fair evaluation of:
1. 2016-inspired 5-qubit Star/T topology
2. Contemporary IBM-style 27-qubit Heavy-Hex topology
3. Finite 21-qubit Hyperbolic-inspired topology
"""

import json
import os
import sys
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

import qiskit
import qiskit_aer
from qiskit_aer import AerSimulator

from src.topologies.star_t import StarTTopology
from src.topologies.heavy_hex import HeavyHexTopology
from src.topologies.hyperbolic import HyperbolicTopology
from src.circuits.bell_state import create_bell_pair_circuit, append_pauli_measurement
from src.routing.transpiler import route_bell_circuit
from src.noise.noise_models import (
    NoiseConfiguration,
    build_depolarizing_noise_model,
)
from src.metrics.fidelity import (
    compute_pauli_expectation,
    compute_bell_fidelity,
    PauliMeasurementSummary,
)
from src.visualization.plots import (
    visualize_topology_graphs,
    plot_comparison_metrics,
)


def run_topology_experiment(
    topology: Any,
    remote_pair: tuple,
    shots: int = 20000,
    seed: int = 42,
    noise_cfg: Optional[NoiseConfiguration] = None,
) -> Dict[str, Any]:
    """
    Execute an isolated, reproducible Bell-state experiment on a specific topology.
    """
    if noise_cfg is None:
        noise_cfg = NoiseConfiguration(
            model_name="superconducting_baseline_transmon",
            p_1q=0.001,
            p_2q=0.015,
            p_readout=0.015,
        )

    # 1. Routing
    bell_circuit = create_bell_pair_circuit()
    coupling_map = topology.get_coupling_map()
    distance = topology.shortest_path_distance(*remote_pair)

    routing_result = route_bell_circuit(
        bell_circuit=bell_circuit,
        coupling_map=coupling_map,
        initial_layout=list(remote_pair),
        seed=seed,
    )

    # 2. Simulators
    ideal_sim = AerSimulator()
    noise_model = build_depolarizing_noise_model(noise_cfg)
    noisy_sim = AerSimulator(noise_model=noise_model)

    # 3. Measurements
    def execute_tomography(sim: AerSimulator) -> PauliMeasurementSummary:
        counts_dict = {}
        exp_dict = {}
        err_dict = {}
        for basis in ["XX", "YY", "ZZ"]:
            c = append_pauli_measurement(
                base_circuit=routing_result.native_circuit,
                basis=basis,
                qubits=routing_result.final_physical_qubits,
            )
            job = sim.run(c, shots=shots, seed_simulator=seed)
            counts = job.result().get_counts()
            counts_dict[basis] = counts
            exp, err = compute_pauli_expectation(counts, total_shots=shots)
            exp_dict[basis] = exp
            err_dict[basis] = err

        fid, fid_err = compute_bell_fidelity(
            exp_xx=exp_dict["XX"],
            exp_yy=exp_dict["YY"],
            exp_zz=exp_dict["ZZ"],
            std_err_xx=err_dict["XX"],
            std_err_yy=err_dict["YY"],
            std_err_zz=err_dict["ZZ"],
        )

        return PauliMeasurementSummary(
            shots=shots,
            counts_xx=counts_dict["XX"],
            counts_yy=counts_dict["YY"],
            counts_zz=counts_dict["ZZ"],
            exp_xx=exp_dict["XX"],
            exp_yy=exp_dict["YY"],
            exp_zz=exp_dict["ZZ"],
            fidelity=fid,
            std_err_xx=err_dict["XX"],
            std_err_yy=err_dict["YY"],
            std_err_zz=err_dict["ZZ"],
            std_err_fidelity=fid_err,
        )

    ideal_summary = execute_tomography(ideal_sim)
    noisy_summary = execute_tomography(noisy_sim)

    fid_drop = ideal_summary.fidelity - noisy_summary.fidelity
    rel_deg = (fid_drop / ideal_summary.fidelity * 100.0) if ideal_summary.fidelity > 0 else 0.0

    return {
        "topology": {
            "name": topology.name,
            "num_qubits": topology.num_qubits,
            "num_edges": len(topology.undirected_edges),
            "remote_qubits": list(remote_pair),
            "graph_distance_hops": distance,
            "description": topology.description,
        },
        "routing": {
            **routing_result.to_dict(),
        },
        "noise_model": noise_cfg.to_dict(),
        "measurements": {
            "shots_per_basis": shots,
            "seed": seed,
            "ideal_baseline": ideal_summary.to_dict(),
            "noisy_baseline": noisy_summary.to_dict(),
        },
        "fidelity_comparison": {
            "ideal_fidelity": round(ideal_summary.fidelity, 6),
            "ideal_uncertainty": round(ideal_summary.std_err_fidelity, 6),
            "noisy_fidelity": round(noisy_summary.fidelity, 6),
            "noisy_uncertainty": round(noisy_summary.std_err_fidelity, 6),
            "fidelity_drop": round(fid_drop, 6),
            "relative_degradation_percent": round(rel_deg, 2),
        },
    }


def run_all_topologies_comparison(
    shots: int = 20000,
    seed: int = 42,
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run the end-to-end experiment across all three architectures with identical parameters.

    Parameters:
        shots: Shots per Pauli measurement basis.
        seed: Random seed for routing and Aer simulation.
        output_dir: Root results directory.

    Returns:
        Dict[str, Any]: Comprehensive comparison dictionary.
    """
    start_time = datetime.now(timezone.utc).isoformat()

    # Instantiate all 3 topologies
    star_t = StarTTopology(variant="t")
    heavy_hex = HeavyHexTopology(remote_pair=(0, 14))
    hyperbolic = HyperbolicTopology(remote_pair=(6, 13))

    topologies = [star_t, heavy_hex, hyperbolic]

    # Shared noise model configuration
    noise_cfg = NoiseConfiguration(
        model_name="superconducting_baseline_transmon",
        p_1q=0.001,
        p_2q=0.015,
        p_readout=0.015,
    )

    results_by_topology = []
    for topo in topologies:
        remote_pair = topo.get_remote_qubits()
        res = run_topology_experiment(
            topology=topo,
            remote_pair=remote_pair,
            shots=shots,
            seed=seed,
            noise_cfg=noise_cfg,
        )
        results_by_topology.append(res)

    # Determine directories
    if output_dir is None:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(project_root, "results")

    figures_dir = os.path.join(output_dir, "figures")
    os.makedirs(figures_dir, exist_ok=True)

    # Generate figures
    topo_fig_path = os.path.join(figures_dir, "topology_graphs.png")
    visualize_topology_graphs(topologies, topo_fig_path)

    metric_figs = plot_comparison_metrics(results_by_topology, figures_dir)
    metric_figs["topology_graphs"] = topo_fig_path

    # Structured comparison report
    full_report = {
        "metadata": {
            "checkpoint": "CHECKPOINT_2",
            "problem_statement": "PS4 - Geometry-Aware Quantum Cloud: Routing, Noise, and Architecture Comparison",
            "timestamp_utc": start_time,
            "qiskit_version": qiskit.__version__,
            "qiskit_aer_version": qiskit_aer.__version__,
            "python_version": sys.version.split()[0],
            "hardware_nature": "SIMULATED_AER_BENCHMARK (Explicitly distinguished from physical IBM hardware)",
            "scientific_fairness_protocol": (
                "Identical Bell-state circuit (|Phi+>), identical shot count (20000), "
                "identical noise parameters (p_1q=0.1%, p_2q=1.5%, p_ro=1.5%), "
                "identical Pauli basis tomography (XX, YY, ZZ), and identical seed (42) "
                "across all three topologies."
            ),
            "scientific_scope": (
                "Under the selected communication pairs, workload (|Phi+>), routing methodology (SABRE), "
                "and documented depolarizing noise model, routing metrics and fidelities reflect "
                "topology-constrained routing overhead for these specific tasks rather than universal architectural superiority."
            ),
        },
        "architectures": results_by_topology,
        "summary_table": [
            {
                "topology": r["topology"]["name"],
                "num_qubits": r["topology"]["num_qubits"],
                "selected_qubits": r["topology"]["remote_qubits"],
                "graph_distance": r["topology"]["graph_distance_hops"],
                "swap_count": r["routing"]["swap_count"],
                "native_two_qubit_gate_count": r["routing"]["native_cx_count"],
                "native_two_qubit_depth": r["routing"]["depth_2q_native"],
                "total_depth": r["routing"]["total_depth_native"],
                "XX": r["measurements"]["noisy_baseline"]["expectations"]["XX"],
                "YY": r["measurements"]["noisy_baseline"]["expectations"]["YY"],
                "ZZ": r["measurements"]["noisy_baseline"]["expectations"]["ZZ"],
                "ideal_fidelity": r["fidelity_comparison"]["ideal_fidelity"],
                "noisy_fidelity": r["fidelity_comparison"]["noisy_fidelity"],
                "fidelity_drop": r["fidelity_comparison"]["fidelity_drop"],
            }
            for r in results_by_topology
        ],
        "generated_figures": metric_figs,
    }

    # Save to JSON
    json_path = os.path.join(output_dir, "checkpoint2_architecture_comparison.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2)

    full_report["saved_to"] = json_path
    return full_report


def format_comparison_table(report: Dict[str, Any]) -> str:
    """Format comparison data into an ASCII presentation table."""
    table = report["summary_table"]
    meta = report["metadata"]

    lines = [
        "=" * 105,
        " IBM QISKIT FALL FEST 2026 - PS4 THREE-ARCHITECTURE COMPARISON REPORT (CHECKPOINT 2)",
        "=" * 105,
        f"Problem Statement : {meta['problem_statement']}",
        f"Software Env      : Qiskit {meta['qiskit_version']} | Qiskit Aer {meta['qiskit_aer_version']} | Python {meta['python_version']}",
        f"Hardware Nature   : {meta['hardware_nature']}",
        f"Fairness Protocol : {meta['scientific_fairness_protocol']}",
        f"Scientific Scope  : {meta.get('scientific_scope', 'N/A')}",
        "-" * 105,
        f"{'Topology':<24} | {'Qubits':<6} | {'Pair':<8} | {'Dist':<4} | {'SWAP':<4} | {'2Q CX':<5} | {'2Q Dep':<6} | {'Tot Dep':<7} | {'Ideal F':<7} | {'Noisy F':<7} | {'Drop':<6}",
        "-" * 105,
    ]

    label_map = {
        "2016_5qubit_T": "Star/T (Yorktown)",
        "contemporary_ibm_heavy_hex_27q": "Heavy-Hex (IBM Falcon)",
        "finite_hyperbolic_poincare_21q": "Hyperbolic (Poincare)",
    }

    for row in table:
        name = label_map.get(row["topology"], row["topology"])
        pair_str = f"{row['selected_qubits'][0]},{row['selected_qubits'][1]}"
        lines.append(
            f"{name:<24} | "
            f"{row['num_qubits']:<6} | "
            f"{pair_str:<8} | "
            f"{row['graph_distance']:<4} | "
            f"{row['swap_count']:<4} | "
            f"{row['native_two_qubit_gate_count']:<5} | "
            f"{row['native_two_qubit_depth']:<6} | "
            f"{row['total_depth']:<7} | "
            f"{row['ideal_fidelity']:<7.4f} | "
            f"{row['noisy_fidelity']:<7.4f} | "
            f"{row['fidelity_drop']:<6.4f}"
        )

    lines.extend([
        "-" * 105,
        "PAULI CORRELATION DETAIL (<XX>, <YY>, <ZZ>) FOR NOISY BASELINES:",
    ])

    for row in table:
        name = label_map.get(row["topology"], row["topology"])
        lines.append(
            f"  * {name:<22}: <XX> = {row['XX']:+.4f}, <YY> = {row['YY']:+.4f}, <ZZ> = {row['ZZ']:+.4f} "
            f"=> F = (1 + <XX> - <YY> + <ZZ>) / 4 = {row['noisy_fidelity']:.4f}"
        )

    lines.extend([
        "-" * 105,
        f"Machine-readable comparison saved to: {report.get('saved_to', 'N/A')}",
        "Generated comparison figures in:",
    ])
    for k, v in report["generated_figures"].items():
        lines.append(f"  - {k:<18}: {v}")
    lines.append("=" * 105)

    return "\n".join(lines)
