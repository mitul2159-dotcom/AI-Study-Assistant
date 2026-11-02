import streamlit as st
from modules.ui_theme import apply_theme

st.set_page_config(
    page_title="LearnSphere AI | Brutalist Study Studio",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()

with st.sidebar:
    st.markdown("## 🎓 LearnSphere AI")
    st.caption("PERSONALIZED LEARNING WORKSPACE")
    st.divider()
    st.markdown("**Your toolkit**")
    st.markdown("📚 Study materials")
    st.markdown("💻 Coding practice")
    st.markdown("🧭 Learning roadmap")
    st.markdown("🧠 Adaptive revision")
    st.divider()
    st.caption("Local-first AI · Built for focused learning")

st.markdown(
    """
    <div class="hero-panel">
      <div class="hero-eyebrow">THE BRUTALIST LEARNING STUDIO</div>
      <h1 style="font-size:2.55rem; margin:.45rem 0 .7rem 0;">LEARN LOUD.  BUILD SKILLS.<br>MAKE PROGRESS.</h1>
      <p class="hero-sub">One bold workspace for notes, lectures, coding practice, revision, and progress. Local AI tools. Clear next steps. Zero visual clutter.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Learning tools", "11+", "Across study + coding")
m2.metric("AI workflow", "Local", "Ollama-powered")
m3.metric("Study formats", "PDF · Audio · Video", "Convert and revise")
m4.metric("Practice languages", "5", "Python, Java, C/C++ & JS")

st.markdown("## PICK YOUR NEXT MOVE")
st.markdown('<p class="small-muted">Six tools. One workspace. Pick a card and get moving.</p>', unsafe_allow_html=True)

left, right = st.columns(2, gap="large")
with left:
    with st.container(border=True):
        st.markdown('<div class="feature-kicker">01 · READ & REVISE</div>', unsafe_allow_html=True)
        st.markdown("### 📚 Study Materials Hub")
        st.write("Ask questions from PDFs with page citations, summarize chapters, create revision notes, generate MCQ quizzes, identify learning gaps, build flashcards with spaced repetition, plan for exams, and convert lecture audio/video into study material.")
        st.page_link("pages/6_Study_Materials_Hub.py", label="Open Study Materials Hub →", icon="📚", use_container_width=True)
    with st.container(border=True):
        st.markdown('<div class="feature-kicker">02 · BUILD FOUNDATIONS</div>', unsafe_allow_html=True)
        st.markdown("### 🧭 Prerequisite Knowledge Mapper")
        st.write("Find what to learn first and build a visual roadmap based on the topics you already know.")
        st.page_link("pages/1_Prerequisite_Knowledge_Mapper.py", label="Build my learning roadmap →", icon="🧭", use_container_width=True)
    with st.container(border=True):
        st.markdown('<div class="feature-kicker">03 · LEARN YOUR WAY</div>', unsafe_allow_html=True)
        st.markdown("### 🌍 Multilingual Learning Assistant")
        st.write("Get beginner-friendly or advanced explanations in your preferred language, with examples when useful.")
        st.page_link("pages/3_Multilingual_Learning_Assistant.py", label="Explain a topic →", icon="🌍", use_container_width=True)
    with st.container(border=True):
        st.markdown('<div class="feature-kicker">04 · DEBUG WITH GUIDANCE</div>', unsafe_allow_html=True)
        st.markdown("### 🐛 AI Code Debugging Tutor")
        st.write("Understand likely bugs, see a corrected version, and learn why the fix works.")
        st.page_link("pages/4_AI_Code_Debugging_Tutor.py", label="Debug my code →", icon="🐛", use_container_width=True)

with right:
    with st.container(border=True):
        st.markdown('<div class="feature-kicker">05 · PRACTICE & IMPROVE</div>', unsafe_allow_html=True)
        st.markdown("### 💻 Coding Practice Bridge")
        st.write("Generate exercises, use hints, run supported test cases, and get feedback on your solution.")
        st.page_link("pages/2_Coding_Practice_Bridge.py", label="Start coding practice →", icon="💻", use_container_width=True)
    with st.container(border=True):
        st.markdown('<div class="feature-kicker">06 · SEE THE LOGIC</div>', unsafe_allow_html=True)
        st.markdown("### 🔢 Algorithm Step Visualizer")
        st.write("Walk through sorting and searching algorithms one comparison, swap, and decision at a time.")
        st.page_link("pages/5_Algorithm_Step_Visualizer.py", label="Visualize an algorithm →", icon="🔢", use_container_width=True)
    with st.container(border=True):
        st.markdown('<div class="feature-kicker">A SIMPLE WORKFLOW</div>', unsafe_allow_html=True)
        st.markdown("### ✨ Your recommended study loop")
        st.markdown("**1. Understand** — ask questions or translate a difficult concept.\n\n**2. Practice** — solve coding tasks or take a PDF quiz.\n\n**3. Diagnose** — inspect mistakes and weak topics.\n\n**4. Remember** — review flashcards and follow your study plan.")
    with st.container(border=True):
        st.markdown('<div class="feature-kicker">SETUP CHECK</div>', unsafe_allow_html=True)
        st.markdown("### ⚙️ Before your demo")
        st.write("Make sure Ollama is running and both required models are installed. Some coding languages also need their compiler/runtime installed.")
        st.code("ollama list\nstreamlit run Home.py", language="powershell")

st.divider()
st.markdown("### BUILT FOR THE WAY YOU LEARN")
c1, c2, c3 = st.columns(3)
c1.markdown("**🔒 Local-first AI**\n\nAI features use Ollama models on your computer; lecture transcription uses local Faster Whisper.")
c2.markdown("**📈 Personalized practice**\n\nQuiz history, learning gaps, flashcard reviews, and study goals help make revision more targeted.")
c3.markdown("**🧩 Modular workspace**\n\nStudy-material and coding tools are grouped in one navigable Streamlit website.")
st.caption("LearnSphere AI · AI-Powered Personalized Study Assistant · College Project")
