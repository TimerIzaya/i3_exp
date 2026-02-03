# -*- coding: utf-8 -*-
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# 脚本现在放在 rq_osv/analysis/tp/ 下，这里把日志根目录指回 rq_osv/
SCRIPT_DIR = Path(__file__).resolve().parent
LOG_ROOT = Path(__file__).resolve().parents[2]

TIME_RE = re.compile(r"Elapsed Time\s*:\s*(\d+)h\s*(\d+)m\s*(\d+)s")
TP_RE = re.compile(r"Throughput\s*\(seeds/min\)\s*:\s*([0-9.]+)")


def parse_throughput(log_path: Path):
    """从 fuzz_log.txt 中提取 (小时, 吞吐量) 序列。"""
    xs = []
    ys = []

    pending_time = None
    with log_path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            m_t = TIME_RE.search(line)
            if m_t:
                h, m, s = map(int, m_t.groups())
                pending_time = h + m / 60.0 + s / 3600.0
                continue

            m_tp = TP_RE.search(line)
            if m_tp and pending_time is not None:
                tp = float(m_tp.group(1))
                xs.append(pending_time)
                ys.append(tp)
                pending_time = None

    return xs, ys


def filter_0_24h(xs, ys):
    fx = []
    fy = []
    for x, y in zip(xs, ys):
        if 0.0 <= x <= 24.0:
            fx.append(x)
            fy.append(y)
    return fx, fy


def bin_quantile_band(xs, ys, bin_minutes=10, start_h=0.0, end_h=24.0, q_low=25, q_mid=50, q_high=75):
    """
    按固定时间桶（默认每 10min）计算分位数带。

    - x: 取每个桶的中心点（小时）
    - y_mid: 中位数（或 q_mid）
    - y_low/y_high: 分位带（q_low~q_high）
    """
    if not xs or not ys:
        return [], [], [], []

    pairs = sorted(zip(xs, ys), key=lambda t: t[0])

    bin_w = bin_minutes / 60.0
    n_bins = int((end_h - start_h) / bin_w + 1e-9)

    out_x = []
    out_low = []
    out_mid = []
    out_high = []

    j = 0
    for i in range(n_bins):
        left = start_h + i * bin_w
        right = left + bin_w
        vals = []
        while j < len(pairs) and pairs[j][0] < right:
            if pairs[j][0] >= left:
                vals.append(pairs[j][1])
            j += 1

        if not vals:
            continue

        out_x.append(left + bin_w / 2.0)
        out_low.append(float(np.percentile(vals, q_low)))
        out_mid.append(float(np.percentile(vals, q_mid)))
        out_high.append(float(np.percentile(vals, q_high)))

    return out_x, out_low, out_mid, out_high


def main():
    series = []
    for subdir in sorted(p for p in LOG_ROOT.iterdir() if p.is_dir()):
        log_path = subdir / "fuzz_log.txt"
        if not log_path.exists():
            continue

        xs, ys = parse_throughput(log_path)
        xs, ys = filter_0_24h(xs, ys)
        bx, b_low, b_mid, b_high = bin_quantile_band(
            xs,
            ys,
            bin_minutes=10,
            start_h=0.0,
            end_h=24.0,
            q_low=25,
            q_mid=50,
            q_high=75,
        )
        if bx:
            series.append((subdir.name, bx, b_low, b_mid, b_high))

    if not series:
        raise SystemExit("没有在 fuzz_log.txt 里找到吞吐量数据（Throughput）。")

    plt.figure(figsize=(10, 6))
    for name, bx, b_low, b_mid, b_high in series:
        plt.fill_between(bx, b_low, b_high, alpha=0.18)
        plt.plot(bx, b_mid, label=name, linewidth=0.9)

    plt.xlim(0, 24)
    plt.xlabel("Time (hours)")
    plt.ylabel("Throughput (seeds/min)")
    plt.title("Throughput Quantile Band (0-24h, 10min bins, P25-P75 + Median)")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.legend()
    plt.tight_layout()

    # 输出放在脚本同目录（analysis/tp）
    out_path = SCRIPT_DIR / "throughput_plot.png"
    plt.savefig(out_path, dpi=150)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
