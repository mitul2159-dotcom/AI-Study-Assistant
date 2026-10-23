
import sys
from pathlib import Path

# ----------------------------------------------------
# PROJECT PATH SETUP
# ----------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from modules.ollama_practice import generate_practice
from modules.coding_practice import get_exercise_names, get_exercise
from modules.code_runner import run_code_tests


# ----------------------------------------------------
# PAGE CONFIGURATION
# ----------------------------------------------------

st.set_page_config(
    page_title="Coding Practice Bridge",
    page_icon="💻",
    layout="wide",
)

st.title("💻 Coding Practice Bridge")

st.write(
    "Practice coding with AI-generated exercises, hints, test cases, "
    "and automatic feedback on your solutions."
)

st.divider()


# ----------------------------------------------------
# CONSTANTS
# ----------------------------------------------------

LANGUAGES = ["Python", "Java", "C++", "C", "JavaScript"]

DIFFICULTIES = ["Beginner", "Intermediate", "Advanced"]

PRACTICE_TYPES = [
    "Concept Practice",
    "Problem Solving",
    "Debugging Practice",
    "Interview Practice",
]

LANGUAGE_EXTENSIONS = {
    "Python": "py",
    "Java": "java",
    "C++": "cpp",
    "C": "c",
    "JavaScript": "js",
}

LANGUAGE_HINTS = {
    "Python": "python",
    "Java": "java",
    "C++": "cpp",
    "C": "c",
    "JavaScript": "javascript",
}


# ----------------------------------------------------
# SESSION STATE
# ----------------------------------------------------

