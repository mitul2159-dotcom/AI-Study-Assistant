import streamlit as st

def apply_theme():
    """Consistent visual styling shared by all pages."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
        :root { --ink:#172033; --muted:#667085; --brand:#635bff; --brand2:#14b8a6; }
        html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
        .stApp { background: radial-gradient(ellipse at 8% 0%, rgba(99,91,255,.10), transparent 33%), radial-gradient(ellipse at 92% 8%, rgba(20,184,166,.08), transparent 28%), #f7f8fc; color:var(--ink); }
        h1,h2,h3 { font-family:'Manrope',sans-serif !important; letter-spacing:-.035em; color:#172033; }
        h1 { font-weight:800 !important; }
        [data-testid="stSidebar"] { background:linear-gradient(180deg,#111827 0%,#1e1b4b 100%); }
        [data-testid="stSidebar"] * { color:#f8fafc !important; }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:#cbd5e1 !important; }
        [data-testid="stHeader"] { background:rgba(247,248,252,.78); }
        div[data-testid="stMetric"] { background:rgba(255,255,255,.92); border:1px solid #e7eaf2; padding:18px 20px; border-radius:18px; box-shadow:0 6px 20px rgba(30,41,59,.035); }
        div[data-testid="stMetricLabel"] { color:#667085; }
        div.stButton > button, div.stFormSubmitButton > button { border-radius:12px; border:0; background:linear-gradient(110deg,#635bff,#8178ff); color:white; font-weight:700; padding:.62rem 1rem; box-shadow:0 5px 14px rgba(99,91,255,.18); transition:transform .15s ease, box-shadow .15s ease; }
        div.stButton > button:hover, div.stFormSubmitButton > button:hover { color:white; transform:translateY(-1px); box-shadow:0 8px 20px rgba(99,91,255,.24); }
        div[data-testid="stVerticalBlockBorderWrapper"] { border-radius:18px; border-color:#e6e9f2; background:rgba(255,255,255,.78); }
        div[data-testid="stFileUploader"] section { border-radius:16px; border:1px dashed #a5a6f6; background:#fbfbff; }
        div[data-baseweb="input"] > div, div[data-baseweb="select"] > div, textarea { border-radius:10px !important; }
        .hero-panel { padding:30px 32px; border-radius:24px; background:linear-gradient(115deg,#171b3b 0%,#39318a 54%,#0f766e 100%); color:white; box-shadow:0 18px 45px rgba(43,45,105,.18); margin:8px 0 24px 0; }
        .hero-panel h1,.hero-panel h2,.hero-panel p,.hero-panel span { color:white !important; }
        .hero-eyebrow { text-transform:uppercase; letter-spacing:.16em; font-size:.76rem; font-weight:800; opacity:.78; }
        .hero-sub { color:#e0e7ff !important; font-size:1.05rem; max-width:780px; line-height:1.7; }
        .feature-kicker { color:#635bff; font-weight:800; text-transform:uppercase; letter-spacing:.1em; font-size:.72rem; }
        .small-muted { color:#667085; font-size:.92rem; }
        hr { border-color:#e7eaf2; }
        footer { visibility:hidden; }
        @media (max-width: 800px) { .hero-panel { padding:22px; } }
        </style>
        """,
        unsafe_allow_html=True,
    )
