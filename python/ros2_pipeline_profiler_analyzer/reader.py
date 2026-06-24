from pathlib import Path

import pandas as pd


def read_profiler_logs(log_dir: str) -> pd.DataFrame:
    log_dir = Path(log_dir).expanduser()
    files = sorted(log_dir.glob("profiler_*.csv"))
    if not files:
        raise FileNotFoundError(f"No profiler CSV files found in {log_dir}")

    dfs = []
    for f in files:
        df = pd.read_csv(f)
        df["source_file"] = f.name
        dfs.append(df)

    result = pd.concat(dfs, ignore_index=True)
    if "sys_timestamp_ns" not in result.columns:
        result["sys_timestamp_ns"] = result["timestamp_ns"]
    result = result.sort_values("sys_timestamp_ns").reset_index(drop=True)
    return result
