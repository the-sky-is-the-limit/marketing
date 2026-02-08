import streamlit as st
import pandas as pd
from logic.schema import ColumnMap, STD_COLS
from logic.preprocess import preprocess


def render_data_tab():
    st.subheader("📥 Data（Excel取り込み・整備）")

    uploaded = st.file_uploader("Excelファイル（.xlsx）をアップロード", type=["xlsx", "xls"])
    if not uploaded:
        st.info("Excelをアップロードしてください。")
        return

    xls = pd.ExcelFile(uploaded)
    sheet = st.selectbox("読み込むシート", options=xls.sheet_names, index=0)
    df_raw = pd.read_excel(uploaded, sheet_name=sheet)
    st.session_state.df_raw = df_raw

    st.caption(f"プレビュー（{len(df_raw):,}行 × {len(df_raw.columns)}列）")
    st.dataframe(df_raw.head(15), use_container_width=True, height=300)

    # 列マッピング
    st.markdown("#### 列マッピング")
    st.caption("Excel列名が標準名と一致していれば自動マッピングされます。ズレている場合は手動で修正してください。")
    cols = list(df_raw.columns)
    default_map = ColumnMap.default_from_df_columns(cols).mapping

    colmap = {}
    col_left, col_right = st.columns(2)
    items = list(STD_COLS.items())

    for i, (internal, excel_expected) in enumerate(items):
        with (col_left if i % 2 == 0 else col_right):
            options = ["(なし)"] + cols
            default_idx = 0
            if default_map.get(internal) in cols:
                default_idx = options.index(default_map[internal])
            selected = st.selectbox(
                f"**{internal}** ← {excel_expected}",
                options=options,
                index=default_idx,
                key=f"map_{internal}",
            )
        if selected != "(なし)":
            colmap[internal] = selected

    if st.button("🔄 整備して分析タブへ反映", type="primary", use_container_width=True):
        df, meta = preprocess(df_raw, colmap)
        st.session_state.df = df
        st.session_state.meta = meta
        st.session_state.colmap = colmap
        st.success("✅ 整備完了！上部のタブで分析できます。")

    if st.session_state.get("df") is not None:
        meta = st.session_state.meta
        st.markdown("---")
        st.markdown("#### 整備結果サマリ")

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("総リード数", f"{meta.get('rows', 0):,}")
        m2.metric("Qualified数", f"{meta.get('qualified_count', 0):,}")
        m3.metric("成約数", f"{meta.get('won_count', 0):,}")
        m4.metric("売上合計", f"¥{meta.get('revenue_sum', 0):,.0f}")
        m5.metric("期間", meta.get("date_range", "N/A"))

        if meta.get("missing_required"):
            st.warning(f"⚠️ 未マッピング必須列: {meta['missing_required']}")

        st.caption(
            f"マルチタッチ率（貢献フラグ2つ以上TRUE）: "
            f"{meta.get('contrib_multi_touch_rate', 0)*100:.1f}%"
        )
