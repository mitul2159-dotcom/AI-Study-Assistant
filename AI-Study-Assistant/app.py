
import streamlit as st

st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="📚"
)

st.title("AI Study Assistant")
st.write("Your personalized learning companion")

page = st.sidebar.radio(
    "Choose a feature",
    [
        "Home",
        "Study with PDF",
        "Generate Quiz",
        "Learning Gaps",
        "Study Planner",
        "Progress Dashboard"
    ]
)

if page == "Home":
    st.write("Welcome to your study assistant!")
elif page == "Study with PDF":
    st.write("PDF tools will be added here.")
elif page == "Generate Quiz":
    st.write("Quiz generation will be added here.")
elif page == "Learning Gaps":
    st.write("Learning gap detection will be added here.")
elif page == "Study Planner":
    st.write("Your study plan will appear here.")
elif page == "Progress Dashboard":
    st.write("Your learning progress will appear here.")
