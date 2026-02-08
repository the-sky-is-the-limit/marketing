from __future__ import annotations
import pandas as pd
from typing import List
from logic.metrics import funnel_kpis, group_funnel


def rank_by_metric(df: pd.DataFrame, group_col: str, metric: str, min_leads: int = 5) -> pd.DataFrame:
    t = group_funnel(df, group_col)
    t = t[t["leads"] >= min_leads].copy()
    t = t.sort_values(metric, ascending=False)
    return t


def contrib_flag_table(df: pd.DataFrame, contrib_cols: List[str]) -> pd.DataFrame:
    rows = []
    for c in contrib_cols:
        col_name = f"_contrib__{c}"
        if col_name not in df.columns:
            continue
        sub = df[df[col_name] == True]
        if len(sub):
            k = funnel_kpis(sub)
            k["flag"] = c
            rows.append(k)
        else:
            rows.append({
                "flag": c, "leads": 0, "qualified": 0, "won": 0,
                "qualified_rate": 0.0, "won_rate": 0.0, "won_rate_in_qualified": 0.0,
                "revenue_sum": 0.0, "median_ticket": 0.0, "mean_ticket": 0.0
            })
    out = pd.DataFrame(rows)
    if "flag" in out.columns:
        cols = ["flag"] + [c for c in out.columns if c != "flag"]
        out = out[cols]
    return out
