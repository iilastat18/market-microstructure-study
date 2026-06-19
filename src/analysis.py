from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from utils import DATA_DIR, FIGURES_DIR, RESULTS_DIR, ensure_project_dirs, fit_ols


plt.style.use("seaborn-v0_8-whitegrid")


def load_data() -> pd.DataFrame:
    path = DATA_DIR / "synthetic_microstructure_data.csv"
    if not path.exists():
        raise FileNotFoundError(
            "Synthetic dataset not found. Run `python src/generate_data.py` first."
        )
    df = pd.read_csv(path, parse_dates=["date"])
    df["is_stress"] = (df["stress_regime"] == "Stress").astype(int)
    return df


def build_summary_tables(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    summary = (
        df.groupby(["stress_regime", "liquidity_tier"], as_index=False)[
            ["spread_bps", "realized_vol", "turnover_usd_m"]
        ]
        .mean()
        .round(3)
    )

    regression_input = df[["realized_vol", "log_turnover", "is_stress"]].copy()
    regression = fit_ols(df["spread_bps"], regression_input).round(4)
    return summary, regression


def save_charts(df: pd.DataFrame) -> None:
    sample = df.sample(n=min(len(df), 2000), random_state=7)

    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    colors = {"Low": "#b24a3a", "Medium": "#d18f43", "High": "#2f7d6b"}
    for tier, group in sample.groupby("liquidity_tier"):
        ax.scatter(
            group["realized_vol"],
            group["spread_bps"],
            alpha=0.35,
            s=18,
            label=tier,
            color=colors[tier],
        )
    ax.set_title("Spread Proxy vs Realized Volatility")
    ax.set_xlabel("Realized volatility")
    ax.set_ylabel("Spread proxy (bps)")
    ax.legend(title="Liquidity tier")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "spread_vs_volatility.png", dpi=180)
    plt.close(fig)

    grouped = (
        df.groupby(["stress_regime", "liquidity_tier"], as_index=False)["spread_bps"]
        .mean()
        .round(2)
    )
    fig, ax = plt.subplots(figsize=(8.2, 5.0))
    x = np.arange(grouped["stress_regime"].nunique())
    width = 0.22
    tiers = ["Low", "Medium", "High"]
    regime_order = ["Calm", "Stress"]
    for idx, tier in enumerate(tiers):
        subset = grouped[grouped["liquidity_tier"] == tier].set_index("stress_regime").reindex(regime_order)
        ax.bar(x + (idx - 1) * width, subset["spread_bps"], width=width, label=tier, color=colors[tier])
    ax.set_xticks(x)
    ax.set_xticklabels(regime_order)
    ax.set_ylabel("Average spread proxy (bps)")
    ax.set_title("Spread Proxy by Regime and Liquidity Tier")
    ax.legend(title="Liquidity tier")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "spread_by_regime_and_liquidity.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.2, 5.0))
    box_data = [df.loc[df["liquidity_tier"] == tier, "spread_bps"] for tier in tiers]
    box = ax.boxplot(box_data, tick_labels=tiers, patch_artist=True)
    for patch, tier in zip(box["boxes"], tiers):
        patch.set_facecolor(colors[tier])
        patch.set_alpha(0.55)
    ax.set_title("Spread Distribution by Liquidity Tier")
    ax.set_ylabel("Spread proxy (bps)")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "spread_distribution_by_liquidity.png", dpi=180)
    plt.close(fig)


def save_findings(df: pd.DataFrame, summary: pd.DataFrame, regression: pd.DataFrame) -> None:
    stress_spread = (
        summary.loc[summary["stress_regime"] == "Stress", "spread_bps"].mean()
    )
    calm_spread = summary.loc[summary["stress_regime"] == "Calm", "spread_bps"].mean()
    low_liq_spread = (
        summary.loc[summary["liquidity_tier"] == "Low", "spread_bps"].mean()
    )
    high_liq_spread = (
        summary.loc[summary["liquidity_tier"] == "High", "spread_bps"].mean()
    )
    vol_coef = regression.loc[regression["term"] == "realized_vol", "coefficient"].iloc[0]
    turnover_coef = regression.loc[regression["term"] == "log_turnover", "coefficient"].iloc[0]
    stress_coef = regression.loc[regression["term"] == "is_stress", "coefficient"].iloc[0]

    findings = f"""# Key Findings

- Average spread proxy is wider in stress regimes than in calm regimes ({stress_spread:.2f} bps vs {calm_spread:.2f} bps).
- Low-liquidity names show materially wider spreads than high-liquidity names ({low_liq_spread:.2f} bps vs {high_liq_spread:.2f} bps).
- In the simple OLS, realized volatility has a positive association with spread ({vol_coef:.2f} coefficient).
- Log turnover has a negative association with spread ({turnover_coef:.2f} coefficient), consistent with a liquidity effect.
- The stress indicator remains positive ({stress_coef:.2f} coefficient), suggesting extra widening beyond the volatility channel alone.

## Interpretation

This synthetic study reproduces the intuition that trading frictions become larger when market conditions deteriorate and when instruments trade with lower liquidity.

## Portfolio Framing

The value of this project is not the synthetic result itself. The value is that it demonstrates a clean research workflow:

1. formulate a microstructure-style question
2. generate or load structured data
3. test a small empirical relationship
4. summarize findings clearly with charts and concise interpretation
"""

    (RESULTS_DIR / "key_findings.md").write_text(findings)


def main() -> None:
    ensure_project_dirs()
    df = load_data()
    summary, regression = build_summary_tables(df)

    summary.to_csv(RESULTS_DIR / "summary_metrics.csv", index=False)
    regression.to_csv(RESULTS_DIR / "regression_summary.csv", index=False)
    save_charts(df)
    save_findings(df, summary, regression)

    print("Saved results to:")
    print(f"  - {RESULTS_DIR / 'summary_metrics.csv'}")
    print(f"  - {RESULTS_DIR / 'regression_summary.csv'}")
    print(f"  - {RESULTS_DIR / 'key_findings.md'}")
    print(f"  - {FIGURES_DIR / 'spread_vs_volatility.png'}")
    print(f"  - {FIGURES_DIR / 'spread_by_regime_and_liquidity.png'}")
    print(f"  - {FIGURES_DIR / 'spread_distribution_by_liquidity.png'}")


if __name__ == "__main__":
    main()
