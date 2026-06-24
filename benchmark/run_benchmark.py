#!/usr/bin/env python3
"""Run the pipeline profiler benchmark under multiple RMW implementations."""

import argparse
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def _run_pipeline(duration: int, log_dir: str):
    """Launch the demo pipeline, wait, kill, return True on success."""
    env = os.environ.copy()
    env["RCUTILS_CONSOLE_OUTPUT_FORMAT"] = "[{name}] {message}"

    proc = subprocess.Popen(
        ["ros2", "launch", "ros2_pipeline_profiler", "demo.launch.py"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid,
    )

    try:
        time.sleep(duration)
    except KeyboardInterrupt:
        pass
    finally:
        os.killpg(os.getpgid(proc.pid), signal.SIGINT)
        proc.wait(timeout=10)

    # Copy CSVs to log_dir
    csv_dir = Path(log_dir)
    csv_dir.mkdir(parents=True, exist_ok=True)
    for f in Path(".").glob("profiler_*.csv"):
        shutil.move(str(f), str(csv_dir / f.name))

    return True


def _run_analyzer(csv_dir: str, output_html: str, results_json: str, rmw_label: str):
    env = os.environ.copy()
    cmd = [
        sys.executable, "-m", "ros2_pipeline_profiler_analyzer.cli", "analyze",
        "--log-dir", csv_dir,
        "--output", output_html,
        "--rmw-label", rmw_label,
        "--save-results", results_json,
    ]
    subprocess.run(cmd, env=env, check=True)


def _run_compare(result_paths: list, labels: list, output_html: str):
    env = os.environ.copy()
    cmd = [
        sys.executable, "-m", "ros2_pipeline_profiler_analyzer.cli", "compare",
        "--results", *result_paths,
        "--labels", ",".join(labels),
        "--output", output_html,
    ]
    subprocess.run(cmd, env=env, check=True)


def main():
    parser = argparse.ArgumentParser(description="ROS2 Pipeline Profiler Benchmark")
    parser.add_argument("--rmw-list", default="rmw_fastrtps_cpp,rmw_cyclonedds_cpp",
                        help="Comma-separated list of RMW implementations")
    parser.add_argument("--trials", type=int, default=3,
                        help="Number of trials per RMW (default: 3)")
    parser.add_argument("--duration", type=int, default=30,
                        help="Duration per trial in seconds (default: 30)")
    parser.add_argument("--output-dir", default="benchmark_results",
                        help="Output directory (default: benchmark_results)")
    args = parser.parse_args()

    rmw_list = [r.strip() for r in args.rmw_list.split(",")]
    base_dir = Path(args.output_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    all_results = []
    all_labels = []

    for rmw in rmw_list:
        print(f"\n{'='*60}")
        print(f"RMW: {rmw}")
        print(f"{'='*60}")

        for trial in range(1, args.trials + 1):
            label = f"{rmw} trial {trial}"
            run_dir = base_dir / rmw / f"run_{trial}"
            run_dir.mkdir(parents=True, exist_ok=True)

            print(f"  Trial {trial}/{args.trials} (duration={args.duration}s)...")

            with tempfile.TemporaryDirectory() as tmpdir:
                env = os.environ.copy()
                env["RMW_IMPLEMENTATION"] = rmw

                # Launch pipeline in tmpdir so CSVs land there
                proc = subprocess.Popen(
                    ["ros2", "launch", "ros2_pipeline_profiler", "demo.launch.py"],
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

                # Move CSVs to run_dir
                for f in Path(tmpdir).glob("profiler_*.csv"):
                    shutil.move(str(f), str(run_dir / f.name))

            # Verify we got CSVs
            csv_files = list(run_dir.glob("profiler_*.csv"))
            if not csv_files:
                print(f"  WARNING: no CSV files found for {rmw} trial {trial}")
                continue

            print(f"  Got {len(csv_files)} CSV files, analyzing...")

            report_path = str(run_dir / "report.html")
            results_path = str(run_dir / "results.json")

            analyzer_env = os.environ.copy()
            subprocess.run([
                sys.executable, "-m", "ros2_pipeline_profiler_analyzer.cli", "analyze",
                "--log-dir", str(run_dir),
                "--output", report_path,
                "--rmw-label", label,
                "--save-results", results_path,
            ], env=analyzer_env, check=True)

            all_results.append(results_path)
            all_labels.append(f"{rmw} trial {trial}")

    # Generate comparison report if we have results from multiple RMWs
    if len(set(all_labels)) > 1:
        print(f"\n{'='*60}")
        print("Generating comparison report...")
        compare_path = str(base_dir / "compare_report.html")
        _run_compare(all_results, all_labels, compare_path)
        print(f"Comparison report → {compare_path}")
    else:
        print("\nOnly one RMW tested, skipping comparison report.")

    print("\nDone.")


if __name__ == "__main__":
    main()
