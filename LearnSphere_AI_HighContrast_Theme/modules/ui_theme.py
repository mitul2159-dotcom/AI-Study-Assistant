import streamlit as st


def apply_theme():
    """Apply a high-contrast, consistent light theme to every LearnSphere page."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');

        :root {
            color-scheme: light;
            --ink: #172033;
            --muted: #526078;
            --brand: #5145e5;
            --brand-dark: #3d32bd;
            --teal: #0f766e;
            --panel: #ffffff;
            --line: #dce3ef;
            --text-color: #172033;
            --background-color: #f5f7fc;
            --secondary-background-color: #edf1f8;
            --primary-color: #5145e5;
        }

        html, body, [class*="css"], [data-testid="stAppViewContainer"] {
            font-family: 'DM Sans', sans-serif;
            color: var(--ink);
        }
        .stApp {
            background:
                radial-gradient(ellipse at 8% 0%, rgba(99,91,255,.09), transparent 34%),
                radial-gradient(ellipse at 92% 8%, rgba(20,184,166,.07), transparent 30%),
                #f5f7fc !important;
            color: #172033 !important;
        }

        /* Explicit text colors fix the pale labels and numbers in the screenshots. */
        .stApp p, .stApp li, .stApp label, .stApp .stMarkdown,
        .stApp [data-testid="stWidgetLabel"],
        .stApp [data-testid="stWidgetLabel"] p,
        .stApp [data-testid="stCaptionContainer"],
        .stApp [data-testid="stCaptionContainer"] p,
        .stApp [data-testid="stMetricLabel"],
        .stApp [data-testid="stMetricLabel"] p,
        .stApp [data-testid="stMetricValue"],
        .stApp [data-testid="stMetricDelta"],
        .stApp [data-testid="stMarkdownContainer"] p,
        .stApp [data-testid="stMarkdownContainer"] li {
            color: #172033 !important;
        }
        .stApp [data-testid="stCaptionContainer"],
        .stApp [data-testid="stMetricLabel"],
        .stApp .small-muted { color: #526078 !important; }

        h1, h2, h3, h4, h5, h6 {
            font-family: 'Manrope', sans-serif !important;
            letter-spacing: -.025em;
            color: #172033 !important;
        }
        h1 { font-weight: 800 !important; }
        [data-testid="stHeader"] { background: rgba(245,247,252,.92) !important; }

        /* Sidebar remains dark, with readable text. */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #111827 0%, #25205b 100%) !important;
            border-right: 1px solid rgba(255,255,255,.08);
        }
        [data-testid="stSidebar"] * { color: #f8fafc !important; }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
            color: #d5deec !important;
        }

        /* Metric cards */
        div[data-testid="stMetric"] {
            background: #ffffff !important;
            border: 1px solid #dce3ef !important;
            padding: 18px 20px;
            border-radius: 18px;
            box-shadow: 0 7px 22px rgba(30,41,59,.045);
        }
        div[data-testid="stMetricLabel"], div[data-testid="stMetricLabel"] * {
            color: #526078 !important;
            opacity: 1 !important;
        }
        div[data-testid="stMetricValue"], div[data-testid="stMetricValue"] * {
            color: #172033 !important;
            opacity: 1 !important;
            font-weight: 750 !important;
        }
        div[data-testid="stMetricDelta"] { opacity: 1 !important; }

        /* Buttons and page navigation */
        div.stButton > button, div.stFormSubmitButton > button,
        [data-testid="stPageLink"] a {
            border-radius: 12px;
            border: 1px solid #5145e5;
            background: linear-gradient(110deg, #5145e5, #7066f4) !important;
            color: #ffffff !important;
            font-weight: 700;
            padding: .62rem 1rem;
            box-shadow: 0 5px 14px rgba(81,69,229,.16);
            transition: transform .15s ease, box-shadow .15s ease;
        }
        div.stButton > button *, div.stFormSubmitButton > button * { color: #ffffff !important; }
        div.stButton > button:hover, div.stFormSubmitButton > button:hover {
            color: #ffffff !important;
            border-color: #3d32bd;
            transform: translateY(-1px);
            box-shadow: 0 8px 20px rgba(81,69,229,.23);
        }
        div.stButton > button:disabled, div.stFormSubmitButton > button:disabled {
            background: #e6e9f2 !important;
            border-color: #d4d9e5 !important;
            color: #657087 !important;
            box-shadow: none !important;
        }

        /* Containers and upload areas */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 18px;
            border-color: #dce3ef !important;
            background: rgba(255,255,255,.96) !important;
        }
        div[data-testid="stFileUploader"] section {
            border-radius: 16px;
            border: 1px dashed #8580ec !important;
            background: #ffffff !important;
        }
        div[data-testid="stFileUploader"] section *,
        div[data-testid="stFileUploader"] small,
        div[data-testid="stFileUploader"] [data-testid="stMarkdownContainer"] {
            color: #344054 !important;
            opacity: 1 !important;
        }
        div[data-testid="stFileUploader"] button {
            background: #5145e5 !important;
            color: #ffffff !important;
            border: 1px solid #5145e5 !important;
        }
        div[data-testid="stFileUploader"] button * { color: #ffffff !important; }

        /* Inputs, dropdowns, text areas and their options */
        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div,
        div[data-baseweb="textarea"] > div,
        textarea, input {
            border-radius: 10px !important;
            background-color: #ffffff !important;
            color: #172033 !important;
            border-color: #cbd5e1 !important;
        }
        div[data-baseweb="select"] *,
        div[data-baseweb="input"] *,
        div[data-baseweb="textarea"] *,
        textarea, input {
            color: #172033 !important;
        }
        [data-baseweb="popover"], [data-baseweb="menu"],
        [role="listbox"], [role="option"] {
            background: #ffffff !important;
            color: #172033 !important;
        }
        [role="option"] * { color: #172033 !important; }
        [data-testid="stRadio"] label, [data-testid="stCheckbox"] label {
            color: #172033 !important;
        }
        [data-testid="stSlider"] [data-testid="stTickBar"] { color: #526078 !important; }

        /* Intentional dark hero panel; keep its text white. */
        .hero-panel {
            padding: 30px 32px;
            border-radius: 24px;
            background: linear-gradient(115deg, #171b3b 0%, #39318a 54%, #0f766e 100%);
            color: #ffffff !important;
            box-shadow: 0 18px 45px rgba(43,45,105,.18);
            margin: 8px 0 24px 0;
        }
        .hero-panel h1, .hero-panel h2, .hero-panel p, .hero-panel span {
            color: #ffffff !important;
        }
        .hero-eyebrow {
            text-transform: uppercase;
            letter-spacing: .16em;
            font-size: .76rem;
            font-weight: 800;
            opacity: .9;
        }
        .hero-sub { color: #eef2ff !important; font-size: 1.05rem; max-width: 780px; line-height: 1.7; }
        .feature-kicker { color: #5145e5 !important; font-weight: 800; text-transform: uppercase; letter-spacing: .1em; font-size: .72rem; }
        .small-muted { color: #526078 !important; font-size: .92rem; }
        hr { border-color: #dce3ef !important; }
        footer { visibility: hidden; }
        @media (max-width: 800px) { .hero-panel { padding: 22px; } }
        </style>
        """,
        unsafe_allow_html=True,
    )
