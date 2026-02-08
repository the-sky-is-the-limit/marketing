import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from logic.metrics import funnel_kpis, group_funnel


def _format_pct(v):
    return f"{v*100:.1f}%"


def render_funnel_tab():
    st.subheader("🔄 Funnel（資料請求 → Qualified → 成約）")
    df = st.session_state.get("df")
    if df is None:
        st.info("Dataタブで整備を完了してください。")
        return

    # --- フィルタ ---
    with st.expander("🔍 フィルタ", expanded=False):
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            months = sorted(df["_month"].dropna().unique())
            sel_months = st.multiselect("月", months, default=months, key="funnel_months")
        with fc2:
            owners = sorted(df["_sales_owner"].unique())
            sel_owners = st.multiselect("営業担当者", owners, default=owners, key="funnel_owners")
        with fc3:
            assets = sorted(df["_asset_band"].dropna().unique())
            sel_assets = st.multiselect("純金融資産", [str(a) for a in assets], default=[str(a) for a in assets], key="funnel_assets")

    mask = (
        df["_month"].isin(sel_months)
        & df["_sales_owner"].isin(sel_owners)
        & df["_asset_band"].astype(str).isin(sel_assets)
    )
    fdf = df[mask]

    if len(fdf) == 0:
        st.warning("フィルタ条件に該当するデータがありません。")
        return

    # --- 全体KPI ---
    k = funnel_kpis(fdf)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Leads", f"{int(k['leads']):,}")
    c2.metric("Qualified", f"{int(k['qualified']):,}", _format_pct(k['qualified_rate']))
    c3.metric("成約", f"{int(k['won']):,}", _format_pct(k['won_rate']))
    c4.metric("成約/Qualified", _format_pct(k['won_rate_in_qualified']))
    c5.metric("売上合計", f"¥{k['revenue_sum']:,.0f}")
    c6.metric("成約単価中央値", f"¥{k['median_ticket']:,.0f}")

    # --- ファネルバー ---
    funnel_data = pd.DataFrame({
        "ステージ": ["資料請求", "Qualified（面談済）", "成約（売上あり）"],
        "件数": [int(k["leads"]), int(k["qualified"]), int(k["won"])],
    })
    fig_funnel = px.funnel(funnel_data, x="件数", y="ステージ",
                           color_discrete_sequence=["#1f77b4", "#2ca02c", "#ff7f0e"])
    fig_funnel.update_layout(height=250, margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig_funnel, use_container_width=True)

    # --- 月次推移 ---
    st.markdown("### 📅 月次推移")
    monthly = group_funnel(fdf, "_month").sort_values("_month")

    fig_monthly = go.Figure()
    fig_monthly.add_trace(go.Bar(
        x=monthly["_month"], y=monthly["leads"],
        name="Leads", marker_color="#d9d9d9", yaxis="y2", opacity=0.4,
    ))
    fig_monthly.add_trace(go.Scatter(
        x=monthly["_month"], y=monthly["qualified_rate"],
        name="Qualified率", mode="lines+markers", marker_color="#2ca02c",
    ))
    fig_monthly.add_trace(go.Scatter(
        x=monthly["_month"], y=monthly["won_rate"],
        name="成約率", mode="lines+markers", marker_color="#ff7f0e",
    ))
    fig_monthly.update_layout(
        yaxis=dict(title="率", tickformat=".0%", range=[0, max(monthly["qualified_rate"].max() * 1.3, 0.05)]),
        yaxis2=dict(title="Leads", overlaying="y", side="right"),
        height=350, legend=dict(orientation="h", y=-0.2),
        margin=dict(l=0, r=0, t=30, b=0),
    )
    st.plotly_chart(fig_monthly, use_container_width=True)

    with st.expander("月次データ詳細"):
        display_cols = ["_month", "leads", "qualified", "won", "qualified_rate", "won_rate", "won_rate_in_qualified", "revenue_sum"]
        st.dataframe(monthly[display_cols], use_container_width=True)

    # --- 営業担当者別 ---
    st.markdown("### 👤 営業担当者別")
    by_owner = group_funnel(fdf, "_sales_owner")
    by_owner = by_owner[by_owner["_sales_owner"] != ""].sort_values("won_rate_in_qualified", ascending=False)

    fig_owner = go.Figure()
    fig_owner.add_trace(go.Bar(x=by_owner["_sales_owner"], y=by_owner["qualified_rate"], name="Qualified率", marker_color="#2ca02c"))
    fig_owner.add_trace(go.Bar(x=by_owner["_sales_owner"], y=by_owner["won_rate_in_qualified"], name="成約率(Qualified内)", marker_color="#ff7f0e"))
    fig_owner.update_layout(
        barmode="group", yaxis_tickformat=".0%",
        height=300, margin=dict(l=0, r=0, t=30, b=0),
    )
    st.plotly_chart(fig_owner, use_container_width=True)

    with st.expander("担当者別データ詳細"):
        st.dataframe(by_owner, use_container_width=True)
