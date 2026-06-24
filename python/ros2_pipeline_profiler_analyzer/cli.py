import argparse
import sys
from pathlib import Path

from .reader import read_profiler_logs
from .analyzer import analyze, save_results, load_results
from .visualizer import generate_report
from .comparator import generate_comparison_report
from .heatmap import generate_heatmap_report


def _run_analyze(args):
    print(f"Reading logs from {args.log_dir}...")
    df = read_profiler_logs(args.log_dir)
    print(f"Loaded {len(df)} events from {df['source_file'].nunique()} nodes")

    print("Analyzing...")
    results = analyze(df)

    if args.rmw_label:
        results["rmw_label"] = args.rmw_label

    summary = results.get("summary", {})
    if "e2e" in summary:
        e = summary["e2e"]
        print(f"End-to-end: p50={e['p50_ms']:.2f}ms, p90={e['p90_ms']:.2f}ms, "
              f"p99={e['p99_ms']:.2f}ms, mean={e['mean_ms']:.2f}ms")
    for name, stats in summary.items():
        if name != "e2e":
            print(f"  {name}: p50={stats['p50_ms']:.2f}ms, p90={stats['p90_ms']:.2f}ms")

    drops = results.get("drops", [])
    if drops:
        print(f"\nDetected {len(drops)} drop events:")
        for d in drops:
            if d.get("type") == "cross_node_drop":
                print(f"  [{d['topic']}] {d['count']} messages published but never received "
                      f"(publisher={d['publisher_files']}, subscriber={d['subscriber_files']})")
            else:
                print(f"  {d['source_file']}: gap {d['from_id']} → {d['to_id']} ({d['count']} dropped)")

    if args.save_results:
        save_results(results, args.save_results)
        print(f"Saved results to {args.save_results}")

    print(f"\nGenerating report → {args.output}...")
    generate_report(results, args.output, args.pipeline_name)
    print("Done.")


def _run_compare(args):
    labels = [l.strip() for l in args.labels.split(",")] if args.labels else None
    result_paths = [Path(p) for p in args.results]

    if labels and len(labels) != len(result_paths):
        print(f"Error: got {len(labels)} labels but {len(result_paths)} result files")
        sys.exit(1)

    results_list = []
    for i, rp in enumerate(result_paths):
        results_list.append(load_results(str(rp)))
        if labels:
            results_list[-1]["rmw_label"] = labels[i]

    print(f"Loaded {len(results_list)} result sets, generating comparison...")
    generate_comparison_report(results_list, args.output)
    print(f"Done → {args.output}")


def main():
    parser = argparse.ArgumentParser(description="ROS2 Pipeline Profiler Analyzer")
    subparsers = parser.add_subparsers(dest="command")

    analyze_parser = subparsers.add_parser("analyze", help="Run analysis on profiler CSVs")
    analyze_parser.add_argument("--log-dir", default=".",
                                help="Directory containing profiler CSV files (default: current dir)")
    analyze_parser.add_argument("--output", default="profiler_report.html",
                                help="Output HTML report path")
    analyze_parser.add_argument("--pipeline-name", default="",
                                help="Optional name for the report header")
    analyze_parser.add_argument("--rmw-label", default="",
                                help="RMW implementation label (e.g. fastrtps, cyclonedds)")
    analyze_parser.add_argument("--save-results", default="",
                                help="Path to save analysis results as JSON for later comparison")

    compare_parser = subparsers.add_parser("compare", help="Compare multiple analysis results")
    compare_parser.add_argument("--results", nargs="+", required=True,
                                help="Paths to result JSON files")
    compare_parser.add_argument("--labels", default="",
                                help="Comma-separated labels for each result file")
    compare_parser.add_argument("--output", default="compare_report.html",
                                help="Output comparison HTML report path")

    heatmap_parser = subparsers.add_parser("heatmap", help="Generate RMW × QoS heatmap")
    heatmap_parser.add_argument("--results-dir", required=True,
                                help="Directory containing benchmark results tree")
    heatmap_parser.add_argument("--output", default="qos_heatmap.html",
                                help="Output HTML heatmap path")

    args = parser.parse_args()

    if args.command == "compare":
        _run_compare(args)
    elif args.command == "heatmap":
        generate_heatmap_report(args.results_dir, args.output)
    else:
        _run_analyze(args)


if __name__ == "__main__":
    main()
