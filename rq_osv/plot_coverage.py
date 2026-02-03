# -*- coding: utf-8 -*-
import re
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent

TIME_RE = re.compile(r"Elapsed Time\s*:\s*(\d+)h\s*(\d+)m\s*(\d+)s")
COV_RE = re.compile(r"Coverage\s*:\s*([0-9.]+)%")


def parse_log(path: Path):
    times = []
    covs = []
    current_time = None

    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            t = TIME_RE.search(line)
            if t:
                h, m, s = map(int, t.groups())
                current_time = h + m / 60.0 + s / 3600.0
                continue

            c = COV_RE.search(line)
            if c and current_time is not None:
                cov = float(c.group(1))
                times.append(current_time)
                covs.append(cov)
                current_time = None

    return times, covs


def filter_24h(times, covs):
    filtered_t = []
    filtered_c = []
    for t, c in zip(times, covs):
        if t <= 24.0:
            filtered_t.append(t)
            filtered_c.append(c)
    return filtered_t, filtered_c


def display_name(dir_name: str) -> str:
    if dir_name == "rq_origin":
        return "rq_origin"
    if dir_name == "rq_no_mut":
        return "rq_mut"
    if dir_name == "rq_no_mut_no_osv":
        return "rq_no_mut_no_osv"
    return dir_name


def series_color(dir_name: str):
    if dir_name == "rq_origin":
        return "tab:orange"
    if dir_name == "rq_no_mut":
        return "tab:blue"
    if dir_name == "rq_no_mut_no_osv":
        return "tab:green"
    return None


def main():
    series = []
    for subdir in sorted(p for p in ROOT.iterdir() if p.is_dir()):
        log_path = subdir / "fuzz_log.txt"
        if not log_path.exists():
            continue
        times, covs = parse_log(log_path)
        if not times or not covs:
            continue
        times, covs = filter_24h(times, covs)
        if times and covs:
            series.append((subdir.name, display_name(subdir.name), times, covs))

    if not series:
        raise SystemExit("No coverage data found in fuzz_log.txt files.")

    plt.figure(figsize=(10, 6))
    for dir_name, name, times, covs in series:
        plt.plot(
            times,
            covs,
            label=name,
            linewidth=1.5,
            color=series_color(dir_name),
        )

    plt.xlim(0, 24)
    plt.xlabel("Time (hours)")
    plt.ylabel("Coverage (%)")
    plt.title("Coverage Over Time (First 24h)")
    plt.ylim(bottom=20)
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.legend()
    plt.tight_layout()

    out_path = ROOT / "coverage_plot.png"
    plt.savefig(out_path, dpi=150)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
