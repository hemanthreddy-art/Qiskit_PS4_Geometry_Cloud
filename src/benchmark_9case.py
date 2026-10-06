"""
Complete 9-Case Benchmark Engine:
3 Architectures (Star/T, Heavy-Hex, Hyperbolic) x 3 Conditions (Ideal, Noisy, Noisy+Protection).
"""

import json
import os
import sys
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

import qiskit
import qiskit_aer
from qiskit import QuantumCircuit, transpile
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
)
from src.protection.stabilizer_check import (
    build_protected_bell_circuit,
    classify_and_postselect_counts,
)
from src.protection.overhead import compute_protection_overhead


def run_single_condition_experiment(
    topology: Any,
    condition: str,
    shots: int = 20000,
    seed: int = 42,
    noise_cfg: Optional[NoiseConfiguration] = None,
) -> Dict[str, Any]:
    """
    Execute one benchmark case for a specific topology and condition.

    Parameters:
        topology: Topology instance.
        condition: 'ideal', 'noisy', or 'noisy_protection'.
        shots: Shots per measurement basis.
        seed: Random seed for routing and simulation.
        noise_cfg: NoiseConfiguration for noisy simulation.

    Returns:
        Dict[str, Any]: Complete metrics dictionary for this case.
    """
    cond_key = condition.lower()
    if cond_key not in {"ideal", "noisy", "noisy_protection"}:
        raise ValueError(f"Unknown condition '{condition}'. Must be 'ideal', 'noisy', or 'noisy_protection'.")

    if noise_cfg is None:
        noise_cfg = NoiseConfiguration(
            model_name="superconducting_baseline_transmon",
            p_1q=0.001,
            p_2q=0.015,
            p_readout=0.015,
        )

    remote_pair = list(topology.get_remote_qubits())
    dist = topology.shortest_path_distance(*remote_pair)
    cmap = topology.get_coupling_map()

    # Determine simulator backend
    if cond_key == "ideal":
        sim = AerSimulator()
    else:
        noise_model = build_depolarizing_noise_model(noise_cfg)
        sim = AerSimulator(noise_model=noise_model)

    # -------------------------------------------------------------
    # Case Type A: Unprotected (Ideal or Noisy)
    # -------------------------------------------------------------
    if cond_key in {"ideal", "noisy"}:
        bell_qc = create_bell_pair_circuit()
        routing_res = route_bell_circuit(
            bell_circuit=bell_qc,
            coupling_map=cmap,
            initial_layout=remote_pair,
            seed=seed,
        )

        counts_dict = {}
        exp_dict = {}
        err_dict = {}

        for basis in ["XX", "YY", "ZZ"]:
            meas_qc = append_pauli_measurement(
                base_circuit=routing_res.native_circuit,
                basis=basis,
                qubits=routing_res.final_physical_qubits,
            )
            job = sim.run(meas_qc, shots=shots, seed_simulator=seed)
            raw_counts = job.result().get_counts()
            counts_dict[basis] = raw_counts
            exp, err = compute_pauli_expectation(raw_counts, total_shots=shots)
            exp_dict[basis] = exp
            err_dict[basis] = err

        fid, fid_err = compute_bell_fidelity(
            exp_dict["XX"], exp_dict["YY"], exp_dict["ZZ"],
            err_dict["XX"], err_dict["YY"], err_dict["ZZ"],
        )

        return {
            "topology": topology.name,
            "condition": cond_key,
            "selected_physical_qubits": remote_pair,
            "graph_distance": dist,
            "swap_count": routing_res.swap_count,
            "native_two_qubit_gate_count": routing_res.native_cx_count,
            "native_two_qubit_depth": routing_res.depth_2q_native,
            "total_circuit_depth": routing_res.total_depth_native,
            "total_shots": shots,
            "accepted_shots": shots,
            "rejected_shots": 0,
            "survival_yield": 1.0,
            "XX": round(exp_dict["XX"], 6),
            "YY": round(exp_dict["YY"], 6),
            "ZZ": round(exp_dict["ZZ"], 6),
            "sigma_XX": round(err_dict["XX"], 6),
            "sigma_YY": round(err_dict["YY"], 6),
            "sigma_ZZ": round(err_dict["ZZ"], 6),
            "bell_fidelity": round(fid, 6),
            "sigma_fidelity": round(fid_err, 6),
            "counts": counts_dict,
        }

    # -------------------------------------------------------------
    # Case Type B: Noisy + Protection (Stabilizer Checking & Post-Selection)
    # -------------------------------------------------------------
    ancilla_pair = list(topology.get_ancilla_qubits())
    full_layout = remote_pair + ancilla_pair

    # Extract routing metrics from actual transpiled circuit
    test_qc = build_protected_bell_circuit("ZZ")
    tqc_routed = transpile(
        test_qc,
        coupling_map=cmap,
        initial_layout=full_layout,
        routing_method="sabre",
        seed_transpiler=seed,
    )
    tqc_native = tqc_routed.decompose("swap")
    swaps = tqc_routed.count_ops().get("swap", 0)
    native_cxs = tqc_native.count_ops().get("cx", 0)
    depth_2q = tqc_native.depth(filter_function=lambda inst: inst.operation.num_qubits == 2)
    tot_depth = tqc_native.depth()

    exp_dict = {}
    err_dict = {}
    accepted_counts_dict = {}
    raw_counts_dict = {}
    total_accepted_across_bases = 0
    total_rejected_across_bases = 0

    for basis in ["XX", "YY", "ZZ"]:
        circuit = build_protected_bell_circuit(basis)
        tqc_b = transpile(
            circuit,
            coupling_map=cmap,
            initial_layout=full_layout,
            routing_method="sabre",
            seed_transpiler=seed,
        )
        tqc_b_native = tqc_b.decompose("swap")

        job = sim.run(tqc_b_native, shots=shots, seed_simulator=seed)
        raw_c = job.result().get_counts()
        raw_counts_dict[basis] = raw_c

        acc_counts, acc_shots, rej_shots, _ = classify_and_postselect_counts(raw_c)
        accepted_counts_dict[basis] = acc_counts
        total_accepted_across_bases += acc_shots
        total_rejected_across_bases += rej_shots

        exp, err = compute_pauli_expectation(acc_counts, total_shots=acc_shots)
        exp_dict[basis] = exp
        err_dict[basis] = err

    fid, fid_err = compute_bell_fidelity(
        exp_dict["XX"], exp_dict["YY"], exp_dict["ZZ"],
        err_dict["XX"], err_dict["YY"], err_dict["ZZ"],
    )

    total_shots_all = total_accepted_across_bases + total_rejected_across_bases
    avg_yield = (total_accepted_across_bases / total_shots_all) if total_shots_all > 0 else 0.0

    return {
        "topology": topology.name,
        "condition": cond_key,
        "selected_physical_qubits": remote_pair,
        "ancilla_physical_qubits": ancilla_pair,
        "initial_layout": full_layout,
        "graph_distance": dist,
        "swap_count": swaps,
        "native_two_qubit_gate_count": native_cxs,
        "native_two_qubit_depth": depth_2q,
        "total_circuit_depth": tot_depth,
        "total_shots": shots,
        "total_shots_all_bases": total_shots_all,
        "accepted_shots": total_accepted_across_bases,
        "rejected_shots": total_rejected_across_bases,
        "survival_yield": round(avg_yield, 6),
        "survival_yield_percent": round(avg_yield * 100.0, 2),
        "XX": round(exp_dict["XX"], 6),
        "YY": round(exp_dict["YY"], 6),
        "ZZ": round(exp_dict["ZZ"], 6),
        "sigma_XX": round(err_dict["XX"], 6),
        "sigma_YY": round(err_dict["YY"], 6),
        "sigma_ZZ": round(err_dict["ZZ"], 6),
        "bell_fidelity": round(fid, 6),
        "sigma_fidelity": round(fid_err, 6),
        "raw_counts": raw_counts_dict,
        "accepted_counts": accepted_counts_dict,
    }


