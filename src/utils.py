from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
FIGURES_DIR = ROOT / "figures"
RESULTS_DIR = ROOT / "results"


def ensure_project_dirs() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    FIGURES_DIR.mkdir(exist_ok=True)
    RESULTS_DIR.mkdir(exist_ok=True)


def fit_ols(y: pd.Series, x: pd.DataFrame) -> pd.DataFrame:
    x_matrix = np.column_stack([np.ones(len(x)), x.to_numpy()])
    beta, *_ = np.linalg.lstsq(x_matrix, y.to_numpy(), rcond=None)
    y_hat = x_matrix @ beta
    residuals = y.to_numpy() - y_hat

    n_obs, n_params = x_matrix.shape
    dof = max(n_obs - n_params, 1)
    sigma2 = (residuals @ residuals) / dof
    cov = sigma2 * np.linalg.inv(x_matrix.T @ x_matrix)
    std_err = np.sqrt(np.diag(cov))
    t_stat = beta / std_err

    names = ["intercept", *x.columns.tolist()]
    return pd.DataFrame(
        {
            "term": names,
            "coefficient": beta,
            "std_error": std_err,
            "t_stat": t_stat,
        }
    )