DEFAULT_STATE = {
    "cp_exercise": None,
    "cp_student_code": "",
    "cp_language": "Python",
    "cp_test_result": None,
    "cp_exercise_source": None,
    "cp_generation_message": None,
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ----------------------------------------------------
# HELPER FUNCTIONS
# ----------------------------------------------------

def show_hints(exercise):
    """Display hints for the current exercise."""

    hints = exercise.get("hints", [])

    if not hints:
        st.info("No hints are available for this exercise.")
        return

    with st.expander("💡 Show Hints"):
        for index, hint in enumerate(hints, start=1):
            st.markdown(f"**Hint {index}:** {hint}")


def show_test_cases(exercise):
    """Display sample test cases."""

    test_cases = exercise.get("test_cases", [])

    if not test_cases:
        st.info("No test cases are available.")
        return

    with st.expander("🧪 View Test Cases"):
        for index, test_case in enumerate(test_cases, start=1):
            st.markdown(f"**Test Case {index}**")
            st.write("**Input:**")
            st.code(str(test_case.get("input", "")), language="text")
            st.write("**Expected Output:**")
            st.code(
                str(test_case.get("expected_output", "")),
                language="text",
            )

            if test_case.get("explanation"):
                st.caption(test_case["explanation"])

            if index < len(test_cases):
                st.divider()


def show_solution(exercise, language):
    """Display the answer and explanation when available."""

    with st.expander("🔎 View Solution and Explanation"):
        solution = exercise.get("solution", "")

        if solution:
            st.markdown("**Solution**")
            st.code(
                solution,
                language=LANGUAGE_HINTS.get(language, "text"),
            )
        else:
            st.info("A solution was not provided for this exercise.")

        explanation = exercise.get("explanation", "")

        if explanation:
            st.markdown("**Explanation**")
            st.write(explanation)


def normalize_exercise(exercise):
    """
    Ensure that an exercise has the fields required by this page.
    The function does not change the original exercise.
    """

    if not isinstance(exercise, dict):
        raise ValueError(
            "The exercise must be a dictionary containing the problem details."
        )

    normalized = dict(exercise)

    normalized.setdefault("title", "Coding Exercise")
    normalized.setdefault("problem", "Solve the coding problem below.")
    normalized.setdefault("starter_code", "")
    normalized.setdefault("hints", [])
    normalized.setdefault("test_cases", [])
    normalized.setdefault("solution", "")
    normalized.setdefault("explanation", "")

    if not isinstance(normalized["hints"], list):
        normalized["hints"] = []

    if not isinstance(normalized["test_cases"], list):
        normalized["test_cases"] = []

    return normalized


def load_exercise(exercise, source, language):
    """Load an exercise and reset results and the editor."""

    normalized = normalize_exercise(exercise)

    st.session_state["cp_exercise"] = normalized
    st.session_state["cp_exercise_source"] = source
    st.session_state["cp_language"] = language
    st.session_state["cp_student_code"] = normalized.get(
        "starter_code", ""
    )
    st.session_state["cp_test_result"] = None


def show_test_results(result, exercise):
    """Display the result returned by the code runner."""

    if not isinstance(result, dict):
        st.error("The code runner returned an unexpected result.")
        return

    if result.get("error"):
        st.error(result["error"])

        if result.get("details"):
            st.markdown("**Compiler or runtime details:**")
            st.code(str(result["details"]), language="text")

        return

    passed = result.get("passed", 0)
    total = result.get("total", 0)

    st.markdown("### 📊 Test Results")

    metric_col1, metric_col2, metric_col3 = st.columns(3)

    with metric_col1:
        st.metric("Passed", passed)

    with metric_col2:
        st.metric("Total Tests", total)

    with metric_col3:
        st.metric("Failed", max(0, total - passed))

    if result.get("success"):
        st.success("🎉 Excellent! All test cases passed!")
    else:
        st.warning(
            "Some test cases failed. Review the results, fix your code, "
            "and run the tests again."
        )

    results = result.get("results", [])
    test_cases = exercise.get("test_cases", [])

    for test in results:
        passed_test = test.get("passed", False)
        status = "✅ Passed" if passed_test else "❌ Failed"
        test_number = test.get("test", "?")

        with st.expander(f"Test {test_number} — {status}"):
            test_index = (
                test_number - 1
                if isinstance(test_number, int)
                else -1
            )

            if 0 <= test_index < len(test_cases):
                st.write("**Input:**")
                st.code(
                    str(test_cases[test_index].get("input", "")),
                    language="text",
                )

            st.write("**Expected Output:**")
            st.code(str(test.get("expected", "")), language="text")

            st.write("**Your Output:**")
            st.code(str(test.get("actual", "")), language="text")

            if test.get("message"):
                st.write("**Details:**")
                st.write(test["message"])


# ----------------------------------------------------
# SIDEBAR
# ----------------------------------------------------

with st.sidebar:
    st.header("⚙️ Practice Settings")

    selected_language = st.selectbox(
        "Programming Language",
        LANGUAGES,
        index=LANGUAGES.index(st.session_state["cp_language"])
        if st.session_state["cp_language"] in LANGUAGES
        else 0,
        key="cp_language_selector",
    )

    st.caption(
        "The selected language is used when generating exercises "
        "and displaying code."
    )

    st.divider()

    st.markdown("### About this feature")
    st.write(
        "Generate coding exercises locally using Ollama, practise "
        "writing solutions, and check your work against test cases."
    )

    st.warning(
        "The code runner executes programs on your computer. "
        "Only run code you trust."
    )


# ----------------------------------------------------
# LANGUAGE CHANGE HANDLING
# ----------------------------------------------------

if selected_language != st.session_state["cp_language"]:
    st.session_state["cp_language"] = selected_language
    st.session_state["cp_exercise"] = None
    st.session_state["cp_student_code"] = ""
    st.session_state["cp_test_result"] = None
    st.session_state["cp_exercise_source"] = None
    st.rerun()


# ----------------------------------------------------
# EXERCISE GENERATION
# ----------------------------------------------------

st.header("🤖 Generate a Personalized Exercise")

with st.form("cp_generate_exercise_form"):
    topic = st.text_input(
        "Topic",
        placeholder="e.g. loops, arrays, functions, recursion",
        help="Enter the programming concept you want to practise.",
    )

    col1, col2 = st.columns(2)

    with col1:
        difficulty = st.selectbox(
            "Difficulty",
            DIFFICULTIES,
            index=0,
        )

    with col2:
        practice_type = st.selectbox(
            "Practice Type",
            PRACTICE_TYPES,
            index=0,
        )

    generate_clicked = st.form_submit_button(
        "✨ Generate Exercise with AI",
        use_container_width=True,
    )

if generate_clicked:
    if not topic.strip():
        st.warning("Please enter a topic before generating an exercise.")
    else:
        try:
            with st.spinner(
                "Ollama is creating your coding exercise..."
            ):
                generated_exercise = generate_practice(
                    topic=topic.strip(),
                    language=selected_language,
                    difficulty=difficulty,
                    practice_type=practice_type,
                )

            load_exercise(
                generated_exercise,
                source="AI-generated",
                language=selected_language,
            )

            st.success("Your coding exercise has been generated!")

        except Exception as error:
            st.error(
                "Could not generate an exercise. Make sure Ollama is "
                "running and the configured model is installed."
            )
            st.code(str(error), language="text")


# ----------------------------------------------------
# BUILT-IN EXERCISE LIBRARY
# ----------------------------------------------------

st.divider()
st.header("📚 Built-in Exercise Library")

try:
    exercise_names = get_exercise_names()

    if not exercise_names:
        st.info("No built-in exercises are currently available.")
    else:
        with st.form("cp_library_form"):
            library_choice = st.selectbox(
                "Choose an exercise",
                exercise_names,
            )

            library_clicked = st.form_submit_button(
                "Load Built-in Exercise",
                use_container_width=True,
            )

        if library_clicked:
            try:
                library_exercise = get_exercise(library_choice)

                load_exercise(
                    library_exercise,
                    source="Built-in library",
                    language=selected_language,
                )

                st.success(f"Loaded: {library_choice}")

            except Exception as error:
                st.error("Could not load the selected exercise.")
                st.code(str(error), language="text")

except Exception as error:
    st.warning("The built-in exercise library could not be loaded.")
    st.code(str(error), language="text")


# ----------------------------------------------------
# CURRENT EXERCISE
# ----------------------------------------------------

exercise = st.session_state.get("cp_exercise")

if exercise:
    st.divider()

    st.header(f"📝 {exercise.get('title', 'Coding Exercise')}")

    source = st.session_state.get("cp_exercise_source", "Exercise")

    st.caption(
        f"Source: {source} · Language: {st.session_state['cp_language']}"
    )

    st.markdown("### Problem Description")
    st.write(exercise.get("problem", "No problem description available."))

    show_hints(exercise)
    show_test_cases(exercise)

    # ------------------------------------------------
    # CODE EDITOR
    # ------------------------------------------------

    st.markdown("### 👨‍💻 Write Your Solution")

    current_language = st.session_state["cp_language"]

    student_code = st.text_area(
        "Your code",
        key="cp_student_code",
        height=350,
        help="Write your solution here before running the test cases.",
        placeholder="Write your code here...",
    )

    extension = LANGUAGE_EXTENSIONS.get(current_language, "txt")

    st.download_button(
        label="⬇️ Download Your Code",
        data=student_code,
        file_name=f"solution.{extension}",
        mime="text/plain",
        use_container_width=False,
    )

    # -----------------------------------------------
    # RUN CODE / SUBMIT TEST CASES — ALL LANGUAGES
    # -----------------------------------------------

    col1, col2 = st.columns(2)

    with col1:
        run_clicked = st.button(
            "▶ Run Code",
            key="custom_ai_run_code",
            use_container_width=True,
        )

    with col2:
        submit_clicked = st.button(
            "✅ Submit & Check Test Cases",
            key="custom_ai_submit_code",
            use_container_width=True,
        )

    if run_clicked or submit_clicked:
        test_cases = exercise.get("test_cases", [])

        if not student_code.strip():
            st.warning("Please enter your code before running it.")

        elif not test_cases:
            st.warning("No test cases are available for this exercise.")

        else:
            try:
                with st.spinner(
                    f"Running {current_language} test cases..."
                ):
                    result = run_code_tests(
                        language=current_language,
                        student_code=student_code,
                        test_cases=test_cases,
                    )

                st.session_state["cp_test_result"] = result

                show_test_results(result, exercise)

            except Exception as error:
                st.error(f"Could not run the test cases: {error}")

    elif st.session_state.get("cp_test_result"):
        st.markdown("### 📊 Previous Test Results")
        show_test_results(
            st.session_state["cp_test_result"],
            exercise,
        )

    # ------------------------------------------------
    # SOLUTION
    # ------------------------------------------------

    show_solution(exercise, current_language)

else:
    st.info(
        "Generate an exercise above or load one from the built-in library "
        "to get started."
    )


# ----------------------------------------------------
# FOOTER
# ----------------------------------------------------

st.divider()

st.caption(
    "AI-Powered Personalized Study Assistant · Coding Practice Bridge"
)
