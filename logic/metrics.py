from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Dict


def funnel_kpis(df: pd.DataFrame) -> Dict[str, float]:
    n = len(df)
    q = int(df["_is_qualified"].sum())
    w = int(df["_is_won"].sum())
    rev = float(df["_revenue"].sum())

    q_rate = q / n if n else 0.0
    w_rate = w / n if n else 0.0
    w_in_q = int((df["_is_won"] & df["_is_qualified"]).sum())
    w_rate_in_q = w_in_q / q if q else 0.0

    won_rev = df.loc[df["_is_won"], "_revenue"]
    median_ticket = float(won_rev.median()) if len(won_rev) else 0.0
    mean_ticket = float(won_rev.mean()) if len(won_rev) else 0.0

    return {
        "leads": float(n),
        "qualified": float(q),
        "won": float(w),
        "qualified_rate": q_rate,
        "won_rate": w_rate,
        "won_rate_in_qualified": w_rate_in_q,
        "revenue_sum": rev,
        "median_ticket": median_ticket,
        "mean_ticket": mean_ticket,
    }


def group_funnel(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    results = []
    for name, grp in df.groupby(group_col, dropna=False, observed=False):
        row = funnel_kpis(grp)
        row[group_col] = name
        results.append(row)
    out = pd.DataFrame(results)
    if group_col in out.columns:
        cols = [group_col] + [c for c in out.columns if c != group_col]
        out = out[cols]
    return out


def pivot_segment(df: pd.DataFrame, row: str, col: str, metric: str) -> pd.DataFrame:
    results = []
    for (r, c), grp in df.groupby([row, col], dropna=False, observed=True):
        kpi = funnel_kpis(grp)
        kpi[row] = r
        kpi[col] = c
        results.append(kpi)
    tmp = pd.DataFrame(results)
    if len(tmp) == 0:
        return pd.DataFrame()
    p = tmp.pivot(index=row, columns=col, values=metric)
    return p


def pivot_segment_count(df: pd.DataFrame, row: str, col: str) -> pd.DataFrame:
    """リード数のピボット（セグメントのサンプルサイズ確認用）"""
    results = []
    for (r, c), grp in df.groupby([row, col], dropna=False, observed=True):
        results.append({row: r, col: c, "count": len(grp)})
    tmp = pd.DataFrame(results)
    if len(tmp) == 0:
        return pd.DataFrame()
    p = tmp.pivot(index=row, columns=col, values="count").fillna(0).astype(int)
    return p
