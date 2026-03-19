import pandas as pd
import numpy as np

REQUIRED_COLS = ["month", "county", "cases"]


def load_and_prepare(df: pd.DataFrame) -> pd.DataFrame:
    # Validate columns
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}. Required: {REQUIRED_COLS}")

    out = df.copy()
    out["month"] = pd.to_datetime(out["month"], errors="coerce").dt.to_period("M")
    if out["month"].isna().any():
        raise ValueError("Could not parse some month values. Use YYYY-MM.")

    out["county"] = out["county"].astype(str).str.strip()
    out["cases"] = pd.to_numeric(out["cases"], errors="coerce")
    if out["cases"].isna().any():
        raise ValueError("Some cases values are not numeric.")
    if (out["cases"] < 0).any():
        raise ValueError("Cases must be >= 0.")

    # Sum duplicates
    out = out.groupby(["county", "month"], as_index=False)["cases"].sum()

    # Fill missing months per county with 0
    all_rows = []
    for county, g in out.groupby("county"):
        g = g.sort_values("month")
        full = pd.period_range(g["month"].min(), g["month"].max(), freq="M")
        filled = (
            g.set_index("month")
             .reindex(full, fill_value=0)
             .rename_axis("month")
             .reset_index()
        )
        filled["county"] = county
        all_rows.append(filled)

    out = pd.concat(all_rows, ignore_index=True)
    out = out.sort_values(["county", "month"]).reset_index(drop=True)
    return out


def run_mock_cusum(prepared: pd.DataFrame, threshold: float = 4.0) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    This is NOT real CUSUM.
    It creates a 'cusum-like' curve and flags alerts when it crosses threshold.
    Just for demo.
    """
    rows = []
    episodes = []

    for county, g in prepared.groupby("county"):
        g = g.sort_values("month").reset_index(drop=True).copy()

        # Simple smoothing (3-month moving avg) for nicer plots
        g["cases_smoothed"] = g["cases"].rolling(3, min_periods=1).mean()

        # Simple baseline (rolling mean of previous 6 months) just for demo
        g["baseline"] = g["cases_smoothed"].shift(1).rolling(6, min_periods=1).mean()

        # Mock "deviation"
        g["deviation"] = (g["cases_smoothed"] - g["baseline"]).fillna(0)

        # Mock "cusum":
        # accumulate only positive deviations, slowly decays when negative
        cus = []
        s = 0.0
        for d in g["deviation"].to_numpy():
            if d > 0:
                s = s + float(d)
            else:
                s = max(0.0, s + float(d))   # drop faster when cases fall
            cus.append(s)
        g["cusum"] = cus
        g["threshold"] = threshold
        g["alert_flag"] = g["cusum"] > threshold

        # Build per-month rows
        for _, r in g.iterrows():
            rows.append({
                "month": r["month"],
                "county": county,
                "cases_raw": r["cases"],
                "cases_smoothed": r["cases_smoothed"],
                "baseline": r["baseline"],
                "deviation": r["deviation"],
                "cusum": r["cusum"],
                "threshold": threshold,
                "alert_flag": bool(r["alert_flag"]),
            })

        # Derive alert episodes
        active = False
        start = None
        for i in range(len(g)):
            is_alert = bool(g.loc[i, "alert_flag"])
            m = g.loc[i, "month"]

            if (not active) and is_alert:
                active = True
                start = m

            if active and (not is_alert):
                episodes.append({
                    "county": county,
                    "alert_start_month": start,
                    "detection_month": start,
                    "alert_end_month": m,
                    "status": "ENDED",
                })
                active = False
                start = None

        if active and start is not None:
            episodes.append({
                "county": county,
                "alert_start_month": start,
                "detection_month": start,
                "alert_end_month": pd.NaT,
                "status": "ACTIVE",
            })

    per_month = pd.DataFrame(rows).sort_values(["county", "month"]).reset_index(drop=True)
    ep = pd.DataFrame(episodes)

    # Pretty formatting for duration
    if not ep.empty:
        ep["duration_months"] = ep.apply(
            lambda r: np.nan if pd.isna(r["alert_end_month"])
            else (r["alert_end_month"] - r["alert_start_month"]).n,
            axis=1,
        )

    return per_month, ep
