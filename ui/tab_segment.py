import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from logic.metrics import pivot_segment, pivot_segment_count, group_funnel


def render_segment_tab():
    st.subheader("🎯 Segment（年代 × 純金融資産）")
    df = st.session_state.get("df")
    if df is None:
        st.info("Dataタブで整備を完了してください。")
        return

    # 指標選択
    metric_options = {
        "Qualified率": "qualified_rate",
        "成約率（全体）": "won_rate",
        "成約率（Qualified内）": "won_rate_in_qualified",
        "成約単価中央値": "median_ticket",
        "売上合計": "revenue_sum",
    }

    sel_label = st.selectbox("表示指標", list(metric_options.keys()), index=0)
    metric = metric_options[sel_label]

    col1, col2 = st.columns(2)

    # ヒートマップ
    with col1:
        st.markdown(f"#### {sel_label}（ヒートマップ）")
        p = pivot_segment(df, "_age_band", "_asset_band", metric)
        if len(p) > 0:
            is_pct = metric in ("qualified_rate", "won_rate", "won_rate_in_qualified")
            fmt = ".1%" if is_pct else ",.0f"

            fig = px.imshow(
                p.astype(float),
                aspect="auto",
                color_continuous_scale="YlOrRd",
                text_auto=fmt,
            )
            fig.update_layout(
                height=400,
                xaxis_title="純金融資産",
                yaxis_title="年代",
                margin=dict(l=0, r=0, t=30, b=0),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("データが不足しています。")

    # サンプルサイズ
    with col2:
        st.markdown("#### リード数（サンプルサイズ）")
        cnt = pivot_segment_count(df, "_age_band", "_asset_band")
        if len(cnt) > 0:
            fig_cnt = px.imshow(
                cnt.astype(float),
                aspect="auto",
                color_continuous_scale="Blues",
                text_auto=".0f",
            )
            fig_cnt.update_layout(
                height=400,
                xaxis_title="純金融資産",
                yaxis_title="年代",
                margin=dict(l=0, r=0, t=30, b=0),
            )
            st.plotly_chart(fig_cnt, use_container_width=True)

    # 年代別・資産別のファネルテーブル
    st.markdown("---")
    tc1, tc2 = st.columns(2)

    with tc1:
        st.markdown("#### 年代別ファネル")
        age_funnel = group_funnel(df, "_age_band")
        age_funnel = age_funnel.sort_values("_age_band")
        disp_cols = ["_age_band", "leads", "qualified", "won", "qualified_rate", "won_rate_in_qualified", "revenue_sum", "median_ticket"]
        st.dataframe(age_funnel[[c for c in disp_cols if c in age_funnel.columns]], use_container_width=True)

    with tc2:
        st.markdown("#### 純金融資産別ファネル")
        asset_funnel = group_funnel(df, "_asset_band")
        asset_funnel = asset_funnel.sort_values("_asset_band")
        st.dataframe(asset_funnel[[c for c in disp_cols if c in asset_funnel.columns].copy().rename(columns={"_age_band": "_asset_band"})], use_container_width=True)

    # 勝ち筋セグメント自動検出
    st.markdown("---")
    st.markdown("#### 🏆 勝ち筋セグメント候補")
    st.caption("成約実績があり、成約率(Qualified内)が高いセグメント")

    results = []
    for (age, asset), grp in df.groupby(["_age_band", "_asset_band"], observed=True):
        n = len(grp)
        q = int(grp["_is_qualified"].sum())
        w = int(grp["_is_won"].sum())
        rev = float(grp["_revenue"].sum())
        if q >= 3 and w >= 1:
            results.append({
                "年代": str(age),
                "資産": str(asset),
                "リード数": n,
                "Qualified": q,
                "成約": w,
                "成約率(Q内)": w / q if q else 0,
                "売上合計": rev,
            })
    if results:
        winners = pd.DataFrame(results).sort_values("成約率(Q内)", ascending=False).head(10)
        st.dataframe(winners, use_container_width=True)
    else:
        st.info("条件を満たすセグメントが見つかりませんでした。")
