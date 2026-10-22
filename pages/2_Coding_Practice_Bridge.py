
import streamlit as st

from modules.ollama_practice import generate_practice
from modules.coding_practice import (
    get_exercise_names,
    get_exercise,
    get_hint,
)

st.set_page_config(
    page_title="Coding Practice Bridge",
    page_icon="💻",
    layout="wide",
)

st.title("💻 Coding Practice Bridge")
st.write(
    "Turn programming concepts into practical coding exercises "
    "with personalized AI challenges, hints, test cases, and explanations."
)

st.divider()

# Choose between AI-generated exercises and the original practice library
practice_mode = st.radio(
    "Choose your practice mode",
    ["Custom AI Practice", "Practice Library"],
    horizontal=True,
)

# =========================================================
# MODE 1: CUSTOM AI PRACTICE USING OLLAMA
# =========================================================

if practice_mode == "Custom AI Practice":

    st.subheader("🤖 Generate Your Own Coding Exercise")
    st.write(
        "Enter any programming topic. Your local Ollama model "
        "will generate an exercise based on your preferences."
    )

    with st.form("custom_practice_form"):

        topic = st.text_input(
            "What do you want to practise?",
            placeholder="e.g. Binary Trees, Recursion, SQL Joins, OOP",
        )

        language = st.selectbox(
            "Programming language",
            ["Python", "Java", "C++", "JavaScript", "C"],
        )

        difficulty = st.selectbox(
            "Difficulty",
            ["Beginner", "Intermediate", "Advanced"],
        )

        practice_type = st.selectbox(
            "Practice style",
            [
                "Coding Challenge",
                "Debugging Challenge",
                "Algorithm Practice",
                "Concept Application",
            ],
        )

        generate_clicked = st.form_submit_button(
            "✨ Generate My Exercise",
            type="primary",
        )

    if generate_clicked:
        if not topic.strip():
            st.warning("Please enter a topic first.")
        else:
            try:
                with st.spinner(
                    "Your local AI tutor is generating an exercise..."
                ):
                    new_exercise = generate_practice(
                        topic=topic,
                        language=language,
                        difficulty=difficulty,
                        practice_type=practice_type,
                    )

                st.session_state["custom_ai_exercise"] = new_exercise
                st.session_state["custom_ai_hints_revealed"] = 0
                st.session_state["custom_ai_topic"] = topic

            except Exception as error:
                st.error(
                    "The exercise could not be generated. "
                    "Check that Ollama is running and your model is available."
                )
                with st.expander("Technical details"):
                    st.code(str(error))

    exercise = st.session_state.get("custom_ai_exercise")

    if exercise:
        st.divider()
        st.subheader(f"📝 {exercise.get('title', 'Your Coding Challenge')}")

        st.caption(
            f"Topic: {exercise.get('topic', '')} | "
            f"Language: {exercise.get('language', language if 'language' in locals() else 'Python')} | "
            f"Difficulty: {exercise.get('difficulty', '')}"
        )

        st.markdown("### The Challenge")
        st.write(exercise.get("problem", "No problem statement was generated."))

        st.markdown("### 🧑‍💻 Starter Code")
        st.code(exercise.get("starter_code", ""))

        st.markdown("### ✍️ Write Your Solution")

        student_code = st.text_area(
            "Your code",
            value=exercise.get("starter_code", ""),
            height=250,
            key="custom_ai_student_code",
            help="Write your solution here. You can download it below.",
        )

        st.download_button(
            "⬇️ Download My Code",
            data=student_code,
            file_name="my_solution.txt",
            mime="text/plain",
        )

        st.markdown("### 💡 Progressive Hints")

        hints = exercise.get("hints", [])
        hint_key = "custom_ai_hints_revealed"
        revealed = st.session_state.get(hint_key, 0)

        hint_col1, hint_col2 = st.columns([1, 2])

        with hint_col1:
            if st.button(
                "Reveal Next Hint",
                key="custom_ai_reveal_hint",
                disabled=revealed >= len(hints),
            ):
                st.session_state[hint_key] = revealed + 1
                st.rerun()

        with hint_col2:
            if st.button(
                "Reset Hints",
                key="custom_ai_reset_hints",
            ):
                st.session_state[hint_key] = 0
                st.rerun()

        for index, hint in enumerate(
            hints[:st.session_state.get(hint_key, 0)],
            start=1,
        ):
            with st.expander(f"Hint {index}", expanded=True):
                st.write(hint)

        if hints and st.session_state.get(hint_key, 0) >= len(hints):
            st.caption("You have revealed all available hints.")

        st.markdown("### 🧪 Practice Test Cases")

        test_cases = exercise.get("test_cases", [])

        if test_cases:
            for index, test in enumerate(test_cases, start=1):
                with st.expander(
                    f"Test {index}: {test.get('description', 'Example')}"
                ):
                    st.write("**Input:**")
                    st.code(str(test.get("input", "")))

                    st.write("**Expected output:**")
                    st.code(str(test.get("expected_output", "")))
        else:
            st.info("No test cases were generated for this exercise.")

        st.markdown("### 📖 Solution and Explanation")

        with st.expander("Reveal the reference solution"):
            st.warning(
                "Try solving the challenge yourself before viewing the answer."
            )

            st.code(exercise.get("solution", ""))

            st.write("**How it works:**")
            st.write(exercise.get("explanation", "No explanation provided."))

            mistakes = exercise.get("common_mistakes", [])

            if mistakes:
                st.markdown("**Common mistakes to avoid:**")
                for mistake in mistakes:
                    st.write(f"- {mistake}")

        st.info(
            "This version generates exercises and displays test cases, "
            "but does not execute or automatically grade your submitted code."
        )

