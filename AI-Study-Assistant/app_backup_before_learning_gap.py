
import streamlit as st
from pypdf import PdfReader
import ollama
import re
import json

MODEL = "qwen2.5:7b"

st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="📚",
    layout="wide"
)

st.title("📚 AI-Powered Personalized Study Assistant")
st.write(
    "Upload your study material to ask questions, "
    "generate summaries, create revision notes, and take quizzes."
)


# ---------------- AI FUNCTION ----------------
def ask_ai(prompt):
    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful study assistant. "
                    "Use only the supplied PDF content. "
                    "Do not invent facts or page numbers. "
                    "Use simple language and cite supporting pages "
                    "using [Page 1], [Page 2], etc. "
                    "If information is missing, say so."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response["message"]["content"]


# ---------------- PAGE CHUNKS ----------------
def make_chunks(pages, pages_per_chunk=4):
    chunks = []

    for start in range(0, len(pages), pages_per_chunk):
        group = pages[start:start + pages_per_chunk]

        chunk_text = "\n\n".join(
            f"[Page {p['number']}]\n{p['text']}"
            for p in group
        )

        chunks.append(chunk_text)

    return chunks


# ---------------- QUIZ GENERATOR ----------------



def generate_quiz(pdf_text, number_of_questions):
    prompt = f"""
You are creating a multiple-choice quiz for a student.

Use ONLY the study material provided below.

Create exactly {number_of_questions} MCQs.

Your response MUST have this exact structure:
{{
  "questions": [
    {{
      "question": "What does the First Law state?",
      "options": {{
        "A": "Energy can be created",
        "B": "Energy cannot be created or destroyed",
        "C": "Heat always flows from cold to hot",
        "D": "Work and energy are unrelated"
      }},
      "correct_answer": "B",
      "explanation": "The law states that energy is conserved.",
      "page": 1
    }}
  ]
}}

IMPORTANT:
- The example is only a format example. Make questions about the supplied material.
- Return a JSON object with the key "questions".
- The value of "questions" must be an array containing MCQ objects.
- Each MCQ must have question, options, correct_answer, explanation, and page.
- Options must be an object with keys A, B, C, D.
- correct_answer must be A, B, C, or D.
- Do not return QAPage, QuestionAnswer, Schema.org, or a written explanation instead of MCQs.
- Do not wrap the JSON in Markdown.
- Return JSON only.

STUDY MATERIAL:
{pdf_text}

Now return the quiz JSON.
"""

    response = ollama.chat(
        model=MODEL,
        format={
            "type": "object",
            "properties": {
                "questions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string"},
                            "options": {
                                "type": "object",
                                "properties": {
                                    "A": {"type": "string"},
                                    "B": {"type": "string"},
                                    "C": {"type": "string"},
                                    "D": {"type": "string"}
                                },
                                "required": ["A", "B", "C", "D"]
                            },
                            "correct_answer": {
                                "type": "string",
                                "enum": ["A", "B", "C", "D"]
                            },
                            "explanation": {"type": "string"},
                            "page": {"type": "integer"}
                        },
                        "required": [
                            "question",
                            "options",
                            "correct_answer",
                            "explanation",
                            "page"
                        ]
                    }
                }
            },
            "required": ["questions"]
        },
        messages=[
            {
                "role": "system",
                "content": (
                    "You generate MCQ quizzes. Follow the supplied JSON "
                    "schema exactly. Never return a QAPage or article."
                )
            },
            {"role": "user", "content": prompt}
        ],
        options={"temperature": 0}
    )

    response_text = response["message"]["content"]

    # Show the raw response if debugging is needed.
    print("OLLAMA QUIZ RESPONSE:")
    print(response_text)

    data = json.loads(response_text)
    questions = data.get("questions", [])

    if not isinstance(questions, list) or not questions:
        raise ValueError(
            "Ollama did not return MCQs. Its response was not a quiz."
        )

    valid_letters = {"A", "B", "C", "D"}
    cleaned_questions = []

    for q in questions:
        if not isinstance(q, dict):
            continue

        if not all(
            key in q
            for key in (
                "question", "options", "correct_answer", "explanation"
            )
        ):
            continue

        options = q["options"]

        if not isinstance(options, dict):
            continue

        if not all(letter in options for letter in valid_letters):
            continue

        answer = str(q["correct_answer"]).strip().upper()

        if answer not in valid_letters:
            continue

        if not all(str(options[letter]).strip() for letter in valid_letters):
            continue

        cleaned_questions.append({
            "question": str(q["question"]),
            "options": {
                letter: str(options[letter])
                for letter in ["A", "B", "C", "D"]
            },
            "correct_answer": answer,
            "explanation": str(q["explanation"]),
            "page": q.get("page", 1)
        })

    if not cleaned_questions:
        raise ValueError(
            "The model returned JSON, but it contained no valid MCQs. "
            "Check the PowerShell output for OLLAMA QUIZ RESPONSE."
        )

    return cleaned_questions[:number_of_questions]





