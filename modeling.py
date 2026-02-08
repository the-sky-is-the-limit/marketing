from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import cross_val_score
import warnings

warnings.filterwarnings("ignore")


def _prepare_features(
    df: pd.DataFrame,
    feature_cols: List[str],
    target_col: str,
) -> Tuple[Optional[pd.DataFrame], Optional[pd.Series], Dict[str, LabelEncoder]]:
    """特徴量をエンコードして返す"""
    sub = df[feature_cols + [target_col]].dropna(subset=[target_col]).copy()
    if len(sub) < 30:
        return None, None, {}

    encoders = {}
    X_encoded = pd.DataFrame(index=sub.index)

    for col in feature_cols:
        if col not in sub.columns:
            continue
        s = sub[col]
        if hasattr(s.dtype, "categories") or s.dtype == object or s.dtype.name == "category":
            le = LabelEncoder()
            vals = s.astype(str).fillna("__missing__")
            X_encoded[col] = le.fit_transform(vals)
            encoders[col] = le
        else:
            X_encoded[col] = pd.to_numeric(s, errors="coerce").fillna(0)

    y = sub[target_col]
    return X_encoded, y, encoders


def feature_importance_classification(
    df: pd.DataFrame,
    feature_cols: List[str],
    target_col: str,
    n_estimators: int = 100,
) -> Optional[pd.DataFrame]:
    """分類（Qualified/成約の0/1）の特徴量重要度"""
    X, y, encoders = _prepare_features(df, feature_cols, target_col)
    if X is None or y is None:
        return None

    # 正例が少なすぎる場合はスキップ
    if y.sum() < 5 or (len(y) - y.sum()) < 5:
        return None

    model = GradientBoostingClassifier(
        n_estimators=n_estimators,
        max_depth=3,
        learning_rate=0.1,
        random_state=42,
    )
    model.fit(X, y)

    # CV score
    try:
        cv_scores = cross_val_score(model, X, y, cv=min(5, int(y.sum())), scoring="roc_auc")
        mean_auc = float(cv_scores.mean())
    except Exception:
        mean_auc = None

    imp = pd.DataFrame({
        "feature": X.columns,
        "importance": model.feature_importances_,
    }).sort_values("importance", ascending=False)
    imp["auc_cv"] = mean_auc

    return imp


def feature_importance_regression(
    df: pd.DataFrame,
    feature_cols: List[str],
    target_col: str = "_revenue",
    n_estimators: int = 100,
) -> Optional[pd.DataFrame]:
    """回帰（成約単価）の特徴量重要度（成約行のみで実行）"""
    sub = df[df["_is_won"] == True].copy()
    if len(sub) < 20:
        return None

    sub["_log_revenue"] = np.log1p(sub[target_col])

    X, y, encoders = _prepare_features(sub, feature_cols, "_log_revenue")
    if X is None or y is None:
        return None

    model = GradientBoostingRegressor(
        n_estimators=n_estimators,
        max_depth=3,
        learning_rate=0.1,
        random_state=42,
    )
    model.fit(X, y)

    try:
        cv_scores = cross_val_score(model, X, y, cv=min(5, len(sub) // 5), scoring="r2")
        mean_r2 = float(cv_scores.mean())
    except Exception:
        mean_r2 = None

    imp = pd.DataFrame({
        "feature": X.columns,
        "importance": model.feature_importances_,
    }).sort_values("importance", ascending=False)
    imp["r2_cv"] = mean_r2

    return imp


def get_model_features(df: pd.DataFrame, include_owner: bool = True, include_month: bool = True) -> List[str]:
    """モデルに投入する特徴量のリストを生成"""
    features = ["_age_band", "_asset_band", "_utm_source", "_utm_campaign"]

    if include_owner:
        features.append("_sales_owner")
    if include_month:
        features.append("_month")

    # 貢献フラグも特徴量に
    contrib_cols = [c for c in df.columns if c.startswith("_contrib__")]
    features.extend(contrib_cols)

    # 実際に存在する列のみ
    features = [f for f in features if f in df.columns]
    return features
