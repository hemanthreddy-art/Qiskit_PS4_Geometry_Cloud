import argparse
import sys
from src.experiment import run_checkpoint1_experiment, format_experiment_report
from src.comparison import run_all_topologies_comparison, format_comparison_table
from src.benchmark_9case import run_full_9case_benchmark, format_9case_summary_table
from src.topologies import get_topology


def main():
    parser = argparse.ArgumentParser(
        description="Run PS4 Geometry-Aware Quantum Cloud Routing & Architecture Experiments"
    )
    parser.add_argument(
        "--benchmark-9case",
        action="store_true",
        help="Execute the complete 9-case benchmark matrix (3 topologies x 3 conditions)",
    )
    parser.add_argument(
        "--topology",
        choices=["star_t", "heavy_hex", "hyperbolic", "all"],
        default="all",
        help="Architecture to benchmark: 'star_t', 'heavy_hex', 'hyperbolic', or 'all' (default: all)",
    )
    parser.add_argument(
        "--variant",
        choices=["t", "star"],
        default="t",
        help="Variant for Star/T topology (default: 't')",
    )
    parser.add_argument(
        "--shots",
        type=int,
        default=20000,
        help="Number of shots per Pauli measurement basis (default: 20000)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic routing and Aer simulation (default: 42)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Custom directory to store results JSON (default: ./results)",
    )

    args = parser.parse_args()

    try:
        if args.benchmark_9case:
            results = run_full_9case_benchmark(
                shots=args.shots,
                seed=args.seed,
                output_dir=args.output_dir,
            )
            print(format_9case_summary_table(results))
        elif args.topology == "all":
            results = run_all_topologies_comparison(
                shots=args.shots,
                seed=args.seed,
                output_dir=args.output_dir,
            )
            print(format_comparison_table(results))
        elif args.topology == "star_t":
            results = run_checkpoint1_experiment(
                variant=args.variant,
                shots=args.shots,
                seed=args.seed,
                output_dir=args.output_dir,
            )
            print(format_experiment_report(results))
        else:
            # Single execution of heavy_hex or hyperbolic
            from src.comparison import run_topology_experiment
            topo = get_topology(args.topology)
            res = run_topology_experiment(
                topology=topo,
                remote_pair=topo.get_remote_qubits(),
                shots=args.shots,
                seed=args.seed,
            )
            print(f"Results for {topo.name}:")
            print(f"  Remote pair: {res['topology']['remote_qubits']} (Distance: {res['topology']['graph_distance_hops']} hops)")
            print(f"  SWAP count: {res['routing']['swap_count']}")
            print(f"  Native CX count: {res['routing']['native_cx_count']}")
            print(f"  Native 2Q depth: {res['routing']['depth_2q_native']}")
            print(f"  Ideal fidelity: {res['fidelity_comparison']['ideal_fidelity']:.4f}")
            print(f"  Noisy fidelity: {res['fidelity_comparison']['noisy_fidelity']:.4f}")
        sys.exit(0)
    except Exception as exc:
        print(f"Error executing experiment: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
