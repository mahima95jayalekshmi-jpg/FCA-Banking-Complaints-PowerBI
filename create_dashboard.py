"""Static dashboard previews for the README, built from the SQL result CSVs.

Run after etl/load_fca.py:
    python create_dashboard.py

Writes images/overview.png and images/consumer_duty.png. These are static
previews; the interactive version is the Power BI report.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
IMAGES = ROOT / "images"

NAVY, BLUE, RED, GREY = "#142B48", "#3577B9", "#D1495B", "#8A97A6"
BACKGROUND = "#F7F9FC"
FLAGGED = {"Lloyds Banking Group", "NatWest Group"}
DEADLINE_TARGET = 95  # reference line only; not a regulatory threshold

plt.rcParams.update({
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": BACKGROUND,
    "axes.facecolor": BACKGROUND,
    "savefig.facecolor": BACKGROUND,
})


def read_result(prefix: str) -> pd.DataFrame:
    return pd.read_csv(next(RESULTS.glob(f"{prefix}*.csv")))


def bar_colours(names) -> list:
    return [RED if name in FLAGGED else BLUE for name in names]


def peer_averages(rates: pd.DataFrame) -> tuple[float, float]:
    """Peer averages from the outlier query; fall back to a simple mean if it returned no rows."""
    outliers = read_result("q4_")
    if not outliers.empty:
        return outliers["peer_per_1000"].iloc[0], outliers["peer_pct_upheld"].iloc[0]
    return rates["complaints_per_1000"].mean(), rates["pct_upheld"].mean()


def chart_rates(ax, rates: pd.DataFrame, peer_rate: float):
    data = rates.dropna(subset=["complaints_per_1000"]).nlargest(12, "complaints_per_1000")
    data = data.sort_values("complaints_per_1000")
    ax.barh(data["banking_group"], data["complaints_per_1000"], color=bar_colours(data["banking_group"]))
    ax.axvline(peer_rate, color=NAVY, ls="--", lw=1)
    ax.text(peer_rate, len(data) - 0.4, f" peer average {peer_rate:.2f}", color=NAVY, fontsize=9, va="bottom")
    ax.set_title("Complaints per 1,000 accounts (12 highest)", loc="left", fontweight="bold")
    ax.set_xlabel("Complaints per 1,000 accounts")


def chart_timeliness(ax, timeliness: pd.DataFrame):
    data = timeliness.nsmallest(12, "pct_within_8_weeks").sort_values("pct_within_8_weeks", ascending=False)
    bars = ax.barh(data["banking_group"], data["pct_within_8_weeks"], color=bar_colours(data["banking_group"]))
    ax.bar_label(bars, labels=[f"{v:.1f}%" for v in data["pct_within_8_weeks"]], padding=3, fontsize=8)
    ax.set_xlim(75, 103)
    ax.set_title("Resolved within the 8-week deadline (12 lowest)", loc="left", fontweight="bold")
    ax.set_xlabel("% of closed complaints")


def chart_scatter(ax, rates: pd.DataFrame, peer_rate: float, peer_upheld: float):
    data = rates.dropna(subset=["complaints_per_1000"])
    sizes = 20 + 400 * data["opened"] / data["opened"].max()
    ax.scatter(data["complaints_per_1000"], data["pct_upheld"], s=sizes,
               color=bar_colours(data["banking_group"]), alpha=0.75, edgecolor="white")
    ax.axvline(peer_rate, color=GREY, ls="--", lw=1)
    ax.axhline(peer_upheld, color=GREY, ls="--", lw=1)
    label_offsets = {"Nationwide": (-8, -14), "Barclays": (6, 6), "HSBC": (-8, 6)}
    for _, row in data[data["opened"] > 20_000].iterrows():
        dx, dy = label_offsets.get(row["banking_group"], (6, 4))
        ax.annotate(row["banking_group"], (row["complaints_per_1000"], row["pct_upheld"]),
                    xytext=(dx, dy), textcoords="offset points", fontsize=8,
                    ha="right" if dx < 0 else "left")
    ax.text(0.98, 0.97, "More complaints and\nmore often at fault", transform=ax.transAxes,
            ha="right", va="top", fontsize=8, color=RED)
    ax.set_title("Complaint rate vs % upheld (bubble = volume)", loc="left", fontweight="bold")
    ax.set_xlabel("Complaints per 1,000 accounts")
    ax.set_ylabel("% upheld by the bank")


def chart_segments(ax, segments: pd.DataFrame):
    bars = ax.bar(segments["segment"], segments["pct_upheld"], color=[BLUE, NAVY][: len(segments)], width=0.5)
    ax.bar_label(bars, labels=[f"{v:.1f}%" for v in segments["pct_upheld"]], padding=3, fontweight="bold")
    ax.set_ylim(0, 75)
    ax.set_title("Complaints upheld: digital vs high-street banks", loc="left", fontweight="bold")
    ax.set_ylabel("% upheld")


def build_overview(rates, timeliness, segments):
    peer_rate, peer_upheld = peer_averages(rates)
    fig = plt.figure(figsize=(16, 10))
    grid = fig.add_gridspec(2, 2, left=0.17, right=0.97, top=0.85, bottom=0.08, wspace=0.55, hspace=0.45)
    fig.text(0.03, 0.95, "UK Bank Complaints | 2026 H1", fontsize=22, fontweight="bold", color=NAVY)
    fig.text(0.03, 0.91, "FCA firm-level data  •  Banking and credit cards  •  22 peer banking groups  •  "
             "Lloyds and NatWest highlighted", fontsize=11, color=GREY)

    chart_rates(fig.add_subplot(grid[0, 0]), rates, peer_rate)
    chart_timeliness(fig.add_subplot(grid[0, 1]), timeliness)
    chart_scatter(fig.add_subplot(grid[1, 0]), rates, peer_rate, peer_upheld)
    chart_segments(fig.add_subplot(grid[1, 1]), segments)

    fig.text(0.03, 0.02, "Source: FCA firm-level complaints data, 2026 H1. Some firms report on non-calendar "
             "6-month windows. See README for method and limitations.", fontsize=9, color=GREY)
    fig.savefig(IMAGES / "overview.png", dpi=150)
    plt.close(fig)


def build_deadline_chart(timeliness):
    data = timeliness.dropna(subset=["closed_after_8_weeks"]).nlargest(10, "closed_after_8_weeks")
    data = data.sort_values("closed_after_8_weeks")
    fig, ax = plt.subplots(figsize=(12, 6.5))
    bars = ax.barh(data["banking_group"], data["closed_after_8_weeks"], color=bar_colours(data["banking_group"]))
    ax.bar_label(bars, labels=[f"{v:,.0f}" for v in data["closed_after_8_weeks"]], padding=4, fontsize=9)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.set_xlabel("Complaints resolved after 8 weeks (estimated)")
    ax.set_title("Complaints resolved after the 8-week deadline, 2026 H1", loc="left",
                 fontsize=16, fontweight="bold", pad=16)
    fig.text(0.02, 0.02, "Estimated as closed complaints × (100% − % resolved within 8 weeks). "
             "Banking and credit cards, 10 highest peer banking groups.", fontsize=9, color=GREY)
    fig.tight_layout(rect=[0, 0.05, 1, 1])
    fig.savefig(IMAGES / "consumer_duty.png", dpi=150)
    plt.close(fig)


def main():
    IMAGES.mkdir(exist_ok=True)
    rates = read_result("q1_")
    segments = read_result("q3_")
    segments = segments[segments["period_label"] == segments["period_label"].max()]
    timeliness = read_result("q6_")

    build_overview(rates, timeliness, segments)
    build_deadline_chart(timeliness)
    print(f"Created {IMAGES / 'overview.png'} and {IMAGES / 'consumer_duty.png'}")


if __name__ == "__main__":
    main()
