from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from utils import DATA_DIR, ensure_project_dirs


def build_synthetic_dataset(seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    ensure_project_dirs()

    dates = pd.bdate_range("2024-01-02", periods=260)
    tickers = [f"STK{i:02d}" for i in range(1, 31)]
    liquidity_tiers = ["Low", "Medium", "High"]
    market_caps = ["Small", "Mid", "Large"]
    regions = ["US", "Europe", "Asia"]
    sectors = ["Tech", "Financials", "Industrials", "Healthcare"]

    meta = []
    for ticker in tickers:
        liquidity_tier = rng.choice(liquidity_tiers, p=[0.28, 0.42, 0.30])
        market_cap = rng.choice(market_caps, p=[0.30, 0.38, 0.32])
        region = rng.choice(regions)
        sector = rng.choice(sectors)
        base_turnover = {"Low": 18.0, "Medium": 45.0, "High": 110.0}[liquidity_tier]
        base_spread = {"Low": 22.0, "Medium": 12.0, "High": 6.5}[liquidity_tier]
        base_vol = {"Small": 0.028, "Mid": 0.022, "Large": 0.018}[market_cap]
        meta.append(
            {
                "ticker": ticker,
                "liquidity_tier": liquidity_tier,
                "market_cap_bucket": market_cap,
                "region": region,
                "sector": sector,
                "base_turnover": base_turnover,
                "base_spread": base_spread,
                "base_vol": base_vol,
            }
        )

    meta_df = pd.DataFrame(meta)
    stress_days = set(rng.choice(np.arange(len(dates)), size=round(len(dates) * 0.22), replace=False).tolist())

    rows: list[dict[str, object]] = []
    for day_idx, current_date in enumerate(dates):
        market_stress = 1 if day_idx in stress_days else 0
        market_shock = rng.normal(0.0, 0.55 if market_stress else 0.20)

        for _, row in meta_df.iterrows():
            vol = (
                row["base_vol"]
                + (0.012 if market_stress else 0.0)
                + abs(market_shock) * 0.008
                + rng.normal(0.0, 0.003)
            )
            turnover = (
                row["base_turnover"]
                * (1.10 + 0.18 * market_stress)
                * np.exp(rng.normal(0.0, 0.25))
            )
            spread = (
                row["base_spread"]
                + 280 * vol
                + 24 / np.sqrt(max(turnover, 1.0))
                + market_stress * 3.5
                + rng.normal(0.0, 1.2)
            )
            ret = rng.normal(0.0, vol)
            rows.append(
                {
                    "date": current_date,
                    "ticker": row["ticker"],
                    "liquidity_tier": row["liquidity_tier"],
                    "market_cap_bucket": row["market_cap_bucket"],
                    "region": row["region"],
                    "sector": row["sector"],
                    "return": round(float(ret), 5),
                    "realized_vol": round(float(max(vol, 0.006)), 5),
                    "turnover_usd_m": round(float(max(turnover, 3.0)), 2),
                    "spread_bps": round(float(max(spread, 2.5)), 2),
                    "stress_regime": "Stress" if market_stress else "Calm",
                }
            )

    df = pd.DataFrame(rows)
    df["log_turnover"] = np.log(df["turnover_usd_m"])
    return df


def main() -> None:
    df = build_synthetic_dataset()
    out_path = DATA_DIR / "synthetic_microstructure_data.csv"
    df.to_csv(out_path, index=False)
    print(f"Wrote dataset to {out_path}")
    print(df.head())


if __name__ == "__main__":
    main()

