import numpy as np
import warnings
from scipy.stats import spearmanr

def compute_metrics(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)
    mask = ~(np.isnan(y_true) | np.isnan(y_pred))
    y_true = y_true[mask]
    y_pred = y_pred[mask]
    n = len(y_true)
    if n < 2:
        return {"n": n, "error": "insufficient data"}
    errors = y_true - y_pred
    mae = float(np.mean(np.abs(errors)))
    rmse = float(np.sqrt(np.mean(errors ** 2)))
    ss_res = np.sum(errors ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    r2 = float(1 - ss_res / ss_tot) if ss_tot > 1e-12 else 0.0
    mape = float(np.mean(np.abs(errors / (np.abs(y_true) + 1e-10)))) * 100
    max_error = float(np.max(np.abs(errors)))
    if n >= 3:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            rho, _ = spearmanr(y_true, y_pred)
            spearman_r = float(rho) if not np.isnan(rho) else None
    else:
        spearman_r = None
    return {
        "n": n,
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
        "mape": mape,
        "max_error": max_error,
        "spearman_r": spearman_r,
    }
