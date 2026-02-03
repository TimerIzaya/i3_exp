import re
from pathlib import Path

import matplotlib.pyplot as plt


def main() -> None:
    log_dir = Path(__file__).resolve().parent
    stat_time_re = re.compile(r"Elapsed Time\s*:\s*(\d+)h\s*(\d+)m\s*(\d+)s")
    coverage_re = re.compile(r"Coverage\s*:\s*([\d\.]+)%")
    files = sorted(log_dir.glob("*_fuzz_log.txt"))
    if not files:
        raise SystemExit("no log files found")

    datasets: dict[str, list[tuple[float, float]]] = {}
    for path in files:
        label = path.name.replace("_fuzz_log.txt", "")
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        entries: list[tuple[float, float]] = []
        for idx, line in enumerate(lines):
            m = stat_time_re.search(line)
            if not m:
                continue
            secs = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
            cov = None
            for next_line in lines[idx + 1 : idx + 60]:
                cm = coverage_re.search(next_line)
                if cm:
                    cov = float(cm.group(1))
                    break
            if cov is not None:
                entries.append((secs / 3600.0, cov))
        if entries:
            datasets[label] = sorted(entries)

    if not datasets:
        raise SystemExit("no coverage data extracted")

    plt.figure(figsize=(12, 7))
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    for idx, (label, data) in enumerate(datasets.items()):
        hrs = [t for t, _ in data]
        covs = [c for _, c in data]
        color = colors[idx % len(colors)]
        plt.plot(
            hrs,
            covs,
            marker="o",
            markersize=0.5,
            linewidth=0.5,
            label=label,
            color=color,
        )
        if label in ("me", "min"):
            step = 2
            max_hr = max(hrs)
            ticks = range(step, int(max_hr) + 1, step)
            for target in ticks:
                candidate = next(((h, c) for h, c in data if h >= target), None)
                if candidate:
                    h, c = candidate
                    plt.text(
                        h + 0.05,
                        c + 0.3,
                        f"{c:.4f}%",
                        fontsize=8,
                        color="black",
                        rotation=0,
                        bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.8),
                    )
        if label == "sa":
            for target in (22, 24):
                candidate = next(((h, c) for h, c in data if h >= target), None)
                if candidate:
                    h, c = candidate
                    plt.text(
                        h + 0.05,
                        c + 0.3,
                        f"{c:.4f}%",
                        fontsize=8,
                        color="black",
                        rotation=0,
                        bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.8),
                    )

    plt.xlabel("Elapsed time (hours)")
    plt.ylabel("Coverage (%)")
    plt.title("Coverage over time (hours) by log, me/min every 2h, sa @22h/24h")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.legend()
    plt.tight_layout()
    output = log_dir / "coverage_comparison.png"
    plt.savefig(output)
    print("saved", output)


if __name__ == "__main__":
    main()
