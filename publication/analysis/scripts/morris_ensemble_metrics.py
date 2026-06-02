"""Morris ensemble metrics (P-factor, R-factor, best member) without ModelProcessing imports."""
from __future__ import annotations

import glob
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
USER_ROOT = Path("${SWATGENX_USER_PATH}")


def swatcup_p_factor(observed, lower_band, upper_band) -> float:
    o = np.asarray(observed, dtype=float)
    lo = np.asarray(lower_band, dtype=float)
    hi = np.asarray(upper_band, dtype=float)
    valid = np.isfinite(o) & np.isfinite(lo) & np.isfinite(hi)
    if not np.any(valid):
        return float("nan")
    o, lo, hi = o[valid], lo[valid], hi[valid]
    return float(np.mean((o >= lo) & (o <= hi)))


def swatcup_r_factor(observed, lower_band, upper_band) -> float:
    o = np.asarray(observed, dtype=float)
    lo = np.asarray(lower_band, dtype=float)
    hi = np.asarray(upper_band, dtype=float)
    valid = np.isfinite(o) & np.isfinite(lo) & np.isfinite(hi)
    if not np.any(valid):
        return float("nan")
    o = o[valid]
    widths = hi[valid] - lo[valid]
    sigma = np.std(o, ddof=0)
    if sigma < 1e-12:
        return float("nan")
    return float(np.mean(widths) / sigma)


def nse(obs, sim) -> float:
    o = np.asarray(obs, dtype=float)
    s = np.asarray(sim, dtype=float)
    v = np.isfinite(o) & np.isfinite(s)
    o, s = o[v], s[v]
    denom = np.sum((o - np.mean(o)) ** 2)
    if denom < 1e-12:
        return float("nan")
    return float(1.0 - np.sum((o - s) ** 2) / denom)


def _load_daily_npz(path: str):
    data = np.load(path, allow_pickle=False)
    dates = pd.to_datetime(data["date_ns"].astype("datetime64[ns]"))
    return dates, data["obs"].astype(float), data["sim"].astype(float)


def _load_monthly_npz(path: str):
    data = np.load(path, allow_pickle=False)
    if "monthly_yr" not in data.files:
        return None
    yr = data["monthly_yr"].astype(np.int32)
    mon = data["monthly_mon"].astype(np.int32)
    dates = pd.to_datetime(pd.DataFrame({"year": yr, "month": mon, "day": np.ones(len(yr), dtype=np.int32)}))
    return dates, data["monthly_obs"].astype(float), data["monthly_sim"].astype(float)


def _sorted_member_paths(ensemble_dir: str, station_id: str) -> list[str]:
    paths = glob.glob(os.path.join(ensemble_dir, f"m*_s{station_id}.npz"))

    def _key(p: str) -> int:
        m = re.search(r"m(\d+)_", os.path.basename(p))
        return int(m.group(1)) if m else -1

    return sorted(paths, key=_key)


def gather_ensemble(ensemble_dir: str, station_id: str, *, monthly: bool = False):
    paths = _sorted_member_paths(ensemble_dir, station_id)
    if not paths:
        return None
    sims = []
    index = None
    obs_arr = None
    loader = _load_monthly_npz if monthly else _load_daily_npz
    for p in paths:
        triplet = loader(p)
        if triplet is None:
            return None
        d, o, s = triplet
        df = pd.DataFrame({"date": d, "obs": o, "sim": s}).drop_duplicates(subset=["date"], keep="last")
        df = df.set_index("date").sort_index()
        if index is None:
            index = df.index
            obs_arr = df["obs"].values
            sims.append(df["sim"].reindex(index).values)
        else:
            sims.append(df["sim"].reindex(index).values)
    return index, obs_arr, np.vstack(sims)


def morris_best_member_index(sensitivity_dir: Path) -> int:
    samples = sensitivity_dir / "morris_samples_SWAT_MODEL_Web_Application.csv"
    df = pd.read_csv(samples)
    return int(df["objective"].idxmin())


def compute_ensemble_metrics(
    site_root: Path,
    gage_channel: str,
    *,
    monthly: bool = False,
) -> dict[str, float | int | None]:
    sens = site_root / "calibration_artifacts/Default_initialized/sensitivity"
    ensemble_dir = sens / "ensemble"
    gathered = gather_ensemble(str(ensemble_dir), gage_channel, monthly=monthly)
    if gathered is None:
        raise FileNotFoundError(f"No ensemble for channel {gage_channel} under {ensemble_dir}")
    date_index, obs, mat = gathered
    p_low = np.nanpercentile(mat, 2.5, axis=0)
    p_high = np.nanpercentile(mat, 97.5, axis=0)
    best_idx = morris_best_member_index(sens)
    ch = gage_channel
    best_path = ensemble_dir / f"m{best_idx:03d}_s{ch}.npz"
    best_nse = None
    if best_path.is_file():
        triplet = _load_monthly_npz(str(best_path)) if monthly else _load_daily_npz(str(best_path))
        if triplet:
            d_b, _, best_sim = triplet
            best_aligned = pd.Series(best_sim, index=d_b).reindex(date_index).values
            v = np.isfinite(best_aligned) & np.isfinite(obs)
            if int(v.sum()) > 5:
                best_nse = nse(obs[v], best_aligned[v])
    return {
        "n_morris_members": len(_sorted_member_paths(str(ensemble_dir), gage_channel)),
        "morris_best_member_index": best_idx,
        "p_factor": swatcup_p_factor(obs, p_low, p_high),
        "r_factor": swatcup_r_factor(obs, p_low, p_high),
        "best_nse": best_nse,
    }
