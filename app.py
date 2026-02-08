import sys
from pathlib import Path

# Streamlit Cloud: ensure app root is on sys.path
APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import streamlit as st

st.set_page_config(
    page_title="Marketing Funnel Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# CSS
st.markdown("""
<style>
    .stMetric .css-1xarl3l { font-size: 1.1rem; }
    div[data-testid="stMetricValue"] { font-size: 1.4rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 20px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

from ui.tab_data import render_data_tab
from ui.tab_funnel import render_funnel_tab
from ui.tab_segment import render_segment_tab
from ui.tab_channel import render_channel_tab
from ui.tab_model import render_model_tab

st.title("📊 Marketing Funnel Analyzer")
st.caption("資料請求 → Qualified（面談済） → 成約（売上あり）のファネルを多角的に分析")

# Session state init
for key in ["df_raw", "df", "meta", "filters", "colmap"]:
    if key not in st.session_state:
        st.session_state[key] = None if key != "filters" else {}

tabs = st.tabs([
    "📥 Data",
    "🔄 Funnel",
    "🎯 Segment",
    "📊 Channel/Campaign",
    "🧪 Drivers(Model)",
])

with tabs[0]:
    render_data_tab()
with tabs[1]:
    render_funnel_tab()
with tabs[2]:
    render_segment_tab()
with tabs[3]:
    render_channel_tab()
with tabs[4]:
    render_model_tab()
