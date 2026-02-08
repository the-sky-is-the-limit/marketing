import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from logic.attribution import rank_by_metric, contrib_flag_table


def render_channel_tab():
    st.subheader("📊 Channel / Campaign（上流と下流を分けて比較）")
    df = st.session_state.get("df")
    if df is None:
        st.info("Dataタブで整備を完了してください。")
        return

    # 上流/下流切替
    view = st.radio(
        "分析ステージ",
        ["上流：全リード → Qualified", "下流：Qualified → 成約"],
        horizontal=True,
    )

    if view.startswith("上流"):
        base_df = df.copy()
        metric = "qualified_rate"
        metric_label = "Qualified率"
    else:
        base_df = df[df["_is_qualified"] == True].copy()
        metric = "won_rate_in_qualified"
        metric_label = "成約率(Qualified内)"

    min_leads = st.slider("最小母数（少ないグループを除外）", 3, 100, 10, 1)

    # --- UTM別ランキング ---
    st.markdown("### 🏷️ UTM別ランキング")

    utm_options = {
        "utm_source": "_utm_source",
        "utm_campaign": "_utm_campaign",
        "utm_medium": "_utm_medium",
        "utm_content": "_utm_content",
        "リードソース": "_lead_source",
    }

    tc1, tc2 = st.columns([1, 3])
    with tc1:
        utm_label = st.selectbox("グルーピング", list(utm_options.keys()), index=0)
    utm_key = utm_options[utm_label]

    t = rank_by_metric(base_df, utm_key, metric, min_leads=min_leads)

    if len(t) > 0:
        # グラフ
        top_n = min(20, len(t))
        t_top = t.head(top_n)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=t_top[utm_key], y=t_top[metric],
            name=metric_label, marker_color="#2ca02c",
        ))
        fig.add_trace(go.Scatter(
            x=t_top[utm_key], y=t_top["leads"],
            name="Leads", mode="lines+markers", marker_color="#d62728",
            yaxis="y2",
        ))
        fig.update_layout(
            yaxis=dict(title=metric_label, tickformat=".0%"),
            yaxis2=dict(title="Leads", overlaying="y", side="right"),
            height=350, margin=dict(l=0, r=0, t=30, b=0),
            legend=dict(orientation="h", y=-0.2),
        )
        st.plotly_chart(fig, use_container_width=True)

        # テーブル
        with st.expander("詳細データ"):
            display_cols = [utm_key, "leads", "qualified", "won", "qualified_rate",
                           "won_rate", "won_rate_in_qualified", "revenue_sum", "median_ticket"]
            st.dataframe(t[[c for c in display_cols if c in t.columns]], use_container_width=True)
    else:
        st.info(f"母数{min_leads}以上のグループがありません。フィルタを緩めてください。")

    # --- utm_source × utm_campaign のクロス集計 ---
    st.markdown("### 🔀 Source × Campaign クロス")
    cross = base_df.groupby(["_utm_source", "_utm_campaign"]).apply(
        lambda g: pd.Series({
            "leads": len(g),
            "qualified": int(g["_is_qualified"].sum()),
            "won": int(g["_is_won"].sum()),
            "qualified_rate": g["_is_qualified"].mean(),
            "won_rate": g["_is_won"].mean(),
            "revenue": g["_revenue"].sum(),
        })
    ).reset_index()
    cross = cross[cross["leads"] >= min_leads].sort_values("revenue", ascending=False)

    if len(cross):
        with st.expander("Source × Campaign 詳細", expanded=True):
            st.dataframe(cross.head(30), use_container_width=True)

    # --- 貢献フラグ ---
    st.markdown("### 🏴 貢献フラグ別ファネル")
    st.caption("各広告貢献フラグがTRUEの行のみでファネルKPIを計算")

    contrib_cols = st.session_state.get("meta", {}).get("contrib_cols", [])
    if not contrib_cols:
        st.info("貢献フラグ列が見つかりませんでした。")
        return

    tf = contrib_flag_table(base_df, contrib_cols)
    tf = tf[tf["leads"] >= 1].sort_values(metric, ascending=False)

    if len(tf):
        fig_contrib = px.bar(
            tf, x="flag", y=metric,
            color="leads", color_continuous_scale="Blues",
            text=tf[metric].apply(lambda x: f"{x*100:.1f}%"),
        )
        fig_contrib.update_layout(
            height=350,
            xaxis_title="貢献フラグ",
            yaxis_title=metric_label,
            yaxis_tickformat=".0%",
            margin=dict(l=0, r=0, t=30, b=0),
        )
        fig_contrib.update_xaxes(tickangle=45)
        st.plotly_chart(fig_contrib, use_container_width=True)

        with st.expander("貢献フラグ詳細データ"):
            st.dataframe(tf, use_container_width=True)
    else:
        st.info("条件を満たす貢献フラグがありません。")
