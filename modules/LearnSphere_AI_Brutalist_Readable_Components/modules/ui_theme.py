import streamlit as st


def apply_theme():
    """Apply a bold neo-brutalist theme with high contrast across LearnSphere AI."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Space+Mono:wght@400;700&display=swap');

        :root {
            color-scheme: light;
            --ink: #171717;
            --muted: #44403c;
            --paper: #fffdf5;
            --panel: #ffffff;
            --line: #171717;
            --red: #ff5a36;
            --yellow: #ffe66d;
            --blue: #9de4ff;
            --green: #b8f28b;
            --primary-color: #ff5a36;
            --background-color: #fffdf5;
            --secondary-background-color: #f3eedf;
        }

        html, body, [class*="css"], [data-testid="stAppViewContainer"] {
            font-family: 'Space Grotesk', sans-serif;
            color: var(--ink);
        }
        .stApp {
            background-color: var(--paper) !important;
            background-image: radial-gradient(#d8d1bf 0.8px, transparent 0.8px) !important;
            background-size: 18px 18px !important;
            color: var(--ink) !important;
        }
        [data-testid="stMainBlockContainer"] { padding-top: 2rem; padding-bottom: 3rem; }

        /* High contrast text everywhere, including captions and widget labels. */
        .stApp p, .stApp li, .stApp label, .stApp .stMarkdown,
        .stApp [data-testid="stWidgetLabel"], .stApp [data-testid="stWidgetLabel"] p,
        .stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stCaptionContainer"] p,
        .stApp [data-testid="stMetricLabel"], .stApp [data-testid="stMetricValue"],
        .stApp [data-testid="stMetricDelta"], .stApp [data-testid="stMarkdownContainer"] p,
        .stApp [data-testid="stMarkdownContainer"] li { color: var(--ink) !important; opacity: 1 !important; }
        .stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stMetricLabel"],
        .stApp .small-muted { color: var(--muted) !important; }
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Space Grotesk', sans-serif !important;
            color: var(--ink) !important;
            letter-spacing: -0.045em;
            font-weight: 700 !important;
        }
        h1 { text-transform: uppercase; line-height: 1.02 !important; }
        h2 { border-bottom: 3px solid var(--ink); padding-bottom: .35rem; }
        [data-testid="stHeader"] { background: rgba(255,253,245,.96) !important; }

        /* Sidebar: ink-black panel with acid-yellow accents. */
        [data-testid="stSidebar"] {
            background: #171717 !important;
            border-right: 3px solid #171717 !important;
        }
        [data-testid="stSidebar"] * { color: #fffdf5 !important; }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color: #f4eccc !important; }
        [data-testid="stSidebar"] hr { border-color: #5c574a !important; }
        [data-testid="stSidebar"] [data-testid="stPageLink"] a { background: var(--yellow) !important; color: var(--ink) !important; }

        /* Metric cards: flat white, thick ink border, offset shadow. */
        div[data-testid="stMetric"] {
            background: var(--panel) !important;
            border: 2px solid var(--ink) !important;
            border-radius: 2px !important;
            padding: 18px 20px !important;
            box-shadow: 5px 5px 0 var(--ink) !important;
        }
        div[data-testid="stMetricLabel"], div[data-testid="stMetricLabel"] * {
            color: var(--muted) !important; opacity: 1 !important; font-weight: 700 !important;
        }
        div[data-testid="stMetricValue"], div[data-testid="stMetricValue"] * {
            color: var(--ink) !important; opacity: 1 !important; font-weight: 700 !important;
        }
        div[data-testid="stMetricDelta"] { opacity: 1 !important; }

        /* Strong, tactile buttons. */
        div.stButton > button, div.stFormSubmitButton > button,
        [data-testid="stPageLink"] a, [data-testid="stDownloadButton"] button {
            border-radius: 2px !important;
            border: 2px solid var(--ink) !important;
            background: var(--red) !important;
            color: var(--ink) !important;
            font-weight: 700 !important;
            padding: .62rem 1rem !important;
            box-shadow: 4px 4px 0 var(--ink) !important;
            transition: transform .12s ease, box-shadow .12s ease !important;
        }
        div.stButton > button *, div.stFormSubmitButton > button *,
        [data-testid="stPageLink"] a *, [data-testid="stDownloadButton"] button * { color: var(--ink) !important; }
        div.stButton > button:hover, div.stFormSubmitButton > button:hover,
        [data-testid="stPageLink"] a:hover, [data-testid="stDownloadButton"] button:hover {
            transform: translate(2px, 2px) !important;
            box-shadow: 2px 2px 0 var(--ink) !important;
            background: var(--yellow) !important;
        }
        div.stButton > button:disabled, div.stFormSubmitButton > button:disabled {
            background: #e7e2d5 !important; border-color: #777064 !important;
            color: #625d53 !important; box-shadow: 2px 2px 0 #777064 !important;
        }

        /* Panels and feature cards use squared corners and hard shadows. */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border: 2px solid var(--ink) !important;
            border-radius: 2px !important;
            background: #ffffff !important;
            box-shadow: 5px 5px 0 var(--ink) !important;
        }
        div[data-testid="stFileUploader"] section {
            border-radius: 2px !important;
            border: 2px dashed var(--ink) !important;
            background: #fff9dc !important;
        }
        div[data-testid="stFileUploader"] section *, div[data-testid="stFileUploader"] small,
        div[data-testid="stFileUploader"] [data-testid="stMarkdownContainer"] {
            color: var(--ink) !important; opacity: 1 !important;
        }
        div[data-testid="stFileUploader"] button {
            background: var(--yellow) !important; color: var(--ink) !important;
            border: 2px solid var(--ink) !important; border-radius: 2px !important;
            box-shadow: 3px 3px 0 var(--ink) !important;
        }
        div[data-testid="stFileUploader"] button * { color: var(--ink) !important; }

        /* Inputs and dropdowns: white with strong outlines, readable menu options. */
        div[data-baseweb="input"] > div, div[data-baseweb="select"] > div,
        div[data-baseweb="textarea"] > div, textarea, input {
            border-radius: 2px !important; background-color: #ffffff !important;
            color: var(--ink) !important; border-color: var(--ink) !important;
        }
        div[data-baseweb="select"] *, div[data-baseweb="input"] *,
        div[data-baseweb="textarea"] *, textarea, input { color: var(--ink) !important; }
        [data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"], [role="option"] {
            background: #ffffff !important; color: var(--ink) !important;
        }
        [role="option"] * { color: var(--ink) !important; }
        [data-testid="stRadio"] label, [data-testid="stCheckbox"] label { color: var(--ink) !important; }
        [data-testid="stSlider"] [data-testid="stTickBar"] { color: var(--ink) !important; }
        input:focus, textarea:focus { outline: 3px solid var(--blue) !important; }

        /* Brutalist home hero: bold block, sticker-like label, no soft gradients. */
        .hero-panel {
            position: relative;
            padding: 34px 34px 30px 34px;
            border: 3px solid var(--ink);
            border-radius: 2px;
            background: var(--yellow);
            color: var(--ink) !important;
            box-shadow: 8px 8px 0 var(--ink);
            margin: 8px 8px 30px 0;
        }
        .hero-panel h1, .hero-panel h2, .hero-panel p, .hero-panel span { color: var(--ink) !important; }
        .hero-eyebrow {
            display: inline-block; background: var(--blue); border: 2px solid var(--ink);
            padding: 5px 9px; text-transform: uppercase; letter-spacing: .12em;
            font-family: 'Space Mono', monospace; font-size: .72rem; font-weight: 700;
        }
        .hero-sub { color: var(--ink) !important; font-size: 1.05rem; max-width: 780px; line-height: 1.65; }
        .feature-kicker {
            display: inline-block; color: var(--ink) !important; background: var(--green);
            border: 2px solid var(--ink); padding: 4px 7px; font-family: 'Space Mono', monospace;
            font-weight: 700; text-transform: uppercase; letter-spacing: .04em; font-size: .72rem;
        }
        .small-muted { color: var(--muted) !important; font-size: .94rem; }
        hr { border-color: var(--ink) !important; border-width: 1px !important; }
        [data-testid="stProgressBar"] > div > div { background: var(--red) !important; }
        [data-testid="stAlert"] { border: 2px solid var(--ink) !important; border-radius: 2px !important; }
        code, pre { border-radius: 2px !important; }

        /* Extra readability pass for common Streamlit components. */
        [data-testid="stTabs"] button {
            color: var(--ink) !important; font-weight: 700 !important;
            border: 2px solid var(--ink) !important; border-radius: 2px !important;
            background: #ffffff !important; margin-right: 6px !important;
        }
        [data-testid="stTabs"] button[aria-selected="true"] {
            color: var(--ink) !important; background: var(--yellow) !important;
            box-shadow: 3px 3px 0 var(--ink) !important;
        }
        [data-testid="stExpander"] {
            border: 2px solid var(--ink) !important; border-radius: 2px !important;
            background: #ffffff !important;
        }
        [data-testid="stExpander"] summary,
        [data-testid="stExpander"] summary *,
        [data-testid="stExpander"] details,
        [data-testid="stExpander"] p { color: var(--ink) !important; opacity: 1 !important; }
        [data-testid="stSelectbox"] label, [data-testid="stMultiSelect"] label,
        [data-testid="stTextInput"] label, [data-testid="stTextArea"] label,
        [data-testid="stNumberInput"] label, [data-testid="stDateInput"] label,
        [data-testid="stTimeInput"] label, [data-testid="stFileUploader"] label,
        [data-testid="stRadio"] > label, [data-testid="stCheckbox"] > label,
        [data-testid="stSlider"] label { color: var(--ink) !important; font-weight: 700 !important; opacity: 1 !important; }
        [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
        [data-testid="stDateInput"] input, [data-testid="stTimeInput"] input,
        [data-testid="stTextArea"] textarea { color: var(--ink) !important; caret-color: var(--ink) !important; }
        [data-testid="stDataFrame"], [data-testid="stTable"] {
            border: 2px solid var(--ink) !important; background: #ffffff !important;
        }
        [data-testid="stAlert"] *, [data-testid="stNotification"] * { opacity: 1 !important; }
        .stApp a:not([data-testid="stPageLink"] a) { color: #0645ad !important; font-weight: 700 !important; }
        .stApp a:focus-visible, button:focus-visible, input:focus-visible,
        textarea:focus-visible, [role="option"]:focus-visible {
            outline: 3px solid #005fcc !important; outline-offset: 2px !important;
        }
        /* Make help text readable without competing with primary labels. */
        [data-testid="stWidgetLabel"] small, [data-testid="stCaptionContainer"] p,
        .stApp small { color: #44403c !important; opacity: 1 !important; }
        footer { visibility: hidden; }
        @media (max-width: 800px) { .hero-panel { padding: 22px; } h1 { font-size: 2rem !important; } }
        </style>
        """,
        unsafe_allow_html=True,
    )
