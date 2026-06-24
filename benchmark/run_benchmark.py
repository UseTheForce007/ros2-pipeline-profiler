#!/usr/bin/env python3
"""Run the pipeline profiler benchmark under multiple RMW implementations and QoS configurations."""

import argparse
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="ROS2 Pipeline Profiler Benchmark")
    parser.add_argument("--rmw-list", default="rmw_fastrtps_cpp,rmw_cyclonedds_cpp",
                        help="Comma-separated list of RMW implementations")
    parser.add_argument("--qos-list", default="reliable,best_effort",
                        help="Comma-separated list of QoS reliability settings")
    parser.add_argument("--depth-list", default="10,100",
                        help="Comma-separated list of QoS history depths")
    parser.add_argument("--trials", type=int, default=3,
                        help="Number of trials per config (default: 3)")
    parser.add_argument("--duration", type=int, default=30,
                        help="Duration per trial in seconds (default: 30)")
    parser.add_argument("--output-dir", default="benchmark_results",
                        help="Output directory (default: benchmark_results)")
    args = parser.parse_args()

    rmw_list = [r.strip() for r in args.rmw_list.split(",")]
    qos_list = [r.strip() for r in args.qos_list.split(",")]
    depth_list = [int(d.strip()) for d in args.depth_list.split(",")]

    base_dir = Path(args.output_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    all_results = []
    all_labels = []

    for rmw in rmw_list:
        for reliability in qos_list:
            for depth in depth_list:
                qos_label = f"{reliability}_depth_{depth}"
                print(f"\n{'='*60}")
                print(f"RMW: {rmw}  QoS: {qos_label}")
                print(f"{'='*60}")

                for trial in range(1, args.trials + 1):
                    label = f"{rmw}_{qos_label}_trial{trial}"
                    run_dir = base_dir / rmw / qos_label / f"run_{trial}"
                    run_dir.mkdir(parents=True, exist_ok=True)

                    print(f"  Trial {trial}/{args.trials} (duration={args.duration}s)...")

                    with tempfile.TemporaryDirectory() as tmpdir:
                        env = os.environ.copy()
                        env["RMW_IMPLEMENTATION"] = rmw

                        proc = subprocess.Popen(
                            ["ros2", "launch", "ros2_pipeline_profiler", "demo.launch.py",
                             f"reliability:={reliability}", f"depth:={depth}"],
                            env=env,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            cwd=tmpdir,
                            preexec_fn=os.setsid,
                        )

                        try:
                            time.sleep(args.duration)
                        except KeyboardInterrupt:
                            print("\nInterrupted, stopping...")
                            os.killpg(os.getpgid(proc.pid), signal.SIGINT)
                            proc.wait(timeout=10)
                            sys.exit(1)
                        finally:
                            os.killpg(os.getpgid(proc.pid), signal.SIGINT)
                            try:
                                proc.wait(timeout=10)
                            except subprocess.TimeoutExpired:
                                proc.kill()

                        for f in Path(tmpdir).glob("profiler_*.csv"):
                            shutil.move(str(f), str(run_dir / f.name))

                    csv_files = list(run_dir.glob("profiler_*.csv"))
                    if not csv_files:
                        print(f"  WARNING: no CSV files found for {label}")
                        continue

                    print(f"  Got {len(csv_files)} CSV files, analyzing...")

                    report_path = str(run_dir / "report.html")
                    results_path = str(run_dir / "results.json")

                    subprocess.run([
                        sys.executable, "-m", "ros2_pipeline_profiler_analyzer.cli", "analyze",
                        "--log-dir", str(run_dir),
                        "--output", report_path,
                        "--rmw-label", label,
                        "--save-results", results_path,
                    ], check=True)

                    all_results.append(results_path)
                    all_labels.append(label)

    # Generate comparison report (last QoS config only, for backward compat)
    print(f"\n{'='*60}")
    print("Generating RMW comparison report...")
    compare_path = str(base_dir / "compare_report.html")
    subprocess.run([
        sys.executable, "-m", "ros2_pipeline_profiler_analyzer.cli", "compare",
        "--results", *all_results,
        "--labels", ",".join(all_labels),
        "--output", compare_path,
    ], check=True)
    print(f"Comparison report → {compare_path}")

    # Generate heatmap
    print("\nGenerating QoS heatmap report...")
    heatmap_path = str(base_dir / "qos_heatmap.html")
    subprocess.run([
        sys.executable, "-m", "ros2_pipeline_profiler_analyzer.cli", "heatmap",
        "--results-dir", str(base_dir),
        "--output", heatmap_path,
    ], check=True)
    print(f"Heatmap → {heatmap_path}")

    print("\nDone.")


if __name__ == "__main__":
    main()
