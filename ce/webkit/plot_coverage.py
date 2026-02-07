import re
from pathlib import Path

import matplotlib.pyplot as plt

TIME_RE = re.compile(r"(\d+)h\s*(\d+)m\s*(\d+)s")
COVERAGE_RE = re.compile(r"([\d.]+)%")


def parse_ce_table_log(path: Path) -> dict[str, list[tuple[float, float]]]:
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    labels: list[str] = []
    datasets: dict[str, list[tuple[float, float]]] = {}
    current_times: list[int] | None = None

    for line in lines:
        if line.startswith("Metric"):
            parts = re.split(r"\s+", line.strip())
            if len(parts) > 1:
                labels = parts[1:]
                for label in labels:
                    datasets.setdefault(label, [])
            continue

        if "Elapsed Time" in line:
            matches = TIME_RE.findall(line)
            if labels and matches and len(matches) == len(labels):
                current_times = [
                    int(h) * 3600 + int(m) * 60 + int(s) for h, m, s in matches
                ]
            continue

        if "Coverage" in line:
            if not labels or current_times is None:
                continue
            matches = COVERAGE_RE.findall(line)
            if matches and len(matches) == len(labels):
                for label, secs, cov in zip(labels, current_times, matches):
                    datasets[label].append((secs / 3600.0, float(cov)))
            current_times = None

    return {label: sorted(values) for label, values in datasets.items() if values}


def plot_coverage(
    engine_name: str,
    engine_data: dict[str, list[tuple[float, float]]],
    output_path: Path,
) -> None:
    if not engine_data:
        raise SystemExit("no coverage data extracted")

    plt.figure(figsize=(12, 7))
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    label_order = list(engine_data.keys())

    for idx, label in enumerate(label_order):
        color = colors[idx % len(colors)]
        hrs = [t for t, _ in engine_data[label]]
        covs = [c for _, c in engine_data[label]]
        plt.plot(
            hrs,
            covs,
            marker="o",
            markersize=0.5,
            linewidth=0.5,
            label=label,
            color=color,
        )

    plt.xlabel("Elapsed time (hours)")
    plt.ylabel("Coverage (%)")
    plt.title(f"Coverage over time ({engine_name})")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.legend(ncol=2, fontsize=8)
    plt.tight_layout()
    plt.savefig(output_path)
    print("saved", output_path)


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    engine_name = base_dir.name
    log_path = base_dir / "ce_log.txt"

    if not log_path.exists():
        raise SystemExit(f"log file not found: {log_path}")

    engine_data = parse_ce_table_log(log_path)
    output_path = base_dir / "coverage_comparison.png"
    plot_coverage(engine_name, engine_data, output_path)


if __name__ == "__main__":
    main()
