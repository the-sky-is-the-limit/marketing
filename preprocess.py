from __future__ import annotations
import pandas as pd
import numpy as np
from pandas.api.types import CategoricalDtype
from typing import Dict, Tuple, List

from logic.schema import ASSET_ORDER, AGE_ORDER, CONTRIB_COL_CANDIDATES


def _to_bool_series(s: pd.Series) -> pd.Series:
    if s.dtype == bool:
        return s.fillna(False)
    return (
        s.astype(str)
        .str.strip()
        .str.upper()
        .map({"TRUE": True, "FALSE": False, "1": True, "0": False, "YES": True, "NO": False})
        .fillna(False)
        .astype(bool)
    )


def preprocess(
    df_raw: pd.DataFrame,
    colmap: Dict[str, str],
) -> Tuple[pd.DataFrame, Dict]:
    meta: Dict = {}
    df = df_raw.copy()

    # 必須列チェック
    required_internals = ["revenue", "stage", "conv_date"]
    missing_required = [k for k in required_internals if k not in colmap]
    meta["missing_required"] = missing_required

    # 売上金額 → 数値化
    rev_col = colmap.get("revenue")
    if rev_col and rev_col in df.columns:
        df["_revenue"] = pd.to_numeric(df[rev_col], errors="coerce").fillna(0.0)
    else:
        df["_revenue"] = 0.0

    # コンバージョン日 → month
    date_col = colmap.get("conv_date")
    if date_col and date_col in df.columns:
        df["_conv_date"] = pd.to_datetime(df[date_col], errors="coerce")
        df["_month"] = df["_conv_date"].dt.to_period("M").astype(str)
    else:
        df["_conv_date"] = pd.NaT
        df["_month"] = "不明"

    # ステージ
    stage_col = colmap.get("stage")
    if stage_col and stage_col in df.columns:
        df["_stage"] = df[stage_col].astype(str).str.strip()
    else:
        df["_stage"] = ""

    df["_is_qualified"] = df["_stage"] == "Qualified"
    df["_is_won"] = df["_revenue"] > 0

    # 年代
    age_col = colmap.get("age_band")
    if age_col and age_col in df.columns:
        df["_age_band"] = df[age_col].astype(str).str.strip().replace({"": "不明", "nan": "不明"})
    else:
        df["_age_band"] = "不明"

    # 資産レンジ
    asset_col = colmap.get("assets_band")
    if asset_col and asset_col in df.columns:
        df["_asset_band"] = df[asset_col].astype(str).str.strip().replace({"": "不明", "nan": "不明"})
    else:
        df["_asset_band"] = "不明"

    df["_age_band"] = df["_age_band"].where(df["_age_band"].isin(AGE_ORDER), "不明")
    df["_asset_band"] = df["_asset_band"].where(df["_asset_band"].isin(ASSET_ORDER), "不明")

    df["_age_band"] = df["_age_band"].astype(CategoricalDtype(categories=AGE_ORDER, ordered=True))
    df["_asset_band"] = df["_asset_band"].astype(CategoricalDtype(categories=ASSET_ORDER, ordered=True))

    # UTM類・その他テキスト列
    for k in ["utm_source", "utm_medium", "utm_campaign", "utm_content",
              "lead_source", "origin", "sales_owner", "trigger"]:
        c = colmap.get(k)
        if c and c in df.columns:
            df[f"_{k}"] = df[c].astype(str).str.strip().replace({"nan": "", "None": ""})
        else:
            df[f"_{k}"] = ""

    # 貢献フラグ
    contrib_cols: List[str] = [c for c in CONTRIB_COL_CANDIDATES if c in df.columns]
    for c in contrib_cols:
        df[f"_contrib__{c}"] = _to_bool_series(df[c])

    if contrib_cols:
        df["_contrib_true_count"] = df[[f"_contrib__{c}" for c in contrib_cols]].sum(axis=1)
    else:
        df["_contrib_true_count"] = 0

    meta["contrib_cols"] = contrib_cols
    meta["contrib_multi_touch_rate"] = float((df["_contrib_true_count"] >= 2).mean()) if len(df) else 0.0
    meta["rows"] = int(len(df))
    meta["won_count"] = int(df["_is_won"].sum())
    meta["qualified_count"] = int(df["_is_qualified"].sum())
    meta["revenue_sum"] = float(df["_revenue"].sum())
    meta["date_range"] = ""
    if "_conv_date" in df.columns:
        valid_dates = df["_conv_date"].dropna()
        if len(valid_dates):
            meta["date_range"] = f"{valid_dates.min().strftime('%Y-%m-%d')} ~ {valid_dates.max().strftime('%Y-%m-%d')}"

    return df, meta
