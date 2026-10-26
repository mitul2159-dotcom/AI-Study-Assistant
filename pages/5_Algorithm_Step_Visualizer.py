
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from modules.algorithm_visualizer import generate_algorithm_steps


st.set_page_config(
    page_title="Algorithm Step Visualizer",
    page_icon="🔢",
    layout="wide",
)

st.title("🔢 Algorithm Step Visualizer")

st.write(
    "Explore how algorithms work by watching comparisons, swaps, "
    "and search decisions one step at a time."
)

st.info(
    "Start with Bubble Sort to watch numbers move into order, "
    "or choose a search algorithm to find a target value."
)

st.divider()


# ----------------------------------------------------
# INPUTS
# ----------------------------------------------------

algorithm = st.selectbox(
    "Choose an algorithm",
    [
        "Bubble Sort",
        "Selection Sort",
        "Insertion Sort",
        "Merge Sort",
        "Quick Sort",
        "Heap Sort",
        "Shell Sort",
        "Counting Sort",
        "Radix Sort",
        "Bucket Sort",
        "Linear Search",
        "Binary Search",
    ],
)

default_numbers = (
    "5, 2, 8, 1, 4"
    if algorithm != "Binary Search"
    else "1, 2, 4, 5, 8"
)

with st.form("algorithm_visualizer_form"):
    numbers_text = st.text_input(
        "Enter numbers separated by commas",
        value=default_numbers,
        help="Example: 5, 2, 8, 1, 4",
    )

    target = None

    if algorithm in ["Linear Search", "Binary Search"]:
        target = st.number_input(
            "Number to search for",
            value=5,
            step=1,
        )

    if algorithm == "Binary Search":
        st.caption(
            "Binary Search requires the input to be sorted in ascending order."
        )

    start_visualization = st.form_submit_button(
        "▶ Generate Visualization",
        use_container_width=True,
    )


# ----------------------------------------------------
# GENERATE STEPS
# ----------------------------------------------------

if start_visualization:
    try:
        numbers = [
            int(part.strip())
            for part in numbers_text.split(",")
            if part.strip()
        ]

        if not numbers:
            raise ValueError("Please enter at least one number.")

        steps = generate_algorithm_steps(
            algorithm=algorithm,
            numbers=numbers,
            target=int(target) if target is not None else None,
        )

        st.session_state["algorithm_steps"] = steps
        st.session_state["algorithm_name"] = algorithm
        st.session_state["algorithm_input"] = numbers
        st.session_state["algorithm_target"] = (
            int(target) if target is not None else None
        )
        st.session_state["algorithm_step_index"] = 0

    except ValueError as error:
        st.error(str(error))

    except Exception as error:
        st.error("Could not generate the visualization.")
        st.code(str(error), language="text")


# ----------------------------------------------------
# DISPLAY THE VISUALIZATION
# ----------------------------------------------------

steps = st.session_state.get("algorithm_steps", [])

if steps:
    st.divider()
    st.header(f"📊 {st.session_state['algorithm_name']} Visualization")

    current_index = st.session_state.get("algorithm_step_index", 0)
    current_index = max(0, min(current_index, len(steps) - 1))

    current_step = steps[current_index]

    st.caption(
        f"Step {current_index + 1} of {len(steps)}"
    )

    # Step selector
    selected_step = st.slider(
        "Move through the algorithm",
        min_value=0,
        max_value=len(steps) - 1,
        value=current_index,
        key=f"algorithm_slider_{len(steps)}",
    )

    st.session_state["algorithm_step_index"] = selected_step
    current_index = selected_step
    current_step = steps[current_index]

    # Step controls
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button(
            "⬅ Previous",
            disabled=current_index == 0,
            use_container_width=True,
        ):
            st.session_state["algorithm_step_index"] = current_index - 1
            st.rerun()

    with col2:
        if st.button(
            "🔄 Reset",
            use_container_width=True,
        ):
            st.session_state["algorithm_step_index"] = 0
            st.rerun()

    with col3:
        if st.button(
            "Next ➡",
            disabled=current_index >= len(steps) - 1,
            use_container_width=True,
        ):
            st.session_state["algorithm_step_index"] = current_index + 1
            st.rerun()

    st.subheader("Current Array")

    values = current_step["array"]
    active = current_step.get("active", [])
    sorted_indices = current_step.get("sorted", [])

    # Display each number in a colored card.
    columns = st.columns(len(values))

    for i, value in enumerate(values):
        if i in active:
            color = "#F59E0B"
            text_color = "#111827"
        elif i in sorted_indices:
            color = "#16A34A"
            text_color = "#FFFFFF"
        else:
            color = "#64748B"
            text_color = "#FFFFFF"

        with columns[i]:
            st.markdown(
                f"""
                <div style="
                    background-color: {color};
                    color: {text_color};
                    padding: 18px 4px;
                    border-radius: 10px;
                    text-align: center;
                    font-size: 24px;
                    font-weight: bold;
                ">
                    {value}
                </div>
                <p style="text-align:center; font-size:12px;">
                    Index {i}
                </p>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("### 💡 What is happening?")

    st.info(current_step["message"])

    st.caption(
        "Orange = currently examined elements · "
        "Green = confirmed sorted positions · "
        "Gray = other elements"
    )

    # Summary
    st.divider()
    st.subheader("Algorithm Summary")

    if st.session_state["algorithm_name"] == "Bubble Sort":
        st.write(
            "Bubble Sort repeatedly compares adjacent elements and swaps "
            "them if they are in the wrong order."
        )
        st.write("**Time complexity:** O(n²) average and worst case.")

    elif st.session_state["algorithm_name"] == "Linear Search":
        st.write(
            "Linear Search checks elements from left to right until it "
            "finds the target or reaches the end."
        )
        st.write("**Time complexity:** O(n) worst case.")

    else:
        st.write(
            "Binary Search repeatedly halves the search range. "
            "The array must be sorted first."
        )
        st.write("**Time complexity:** O(log n) worst case.")

    st.download_button(
        "⬇️ Download Step-by-Step Explanation",
        data="\n\n".join(
            f"Step {i + 1}: {step['message']}"
            for i, step in enumerate(steps)
        ),
        file_name="algorithm_steps.txt",
        mime="text/plain",
    )

else:
    st.markdown("### How to use the visualizer")
    st.write("1. Select an algorithm.")
    st.write("2. Enter a list of numbers.")
    st.write("3. Enter a target number for a search algorithm.")
    st.write("4. Click **Generate Visualization**.")
    st.write("5. Use the slider or navigation buttons to inspect each step.")

st.divider()

st.caption(
    "AI-Powered Personalized Study Assistant · Algorithm Step Visualizer"
)