# =========================================================
# MODE 2: ORIGINAL FIXED PRACTICE LIBRARY
# =========================================================

else:

    st.subheader("📚 Choose an Exercise from the Practice Library")

    exercise_names = get_exercise_names()

    selected_exercise = st.selectbox(
        "Choose a coding exercise",
        exercise_names,
        key="library_exercise_selector",
    )

    exercise = get_exercise(selected_exercise)

    st.subheader(exercise["title"])

    col1, col2 = st.columns(2)

    with col1:
        st.info(f"📚 Topic: {exercise['topic']}")

    with col2:
        st.info(f"🎯 Difficulty: {exercise['difficulty']}")

    st.write(exercise["description"])

    # Starter code
    st.subheader("🧑‍💻 Starter Code")
    st.caption(
        "Study this starter code and identify what you need to implement."
    )
    st.code(exercise["starter_code"], language="python")

    # Progressive hints
    st.subheader("💡 Progressive Hints")

    hint_key = f"library_hints_{selected_exercise}"

    if hint_key not in st.session_state:
        st.session_state[hint_key] = 0

    hint_count = len(exercise["hints"])
    revealed_count = st.session_state[hint_key]

    hint_col1, hint_col2 = st.columns([1, 2])

    with hint_col1:
        if st.button(
            "Reveal Next Hint",
            key=f"reveal_{selected_exercise}",
            disabled=revealed_count >= hint_count,
        ):
            st.session_state[hint_key] += 1
            st.rerun()

    with hint_col2:
        if st.button("Reset Hints", key=f"reset_{selected_exercise}"):
            st.session_state[hint_key] = 0
            st.rerun()

    for index in range(st.session_state[hint_key]):
        with st.expander(f"Hint {index + 1}", expanded=True):
            st.write(get_hint(selected_exercise, index + 1))

    if st.session_state[hint_key] >= hint_count:
        st.caption("You have revealed all available hints.")

    # Test case preview
    st.subheader("🧪 Practice Test Cases")
    st.write(
        "Use these examples to understand how your function should behave."
    )

    for index, test in enumerate(exercise["tests"], start=1):
        with st.expander(f"Test {index}: {test['name']}"):
            st.write("**Input example:**")
            st.code(str(test["input"]), language="python")

            st.write("**Expected result:**")
            st.code(str(test["expected"]))

            st.write("**What this tests:**")
            st.write(test["explanation"])

    # Solution reveal
    st.subheader("📖 Solution and Explanation")

    with st.expander("Reveal the reference solution"):
        st.warning(
            "Try solving the exercise yourself before revealing the solution."
        )

        st.code(exercise["solution"], language="python")

        st.write("**How it works:**")

        if selected_exercise == "Stack Operations":
            st.write(
                "append() adds an item to the end of a list. "
                "pop() removes and returns the last item. "
                "The empty-stack check prevents an invalid pop."
            )

        elif selected_exercise == "Even or Odd":
            st.write(
                "The % operator calculates the remainder. "
                "If number % 2 equals zero, the number is even."
            )

        elif selected_exercise == "Find the Largest Number":
            st.write(
                "The algorithm starts with the first list item as the "
                "largest, then updates it whenever a bigger number appears."
            )

st.divider()

st.caption(
    "Coding Practice Bridge | Learn concepts by practising code with AI"
)