def run_full_9case_benchmark(
    shots: int = 20000,
    seed: int = 42,
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute the complete 9-case benchmark matrix:
    3 Topologies x 3 Conditions = 9 cases.

    Parameters:
        shots: Shots per measurement basis.
        seed: Random seed.
        output_dir: Output directory for JSON and figures.

    Returns:
        Dict[str, Any]: Comprehensive benchmark dataset.
    """
    start_time = datetime.now(timezone.utc).isoformat()

    topologies = [
        StarTTopology(variant="t"),
        HeavyHexTopology(remote_pair=(0, 14)),
        HyperbolicTopology(remote_pair=(6, 13)),
    ]

    conditions = ["ideal", "noisy", "noisy_protection"]

    noise_cfg = NoiseConfiguration(
        model_name="superconducting_baseline_transmon",
        p_1q=0.001,
        p_2q=0.015,
        p_readout=0.015,
    )

    all_cases: List[Dict[str, Any]] = []
    cases_by_topology: Dict[str, Dict[str, Any]] = {}

    for topo in topologies:
        cases_by_topology[topo.name] = {}
        for cond in conditions:
            case_data = run_single_condition_experiment(
                topology=topo,
                condition=cond,
                shots=shots,
                seed=seed,
                noise_cfg=noise_cfg,
            )
            all_cases.append(case_data)
            cases_by_topology[topo.name][cond] = case_data

    # Compute comparative protection metrics for each topology
    protection_analysis: Dict[str, Any] = {}
    for topo in topologies:
        name = topo.name
        noisy_case = cases_by_topology[name]["noisy"]
        prot_case = cases_by_topology[name]["noisy_protection"]

        f_noisy = noisy_case["bell_fidelity"]
        f_prot = prot_case["bell_fidelity"]
        fid_imp = round(f_prot - f_noisy, 6)
        rel_imp_pct = round((fid_imp / f_noisy * 100.0), 2) if f_noisy > 0 else 0.0

        # Protection overhead
        overhead = compute_protection_overhead(
            baseline_routing={
                "swap_count": noisy_case["swap_count"],
                "native_cx_count": noisy_case["native_two_qubit_gate_count"],
                "depth_2q_native": noisy_case["native_two_qubit_depth"],
                "total_depth_native": noisy_case["total_circuit_depth"],
            },
            protected_routing={
                "swap_count": prot_case["swap_count"],
                "native_cx_count": prot_case["native_two_qubit_gate_count"],
                "depth_2q_native": prot_case["native_two_qubit_depth"],
                "total_depth_native": prot_case["total_circuit_depth"],
            },
            rejected_shots=prot_case["rejected_shots"],
            total_shots=prot_case["total_shots_all_bases"],
            survival_yield=prot_case["survival_yield"],
        )

        protection_analysis[name] = {
            "noisy_fidelity": f_noisy,
            "protected_fidelity": f_prot,
            "fidelity_improvement": fid_imp,
            "relative_improvement_percent": rel_imp_pct,
            "accepted_shots": prot_case["accepted_shots"],
            "rejected_shots": prot_case["rejected_shots"],
            "survival_yield": prot_case["survival_yield"],
            "survival_yield_percent": prot_case["survival_yield_percent"],
            "overhead": overhead.to_dict(),
        }

    # Output paths
    if output_dir is None:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(project_root, "results")

    figures_dir = os.path.join(output_dir, "figures")
    os.makedirs(figures_dir, exist_ok=True)

    # Generate 8 required comparison figures
    from src.visualization.plots import generate_all_checkpoint3_figures
    generated_figures = generate_all_checkpoint3_figures(
        all_cases=all_cases,
        protection_analysis=protection_analysis,
        output_dir=figures_dir,
    )

    full_dataset = {
        "metadata": {
            "checkpoint": "CHECKPOINT_3",
            "problem_statement": "PS4 - Geometry-Aware Quantum Cloud: Routing, Noise, and Architecture Comparison",
            "timestamp_utc": start_time,
            "software_versions": {
                "qiskit": qiskit.__version__,
                "qiskit_aer": qiskit_aer.__version__,
                "python": sys.version.split()[0],
            },
            "scientific_scope": (
                "Under the selected Bell-state workload (|Phi+>), selected communication pairs, "
                "routing methodology (SABRE), shot budget (20000 per basis), and documented depolarizing transmon noise model, "
                "these metrics quantify routing overhead and the efficacy of stabilizer-based error detection with post-selection. "
                "This protocol performs error detection rather than full fault-tolerant quantum error correction."
            ),
            "hardware_nature": "SIMULATED_AER_BENCHMARK (Explicitly distinguished from physical IBM hardware)",
        },
        "noise_model": noise_cfg.to_dict(),
        "benchmark_cases": all_cases,
        "protection_analysis": protection_analysis,
        "generated_figures": generated_figures,
    }

    json_path = os.path.join(output_dir, "checkpoint3_9case_benchmark.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(full_dataset, f, indent=2)

    full_dataset["saved_to"] = json_path
    return full_dataset


def format_9case_summary_table(benchmark_data: Dict[str, Any]) -> str:
    """
    Format the complete 9-case benchmark into a professional ASCII presentation table.
    """
    cases = benchmark_data["benchmark_cases"]
    prot_analysis = benchmark_data["protection_analysis"]
    meta = benchmark_data["metadata"]

    lines = [
        "=" * 122,
        " IBM QISKIT FALL FEST 2026 - PS4 COMPLETE 9-CASE BENCHMARK REPORT (CHECKPOINT 3)",
        "=" * 122,
        f"Problem Statement : {meta['problem_statement']}",
        f"Software Env      : Qiskit {meta['software_versions']['qiskit']} | Qiskit Aer {meta['software_versions']['qiskit_aer']} | Python {meta['software_versions']['python']}",
        f"Hardware Nature   : {meta['hardware_nature']}",
        f"Scientific Scope  : {meta['scientific_scope']}",
        "-" * 122,
        f"{'Case':<4} | {'Topology':<22} | {'Condition':<17} | {'Pair':<7} | {'SWAP':<4} | {'2Q CX':<5} | {'2Q Dep':<6} | {'Tot Dep':<7} | {'Yield %':<7} | {'<XX>':<7} | {'<YY>':<7} | {'<ZZ>':<7} | {'Fidelity':<8}",
        "-" * 122,
    ]

    label_map = {
        "2016_5qubit_T": "Star/T (Yorktown)",
        "contemporary_ibm_heavy_hex_27q": "Heavy-Hex (Falcon)",
        "finite_hyperbolic_poincare_21q": "Hyperbolic (Poincare)",
    }

    cond_label = {
        "ideal": "Ideal",
        "noisy": "Noisy",
        "noisy_protection": "Noisy+Protected",
    }

    for idx, c in enumerate(cases, 1):
        name = label_map.get(c["topology"], c["topology"])
        c_name = cond_label.get(c["condition"], c["condition"])
        pair_str = f"{c['selected_physical_qubits'][0]},{c['selected_physical_qubits'][1]}"
        yield_str = f"{c['survival_yield']*100:.1f}%" if c["condition"] == "noisy_protection" else "100.0%"

        lines.append(
            f"{idx:<4} | "
            f"{name:<22} | "
            f"{c_name:<17} | "
            f"{pair_str:<7} | "
            f"{c['swap_count']:<4} | "
            f"{c['native_two_qubit_gate_count']:<5} | "
            f"{c['native_two_qubit_depth']:<6} | "
            f"{c['total_circuit_depth']:<7} | "
            f"{yield_str:<7} | "
            f"{c['XX']:<+7.4f} | "
            f"{c['YY']:<+7.4f} | "
            f"{c['ZZ']:<+7.4f} | "
            f"{c['bell_fidelity']:<8.4f}"
        )

    lines.extend([
        "-" * 122,
        "STABILIZER ERROR-DETECTION & POST-SELECTION ANALYSIS (BY ARCHITECTURE):",
        "-" * 122,
    ])

    for topo_name, p in prot_analysis.items():
        name = label_map.get(topo_name, topo_name)
        ov = p["overhead"]["circuit_overhead"]
        lines.extend([
            f"  * {name}:",
            f"      Noisy Baseline Fidelity : {p['noisy_fidelity']:.4f}",
            f"      Protected Fidelity      : {p['protected_fidelity']:.4f}",
            f"      Fidelity Improvement    : +{p['fidelity_improvement']:.4f} (+{p['relative_improvement_percent']:.2f}% relative)",
            f"      Survival Yield          : {p['survival_yield_percent']:.2f}% (Accepted: {p['accepted_shots']:,} / Rejected: {p['rejected_shots']:,})",
            f"      Protection Overhead     : +{ov['additional_swaps']} SWAPs | +{ov['additional_native_cxs']} Native CXs | +{ov['additional_depth_2q']} 2Q Depth | +{ov['additional_measurements']} Syndrome Measurements",
            "",
        ])

    lines.extend([
        "-" * 122,
        f"Machine-readable 9-case dataset saved to: {benchmark_data.get('saved_to', 'N/A')}",
        "Generated figures in results/figures/:",
    ])
    for k, v in benchmark_data["generated_figures"].items():
        lines.append(f"  - {k:<25}: {v}")
    lines.append("=" * 122)

    return "\n".join(lines)
