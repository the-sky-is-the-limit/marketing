import streamlit as st
import pandas as pd
import plotly.express as px
from logic.modeling import (
    feature_importance_classification,
    feature_importance_regression,
    get_model_features,
)


def render_model_tab():
    st.subheader("🧪 Drivers（要因推定 - 売上に効く要因の特定）")
    df = st.session_state.get("df")
    if df is None:
        st.info("Dataタブで整備を完了してください。")
        return

    st.markdown("""
    集計で見えるパターンに**交絡がないか検証**するためのモデルです。
    3つの目的変数それぞれについて特徴量の重要度を計算します。
    """)

    # 設定
    with st.expander("⚙️ モデル設定", expanded=True):
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            include_owner = st.checkbox("営業担当者を含める", value=True)
        with sc2:
            include_month = st.checkbox("月を含める", value=True)
        with sc3:
            n_est = st.slider("推定器数（多い=精度↑ 速度↓）", 50, 300, 100, 50)

    features = get_model_features(df, include_owner=include_owner, include_month=include_month)

    st.caption(f"投入特徴量: {len(features)}個")
    with st.expander("特徴量一覧"):
        st.write(features)

    if st.button("🚀 モデル実行", type="primary", use_container_width=True):

        # --- Model A: Qualified ---
        st.markdown("---")
        st.markdown("### Model A: Qualified予測（面談に進むかどうか）")
        df["_target_qualified"] = df["_is_qualified"].astype(int)
        imp_q = feature_importance_classification(df, features, "_target_qualified", n_estimators=n_est)

        if imp_q is not None:
            auc = imp_q["auc_cv"].iloc[0]
            if auc is not None:
                st.metric("CV AUC", f"{auc:.3f}")
            _plot_importance(imp_q, "Qualified予測の特徴量重要度")
        else:
            st.warning("Qualifiedのサンプルが少なすぎてモデル構築できませんでした。")

        # --- Model B: Won (within Qualified) ---
        st.markdown("---")
        st.markdown("### Model B: 成約予測（Qualified内で成約するか）")
        q_df = df[df["_is_qualified"] == True].copy()
        q_df["_target_won"] = q_df["_is_won"].astype(int)
        imp_w = feature_importance_classification(q_df, features, "_target_won", n_estimators=n_est)

        if imp_w is not None:
            auc_w = imp_w["auc_cv"].iloc[0]
            if auc_w is not None:
                st.metric("CV AUC", f"{auc_w:.3f}")
            _plot_importance(imp_w, "成約予測の特徴量重要度（Qualified内）")
        else:
            st.warning("成約サンプルが少なすぎてモデル構築できませんでした。")

        # --- Model C: Revenue Regression ---
        st.markdown("---")
        st.markdown("### Model C: 成約単価予測（成約行のみ）")
        imp_r = feature_importance_regression(df, features, n_estimators=n_est)

        if imp_r is not None:
            r2 = imp_r["r2_cv"].iloc[0]
            if r2 is not None:
                st.metric("CV R²", f"{r2:.3f}")
            _plot_importance(imp_r, "成約単価の特徴量重要度")
        else:
            st.warning("成約行が少なすぎてモデル構築できませんでした。")

        # --- 交絡チェック ---
        st.markdown("---")
        st.markdown("### 🔍 交絡チェック：担当者/月を外した場合の比較")
        st.caption("担当者や月を外すと重要度がどう変わるか確認できます（設定で切り替え）")

    else:
        st.info("上の「モデル実行」ボタンを押すと、GBM（勾配ブースティング）による特徴量重要度分析を行います。")

        st.markdown("---")
        st.markdown("#### 💡 このタブの使い方")
        st.markdown("""
        1. **Model A（Qualified予測）**: どの要因が面談に進む確率を上げるか
        2. **Model B（成約予測）**: Qualified後、どの要因が成約確率を上げるか  
        3. **Model C（単価予測）**: 成約した案件で、どの要因が単価に影響するか
        
        営業担当者や月を含める/外すことで、広告チャネルの**純粋な効果**と**交絡**を区別できます。
        """)


def _plot_importance(imp_df: pd.DataFrame, title: str):
    top = imp_df.head(15).copy()
    top["feature_short"] = top["feature"].str.replace("_contrib__", "貢献:").str.replace("_", "")
    fig = px.bar(
        top, x="importance", y="feature_short",
        orientation="h",
        color="importance",
        color_continuous_scale="Viridis",
    )
    fig.update_layout(
        title=title,
        height=max(300, len(top) * 28),
        yaxis=dict(autorange="reversed"),
        showlegend=False,
        margin=dict(l=0, r=0, t=40, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("重要度データ"):
        st.dataframe(imp_df, use_container_width=True)
