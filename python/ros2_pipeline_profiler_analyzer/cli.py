import argparse
import sys

from .reader import read_profiler_logs
from .analyzer import analyze
from .visualizer import generate_report


def main():
    parser = argparse.ArgumentParser(description="ROS2 Pipeline Profiler Analyzer")
    parser.add_argument("--log-dir", default=".",
                        help="Directory containing profiler CSV files (default: current dir)")
    parser.add_argument("--output", default="profiler_report.html",
                        help="Output HTML report path")
    parser.add_argument("--pipeline-name", default="",
                        help="Optional name for the report header")
    args = parser.parse_args()

    print(f"Reading logs from {args.log_dir}...")
    df = read_profiler_logs(args.log_dir)
    print(f"Loaded {len(df)} events from {df['source_file'].nunique()} nodes")

    print("Analyzing...")
    results = analyze(df)

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
            print(f"  {d['source_file']}: gap {d['from_id']} → {d['to_id']} ({d['count']} dropped)")

    print(f"\nGenerating report → {args.output}...")
    generate_report(results, args.output, args.pipeline_name)
    print("Done.")


if __name__ == "__main__":
    main()
