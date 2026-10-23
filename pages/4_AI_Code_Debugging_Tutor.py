
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from modules.ai_debugging_tutor import (
    debug_code,
    SUPPORTED_LANGUAGES,
)


st.set_page_config(
    page_title="AI Code Debugging Tutor",
    page_icon="🐛",
    layout="wide",
)

st.title("🐛 AI Code Debugging Tutor")

st.write(
    "Understand programming errors, explore possible fixes, "
    "and learn how to write better code."
)

st.info(
    "Your code is analyzed by your configured local Ollama model. "
    "The tutor does not execute your code."
)

st.divider()


# ----------------------------------------------------
# SESSION STATE
# ----------------------------------------------------

if "debugger_answer" not in st.session_state:
    st.session_state["debugger_answer"] = ""

if "debugger_code" not in st.session_state:
    st.session_state["debugger_code"] = ""

if "debugger_language" not in st.session_state:
    st.session_state["debugger_language"] = "Python"


# ----------------------------------------------------
# CODE INPUT
# ----------------------------------------------------

st.header("1. Enter Your Code")

language = st.selectbox(
    "Programming Language",
    SUPPORTED_LANGUAGES,
    index=SUPPORTED_LANGUAGES.index(
        st.session_state["debugger_language"]
    ),
)

if language != st.session_state["debugger_language"]:
    st.session_state["debugger_language"] = language
    st.session_state["debugger_code"] = ""
    st.session_state["debugger_answer"] = ""

examples = {
    "Python": "def add_numbers(a, b):\n    return a + b\n\nresult = add_numbers(5)\nprint(result)",
    "Java": "public class Main {\n    public static void main(String[] args) {\n        int result = addNumbers(5, 3);\n        System.out.println(result);\n    }\n\n    static int addNumbers(int a, int b) {\n        return a + b;\n    }\n}",
    "C++": "#include <iostream>\nusing namespace std;\n\nint main() {\n    int numbers[] = {2, 4, 6};\n    cout << numbers[3] << endl;\n    return 0;\n}",
    "C": "#include <stdio.h>\n\nint main(void) {\n    int numbers[] = {2, 4, 6};\n    printf(\"%d\\n\", numbers[3]);\n    return 0;\n}",
    "JavaScript": "function addNumbers(a, b) {\n    return a + b;\n}\n\nconsole.log(addNumbers(5));",
}

with st.expander("💡 Load an example with a bug"):
    st.write(
        "Use this example to see how the tutor explains a possible "
        "programming mistake."
    )

    if st.button("Load Example Code", use_container_width=True):
        st.session_state["debugger_code"] = examples[language]
        st.session_state["debugger_answer"] = ""
        st.rerun()


with st.form("debugging_tutor_form"):
    code = st.text_area(
        "Paste your code",
        key="debugger_code",
        height=300,
        placeholder="Paste your code here...",
    )

    error_message = st.text_area(
        "Error message (optional)",
        placeholder="Paste the compiler error, traceback, or runtime error.",
        height=100,
    )

    expected_behavior = st.text_area(
        "What should the code do? (optional)",
        placeholder="Describe the intended result.",
        height=80,
    )

    explanation_level = st.selectbox(
        "Explanation Level",
        ["Beginner", "Intermediate", "Advanced"],
    )

    submitted = st.form_submit_button(
        "🔍 Debug My Code",
        use_container_width=True,
    )


# ----------------------------------------------------
# AI DEBUGGING
# ----------------------------------------------------

if submitted:
    if not code.strip():
        st.warning("Please paste some code before requesting debugging help.")

    else:
        try:
            with st.spinner(
                "The AI tutor is analyzing your code..."
            ):
                answer = debug_code(
                    code=code,
                    language=language,
                    error_message=error_message,
                    expected_behavior=expected_behavior,
                    explanation_level=explanation_level,
                )

            st.session_state["debugger_answer"] = answer

        except Exception as error:
            st.error(
                "The tutor could not analyze your code. Check that Ollama "
                "is running and your configured model is installed."
            )
            st.code(str(error), language="text")


# ----------------------------------------------------
# DISPLAY RESULTS
# ----------------------------------------------------

answer = st.session_state.get("debugger_answer", "")

if answer:
    st.divider()
    st.header("2. Your Debugging Report")

    st.markdown(answer)

    st.download_button(
        label="⬇️ Download Debugging Report",
        data=answer,
        file_name="debugging_report.md",
        mime="text/markdown",
        use_container_width=True,
    )

    if st.button("🧹 Clear Debugging Report"):
        st.session_state["debugger_answer"] = ""
        st.rerun()


# ----------------------------------------------------
# FOOTER
# ----------------------------------------------------

st.divider()

st.caption(
    "AI-Powered Personalized Study Assistant · AI Code Debugging Tutor"
)
