
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from modules.multilingual_assistant import explain_topic


st.set_page_config(
    page_title="Multilingual Learning Assistant",
    page_icon="🌍",
    layout="wide",
)

from modules.ui_theme import apply_theme
apply_theme()

st.title("🌍 Multilingual Learning Assistant")

st.write(
    "Learn difficult concepts in your preferred language, "
    "at your own learning level."
)

st.divider()

LANGUAGES = [
    "English",
    "Hindi",
    "Spanish",
    "French",
    "German",
    "Tamil",
    "Telugu",
    "Bengali",
    "Marathi",
    "Urdu",
]

LEVELS = [
    "Beginner",
    "Intermediate",
    "Advanced",
]

with st.form("multilingual_learning_form"):
    topic = st.text_area(
        "What would you like to learn?",
        placeholder=(
            "Example: Explain artificial intelligence, "
            "photosynthesis, or database normalization."
        ),
        height=100,
    )

    col1, col2 = st.columns(2)

    with col1:
        language = st.selectbox(
            "Choose your explanation language",
            LANGUAGES,
        )

    with col2:
        level = st.selectbox(
            "Choose your learning level",
            LEVELS,
        )

    include_example = st.checkbox(
        "Include a practical example",
        value=True,
    )

    submitted = st.form_submit_button(
        "✨ Explain This Topic",
        use_container_width=True,
    )

if submitted:
    if not topic.strip():
        st.warning("Please enter a topic first.")
    else:
        try:
            with st.spinner(
                f"Preparing your explanation in {language}..."
            ):
                explanation = explain_topic(
                    topic=topic,
                    language=language,
                    level=level,
                    include_example=include_example,
                )

            st.session_state["multilingual_explanation"] = explanation
            st.session_state["multilingual_topic"] = topic
            st.session_state["multilingual_language"] = language

        except Exception as error:
            st.error(
                "Unable to generate the explanation. "
                "Check that Ollama is running and the model is installed."
            )
            st.code(str(error), language="text")

if st.session_state.get("multilingual_explanation"):
    st.divider()
    st.subheader(
        "📘 Your Explanation: "
        + st.session_state.get("multilingual_topic", "")
    )

    st.caption(
        "Language: "
        + st.session_state.get("multilingual_language", "")
    )

    st.markdown(st.session_state["multilingual_explanation"])

    st.download_button(
        "⬇️ Download Explanation",
        data=st.session_state["multilingual_explanation"],
        file_name="study_explanation.txt",
        mime="text/plain",
    )

st.divider()

st.caption("AI-Powered Personalized Study Assistant")