# ---------------- PDF UPLOAD ----------------
uploaded_file = st.file_uploader(
    "Upload your study PDF",
    type=["pdf"]
)

if uploaded_file is not None:

    try:
        reader = PdfReader(uploaded_file)
        pages = []

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text()

            if text and text.strip():
                pages.append({
                    "number": page_number,
                    "text": text.strip()
                })

        if not pages:
            st.warning(
                "No readable text was found. "
                "This PDF may contain scanned pages."
            )

        else:
            st.success(
                f"PDF loaded! Total pages: {len(reader.pages)}"
            )

            pdf_text = "\n\n".join(
                f"[Page {p['number']}]\n{p['text']}"
                for p in pages
            )

            st.write("Characters extracted:", len(pdf_text))

            with st.expander("View extracted PDF text"):
                st.text_area(
                    "Extracted text",
                    pdf_text,
                    height=250
                )

            # ---------------- TABS ----------------
            tab_qa, tab_summary, tab_notes, tab_quiz = st.tabs([
                "💬 Ask PDF",
                "📝 PDF Summary",
                "📖 Revision Notes",
                "🧠 MCQ Quiz"
            ])

            # ---------------- ASK PDF ----------------
            with tab_qa:
                st.subheader("Ask a question")

                question = st.text_input(
                    "Enter your question about the PDF",
                    key="pdf_question"
                )

                if st.button("Get Answer", key="answer_button"):
                    if not question.strip():
                        st.warning("Please enter a question.")

                    else:
                        with st.spinner("Finding your answer..."):
                            try:
                                context = pdf_text[:12000]

                                answer = ask_ai(
                                    f"PDF CONTENT:\n{context}\n\n"
                                    f"QUESTION: {question}\n\n"
                                    "Answer clearly and cite relevant "
                                    "page numbers. Do not guess citations."
                                )

                                st.subheader("💡 Answer")
                                st.markdown(answer)

                                cited_pages = sorted(set(
                                    int(n) for n in re.findall(
                                        r"\[Page\s+(\d+)\]", answer
                                    )
                                ))

                                if cited_pages:
                                    st.subheader("📚 Cited pages")

                                    for number in cited_pages:
                                        if 1 <= number <= len(reader.pages):
                                            with st.expander(
                                                f"View PDF page {number}"
                                            ):
                                                source = reader.pages[
                                                    number - 1
                                                ].extract_text()

                                                st.write(
                                                    source or
                                                    "No readable text on this page."
                                                )
                                else:
                                    st.info(
                                        "No page citation was returned. "
                                        "Try asking a more specific question."
                                    )

                            except Exception as e:
                                st.error(f"AI error: {e}")

            # ---------------- PDF SUMMARY ----------------
            with tab_summary:
                st.subheader("Generate a PDF Summary")

                st.write(
                    "Create a summary of your PDF in smaller page groups."
                )

                if st.button("Generate Summary", key="summary_button"):
                    summaries = []

                    try:
                        chunks = make_chunks(pages)
                        progress = st.progress(0)

                        for i, chunk in enumerate(chunks):
                            with st.spinner(
                                f"Summarizing section {i + 1} "
                                f"of {len(chunks)}..."
                            ):
                                part_summary = ask_ai(
                                    "Summarize this PDF section. Include "
                                    "main ideas, important facts, and key "
                                    "terms. Use simple language. Preserve "
                                    "relevant [Page N] citations. Do not "
                                    "add information not in the text.\n\n"
                                    f"PDF SECTION:\n{chunk}"
                                )

                                summaries.append(part_summary)
                                progress.progress(
                                    (i + 1) / len(chunks)
                                )

                        final_summary = ask_ai(
                            "Combine these section summaries into one "
                            "organized summary. Remove repetition and "
                            "preserve relevant [Page N] citations. "
                            "Do not add new facts.\n\n"
                            + "\n\n".join(summaries)
                        )

                        st.session_state["pdf_summary"] = final_summary

                    except Exception as e:
                        st.error(f"Could not generate summary: {e}")

                if "pdf_summary" in st.session_state:
                    st.markdown("### Your PDF Summary")
                    st.markdown(st.session_state["pdf_summary"])

                    st.download_button(
                        "Download Summary",
                        data=st.session_state["pdf_summary"],
                        file_name="pdf_summary.txt",
                        mime="text/plain"
                    )

            # ---------------- REVISION NOTES ----------------
            with tab_notes:
                st.subheader("Create Exam Revision Notes")

                st.write(
                    "Generate definitions, important concepts, "
                    "and a quick revision checklist."
                )

                if st.button(
                    "Generate Revision Notes",
                    key="notes_button"
                ):
                    notes_parts = []

                    try:
                        chunks = make_chunks(pages)
                        progress = st.progress(0)

                        for i, chunk in enumerate(chunks):
                            with st.spinner(
                                f"Preparing notes for section "
                                f"{i + 1} of {len(chunks)}..."
                            ):
                                part_notes = ask_ai(
                                    "Create exam-friendly revision notes "
                                    "from this section. Include important "
                                    "definitions, key concepts, facts, "
                                    "steps or formulas if present, and "
                                    "points to remember. Use simple "
                                    "language and preserve [Page N] "
                                    "citations. Do not invent facts.\n\n"
                                    f"PDF SECTION:\n{chunk}"
                                )

                                notes_parts.append(part_notes)
                                progress.progress(
                                    (i + 1) / len(chunks)
                                )

                        final_notes = ask_ai(
                            "Combine these notes into organized exam "
                            "revision notes. Use headings, bullet points, "
                            "and a final quick-revision checklist. "
                            "Remove repeated points and preserve "
                            "[Page N] citations. Do not add new facts.\n\n"
                            + "\n\n".join(notes_parts)
                        )

                        st.session_state["revision_notes"] = final_notes

                    except Exception as e:
                        st.error(f"Could not generate notes: {e}")

                if "revision_notes" in st.session_state:
                    st.markdown("### Your Revision Notes")
                    st.markdown(st.session_state["revision_notes"])

                    st.download_button(
                        "Download Revision Notes",
                        data=st.session_state["revision_notes"],
                        file_name="revision_notes.txt",
                        mime="text/plain"
                    )

            # ---------------- MCQ QUIZ ----------------
            with tab_quiz:
                st.subheader("🧠 Test Your Knowledge")

                st.write(
                    "Generate MCQs from your PDF, select your answers, "
                    "and submit to see your score and explanations."
                )

                number_of_questions = st.selectbox(
                    "Number of questions",
                    [5, 10, 15],
                    index=0,
                    key="quiz_question_count"
                )

                if st.button("Generate New Quiz", key="generate_quiz"):
                    try:
                        # Keep the quiz request manageable for the model.
                        quiz_context = pdf_text[:12000]

                        with st.spinner(
                            "Creating questions from your PDF..."
                        ):
                            new_questions = generate_quiz(
                                quiz_context,
                                number_of_questions
                            )

                        st.session_state["quiz_questions"] = new_questions
                        st.session_state["quiz_answers"] = {}
                        st.session_state["quiz_submitted"] = False
                        st.session_state["quiz_id"] = (
                            st.session_state.get("quiz_id", 0) + 1
                        )

                        st.success("Your quiz is ready!")

                    except Exception as e:
                        st.error(
                            "Could not create the quiz. "
                            "Please try again. Details: " + str(e)
                        )

                quiz_questions = st.session_state.get(
                    "quiz_questions", []
                )

                if quiz_questions:
                    st.divider()

                    st.write(
                        f"**Total questions:** {len(quiz_questions)}"
                    )

                    quiz_submitted = st.session_state.get(
                        "quiz_submitted", False
                    )

                    if not quiz_submitted:
                        with st.form(
                            key=(
                                "quiz_form_"
                                + str(st.session_state.get("quiz_id", 0))
                            )
                        ):
                            selected_answers = {}

                            for i, q in enumerate(quiz_questions):
                                st.markdown(
                                    f"### Question {i + 1}"
                                )
                                st.write(q["question"])

                                options = q["options"]

                                choice = st.radio(
                                    "Choose one answer:",
                                    options=["A", "B", "C", "D"],
                                    format_func=lambda letter, opts=options: (
                                        f"{letter}. {opts[letter]}"
                                    ),
                                    index=None,
                                    key=(
                                        f"quiz_"
                                        f"{st.session_state.get('quiz_id', 0)}"
                                        f"_q_{i}"
                                    )
                                )

                                selected_answers[i] = choice
                                st.divider()

                            submitted = st.form_submit_button(
                                "Submit Quiz"
                            )

                        if submitted:
                            st.session_state["quiz_answers"] = {
                                str(i): answer
                                for i, answer in selected_answers.items()
                            }
                            st.session_state["quiz_submitted"] = True
                            st.rerun()

                    else:
                        answers = st.session_state.get(
                            "quiz_answers", {}
                        )

                        score = 0

                        for i, q in enumerate(quiz_questions):
                            selected = answers.get(str(i))

                            if selected == q["correct_answer"]:
                                score += 1

                        total = len(quiz_questions)
                        percentage = (score / total) * 100

                        st.subheader("🏆 Your Quiz Results")
                        st.metric(
                            "Your Score",
                            f"{score} / {total}"
                        )
                        st.progress(percentage / 100)
                        st.write(f"**Percentage:** {percentage:.1f}%")

                        if percentage == 100:
                            st.success("Excellent! You got every question correct.")
                        elif percentage >= 60:
                            st.success("Good job! Review the questions you missed.")
                        else:
                            st.info(
                                "Keep practising. Review the explanations "
                                "and try another quiz."
                            )

                        st.subheader("Answer Review")

                        for i, q in enumerate(quiz_questions):
                            selected = answers.get(str(i))
                            correct = q["correct_answer"]

                            st.markdown(f"### Question {i + 1}")
                            st.write(q["question"])

                            if selected == correct:
                                st.success(
                                    f"Your answer: {selected}. "
                                    f"{q['options'][selected]}"
                                )
                            else:
                                if selected in q["options"]:
                                    st.error(
                                        f"Your answer: {selected}. "
                                        f"{q['options'][selected]}"
                                    )
                                else:
                                    st.warning("You did not answer this question.")

                                st.write(
                                    f"**Correct answer:** {correct}. "
                                    f"{q['options'][correct]}"
                                )

                            st.write(
                                "**Explanation:** " + q["explanation"]
                            )

                            page_number = q.get("page")

                            if isinstance(page_number, int) and (
                                1 <= page_number <= len(reader.pages)
                            ):
                                st.caption(
                                    f"Suggested source: PDF page {page_number}"
                                )

                            st.divider()

                        if st.button(
                            "Try Again / Generate Another Quiz",
                            key="reset_quiz"
                        ):
                            st.session_state["quiz_questions"] = []
                            st.session_state["quiz_answers"] = {}
                            st.session_state["quiz_submitted"] = False
                            st.rerun()

    except Exception as e:
        st.error(f"Could not read this PDF: {e}")

else:
    st.info("Upload a PDF to get started.")
