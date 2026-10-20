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
    "Upload your study material to ask questions, generate summaries, "
    "create revision notes, and take quizzes."
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
            {"role": "user", "content": prompt}
        ],
        options={"temperature": 0.25, "num_predict": 8192}
    )
    return response["message"]["content"]


# ---------------- PAGE CHUNKS ----------------
def make_chunks(pages, pages_per_chunk=4):
    chunks = []
    for start in range(0, len(pages), pages_per_chunk):
        group = pages[start:start + pages_per_chunk]
        chunk_text = "\n\n".join(
            f"[Page {p['number']}]\n{p['text']}" for p in group
        )
        chunks.append(chunk_text)
    return chunks


# ---------------- QUIZ GENERATOR ----------------
def _generate_quiz_batch(pdf_text, number_of_questions, avoid_questions=None):
    # Ask the model for plain JSON. The fallback below also handles
    # models that return JSON in a slightly different structure.
    avoid_questions = avoid_questions or []
    avoid_text = "\n".join(f"- {q}" for q in avoid_questions[-30:])
    avoid_instruction = (
        "\nDo NOT repeat or rephrase any of these existing questions:\n" + avoid_text
        if avoid_text else ""
    )

    prompt = f"""
Create exactly {number_of_questions} NEW multiple-choice questions using ONLY
the study material below.

Return a JSON object with this structure:
{{
  "questions": [
    {{
      "question": "Question text",
      "options": {{
        "A": "Option A",
        "B": "Option B",
        "C": "Option C",
        "D": "Option D"
      }},
      "correct_answer": "A",
      "explanation": "Explanation based on the study material",
      "page": 1
    }}
  ]
}}

Rules:
- Return JSON only, with no Markdown fences or extra commentary.
- The questions must be based on the study material.
- Each question needs four non-empty options: A, B, C, and D.
- correct_answer must be A, B, C, or D.
- page must be a number if a page number is available; otherwise use 1.
- Cover different facts, definitions, examples, and concepts.
{avoid_instruction}

STUDY MATERIAL:
{pdf_text[:12000]}
"""

    schema = {
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
                        "question", "options", "correct_answer",
                        "explanation", "page"
                    ]
                },
                "minItems": 1
            }
        },
        "required": ["questions"]
    }

    response_text = ""
    try:
        response = ollama.chat(
            model=MODEL,
            format=schema,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You create multiple-choice quizzes from supplied "
                        "study material. Follow the JSON schema exactly. "
                        "Return only a JSON object with a non-empty questions array."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            options={"temperature": 0.25, "num_predict": 8192}
        )
        response_text = response["message"]["content"]
    except Exception as schema_error:
        # Retry without structured-output mode for compatibility with
        # Ollama/model versions that do not support the schema correctly.
        try:
            response = ollama.chat(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Return only valid JSON. Do not use Markdown "
                            "code fences or add commentary."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                options={"temperature": 0.25, "num_predict": 8192}
            )
            response_text = response["message"]["content"]
        except Exception as retry_error:
            raise RuntimeError(
                f"Ollama request failed. Structured-output error: "
                f"{schema_error}; retry error: {retry_error}"
            ) from retry_error

    # Remove Markdown fences if the model adds them.
    response_text = response_text.strip()
    if response_text.startswith("```"):
        response_text = re.sub(r"^```(?:json)?\s*", "", response_text)
        response_text = re.sub(r"\s*```$", "", response_text)

    # Parse JSON, with a fallback for responses containing extra text.
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", response_text, flags=re.DOTALL)
        if not match:
            raise ValueError(
                "Ollama did not return JSON. Try again, or restart Ollama."
            )
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Ollama returned invalid JSON. Details: {e}"
            ) from e

    # Some models may return the list directly or use another common key.
    if isinstance(data, list):
        questions = data
    elif isinstance(data, dict):
        questions = data.get("questions")
        if questions is None:
            questions = data.get("mcqs")
        if questions is None:
            questions = data.get("quiz")
    else:
        questions = None

    if not isinstance(questions, list) or not questions:
        print("OLLAMA QUIZ RESPONSE:", response_text[:5000])
        raise ValueError(
            "Ollama's response did not contain a non-empty 'questions' list. "
            "The raw response was printed in the PowerShell window. "
            "Please copy that response if the problem continues."
        )

    valid_letters = {"A", "B", "C", "D"}
    cleaned_questions = []

    for q in questions:
        if not isinstance(q, dict):
            continue

        question_text = q.get("question") or q.get("text")
        options = q.get("options")
        correct = q.get("correct_answer") or q.get("answer")
        explanation = q.get("explanation") or "Review the relevant PDF section."
        page = q.get("page", 1)

        # Convert a list of four options into A/B/C/D if needed.
        if isinstance(options, list) and len(options) >= 4:
            options = {
                "A": options[0],
                "B": options[1],
                "C": options[2],
                "D": options[3]
            }

        if not isinstance(options, dict):
            continue

        normalized_options = {}
        for letter in ["A", "B", "C", "D"]:
            value = options.get(letter)
            if value is None:
                value = options.get(letter.lower())
            if value is None:
                break
            normalized_options[letter] = str(value).strip()

        if len(normalized_options) != 4:
            continue
        if not question_text or not all(normalized_options.values()):
            continue

        correct = str(correct).strip().upper()
        # Handle answers like "A. Option text" or "Option A".
        if correct not in valid_letters:
            found = re.match(r"^\s*([ABCD])(?:[\.\):\s]|$)", correct)
            if found:
                correct = found.group(1)
            else:
                continue

        try:
            page = int(page)
        except (TypeError, ValueError):
            page = 1

        cleaned_questions.append({
            "question": str(question_text).strip(),
            "options": normalized_options,
            "correct_answer": correct,
            "explanation": str(explanation).strip(),
            "page": page
        })

    if not cleaned_questions:
        print("OLLAMA QUIZ RESPONSE:", response_text[:5000])
        raise ValueError(
            "Ollama returned a response, but no valid MCQs could be read. "
            "The raw response was printed in the PowerShell window."
        )

    return cleaned_questions[:number_of_questions]


# ---------------- QUIZ GENERATOR WRAPPER ----------------
def generate_quiz(pdf_text, number_of_questions):
    """Generate quizzes in small batches so the model is less likely to stop early."""
    import time

    requested = int(number_of_questions)
    all_questions = []
    seen_questions = set()
    max_attempts = 4

    # Qwen often follows a request for five questions more reliably than a
    # request for 10 or 15. Generate batches and retry any short batch.
    while len(all_questions) < requested:
        remaining = requested - len(all_questions)
        batch_size = min(5, remaining)
        batch_added = 0

        for attempt in range(max_attempts):
            attempt_added = 0
            try:
                batch = _generate_quiz_batch(
                    pdf_text, batch_size,
                    avoid_questions=[q["question"] for q in all_questions]
                )
            except Exception:
                if attempt == max_attempts - 1:
                    raise
                time.sleep(1)
                continue

            for q in batch:
                normalized = re.sub(r"\s+", " ", q["question"].strip().lower())
                if normalized in seen_questions:
                    continue
                seen_questions.add(normalized)
                all_questions.append(q)
                batch_added += 1
                attempt_added += 1
                if len(all_questions) >= requested:
                    break

            if len(all_questions) >= requested:
                break
            # If a batch returned fewer new questions than requested, try again.
            if attempt_added >= batch_size:
                break
            time.sleep(1)

        if batch_added == 0:
            break

    if len(all_questions) < requested:
        raise ValueError(
            f"The AI generated only {len(all_questions)} unique valid questions "
            f"out of {requested} requested after several attempts. Try again, "
            "or use a longer/readable PDF."
        )

    return all_questions[:requested]


# ---------------- LEARNING GAP DETECTOR ----------------
def detect_learning_gaps(pdf_text, quiz_questions, quiz_answers):
    wrong_questions = []

    for i, q in enumerate(quiz_questions):
        selected = quiz_answers.get(str(i))
        correct = q["correct_answer"]

        if selected != correct:
            wrong_questions.append({
                "question": q["question"],
                "student_answer": (
                    q["options"][selected]
                    if selected in q["options"]
                    else "Not answered"
                ),
                "correct_answer": q["options"][correct],
                "explanation": q["explanation"]
            })

    if not wrong_questions:
        return (
            "## Great work!\n\n"
            "You answered every question correctly. Try a harder quiz "
            "to check your understanding further."
        )

    mistakes_text = ""
    for i, item in enumerate(wrong_questions, start=1):
        mistakes_text += (
            f"\nMistake {i}:\n"
            f"Question: {item['question']}\n"
            f"Student's answer: {item['student_answer']}\n"
            f"Correct answer: {item['correct_answer']}\n"
            f"Explanation: {item['explanation']}\n"
        )

    prompt = f"""
You are a helpful study coach. Analyse the student's mistakes using only
the PDF and quiz results below.

Include:
1. Weak topics suggested by the mistakes.
2. Possible reasons for confusion, clearly marked as possibilities.
3. PDF concepts the student should revise.
4. A simple step-by-step revision plan.
5. Three specific actions to take next.

Rules:
- Use simple language suitable for a college student.
- One mistake does not prove that a whole topic is unknown.
- Distinguish observed mistakes from possible misunderstandings.
- Use only the supplied PDF and quiz information.
- Do not invent PDF page numbers.
- If evidence is insufficient to identify a weak topic, say so.
- Use headings and bullet points.

PDF CONTENT:
{pdf_text[:18000]}

STUDENT'S INCORRECT OR UNANSWERED QUESTIONS:
{mistakes_text}

Create the personalised learning gap report now.
"""
    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a careful educational tutor. Base your analysis "
                    "on the supplied evidence. Never invent student performance "
                    "data or PDF facts."
                )
            },
            {"role": "user", "content": prompt}
        ],
        options={"temperature": 0.25, "num_predict": 8192}
    )
    return response["message"]["content"]


# ---------------- PDF UPLOAD ----------------
uploaded_file = st.file_uploader("Upload your study PDF", type=["pdf"])

if uploaded_file is None:
    st.info("Upload a PDF to get started.")
else:
    try:
        reader = PdfReader(uploaded_file)
        pages = []

        for page_number, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text()
            if page_text and page_text.strip():
                pages.append({
                    "number": page_number,
                    "text": page_text.strip()
                })

        if not pages:
            st.warning(
                "No readable text was found. This PDF may contain scanned pages."
            )
        else:
            st.success(f"PDF loaded! Total pages: {len(reader.pages)}")

            pdf_text = "\n\n".join(
                f"[Page {p['number']}]\n{p['text']}" for p in pages
            )
            st.write("Characters extracted:", len(pdf_text))

            with st.expander("View extracted PDF text"):
                st.text_area(
                    "Extracted text",
                    pdf_text,
                    height=250
                )

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
                                    "Answer clearly and cite relevant pages using "
                                    "[Page N]. Do not guess citations."
                                )
                                st.subheader("💡 Answer")
                                st.markdown(answer)

                                cited_pages = sorted({
                                    int(n) for n in re.findall(
                                        r"\[Page\s+(\d+)\]", answer
                                    )
                                })

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
                        chunks = make_chunks(pages, pages_per_chunk=4)
                        progress = st.progress(0)

                        for i, chunk in enumerate(chunks):
                            with st.spinner(
                                f"Summarizing section {i + 1} of {len(chunks)}..."
                            ):
                                part_summary = ask_ai(
                                    "Summarize this PDF section. Include main "
                                    "ideas, important facts, and key terms. "
                                    "Use simple language. Preserve relevant "
                                    "[Page N] citations. Do not add information "
                                    "not in the text.\n\n"
                                    f"PDF SECTION:\n{chunk}"
                                )
                            summaries.append(part_summary)
                            progress.progress((i + 1) / len(chunks))

                        final_summary = ask_ai(
                            "Combine these section summaries into one organized "
                            "summary. Remove repetition and preserve relevant "
                            "[Page N] citations. Do not add new facts.\n\n"
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
                    "Generate definitions, important concepts, and a quick "
                    "revision checklist."
                )

                if st.button(
                    "Generate Revision Notes",
                    key="notes_button"
                ):
                    notes_parts = []
                    try:
                        chunks = make_chunks(pages, pages_per_chunk=4)
                        progress = st.progress(0)

                        for i, chunk in enumerate(chunks):
                            with st.spinner(
                                f"Preparing notes for section {i + 1} "
                                f"of {len(chunks)}..."
                            ):
                                part_notes = ask_ai(
                                    "Create exam-friendly revision notes from "
                                    "this section. Include important definitions, "
                                    "key concepts, facts, steps or formulas if "
                                    "present, and points to remember. Use simple "
                                    "language and preserve [Page N] citations. "
                                    "Do not invent facts.\n\n"
                                    f"PDF SECTION:\n{chunk}"
                                )
                            notes_parts.append(part_notes)
                            progress.progress((i + 1) / len(chunks))

                        final_notes = ask_ai(
                            "Combine these notes into organized exam revision "
                            "notes. Use headings, bullet points, and a final "
                            "quick-revision checklist. Remove repeated points "
                            "and preserve [Page N] citations. Do not add new "
                            "facts.\n\n"
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
                        quiz_context = pdf_text[:12000]
                        with st.spinner("Creating questions from your PDF..."):
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
                        st.session_state.pop("learning_gap_report", None)
                        st.success("Your quiz is ready!")
                    except Exception as e:
                        st.error(
                            "Could not create the quiz. Please try again. "
                            "Details: " + str(e)
                        )

                quiz_questions = st.session_state.get("quiz_questions", [])

                if quiz_questions:
                    st.divider()
                    st.write(f"**Total questions:** {len(quiz_questions)}")

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
                                st.markdown(f"### Question {i + 1}")
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

                            submitted = st.form_submit_button("Submit Quiz")

                        if submitted:
                            st.session_state["quiz_answers"] = {
                                str(i): answer
                                for i, answer in selected_answers.items()
                            }
                            st.session_state["quiz_submitted"] = True
                            st.rerun()

                    else:
                        answers = st.session_state.get("quiz_answers", {})
                        score = 0

                        for i, q in enumerate(quiz_questions):
                            if answers.get(str(i)) == q["correct_answer"]:
                                score += 1

                        total = len(quiz_questions)
                        percentage = (score / total) * 100

                        st.subheader("🏆 Your Quiz Results")
                        st.metric("Your Score", f"{score} / {total}")
                        st.progress(percentage / 100)
                        st.write(f"**Percentage:** {percentage:.1f}%")

                        if percentage == 100:
                            st.success(
                                "Excellent! You got every question correct."
                            )
                        elif percentage >= 60:
                            st.success(
                                "Good job! Review the questions you missed."
                            )
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
                                    st.warning(
                                        "You did not answer this question."
                                    )

                                st.write(
                                    f"**Correct answer:** {correct}. "
                                    f"{q['options'][correct]}"
                                )

                            st.write("**Explanation:** " + q["explanation"])
                            page_number = q.get("page")
                            if isinstance(page_number, int) and (
                                1 <= page_number <= len(reader.pages)
                            ):
                                st.caption(
                                    f"Suggested source: PDF page {page_number}"
                                )
                            st.divider()

                        # ---------------- LEARNING GAP DETECTOR UI ----------------
                        st.divider()
                        st.subheader("🎯 Learning Gap Detector")
                        st.write(
                            "Discover which topics need more revision based "
                            "on your quiz mistakes."
                        )

                        if st.button(
                            "Analyse My Weak Topics",
                            key="learning_gap_button"
                        ):
                            with st.spinner(
                                "Analysing your mistakes and preparing "
                                "your personal revision plan..."
                            ):
                                try:
                                    gap_report = detect_learning_gaps(
                                        pdf_text,
                                        quiz_questions,
                                        answers
                                    )
                                    st.session_state[
                                        "learning_gap_report"
                                    ] = gap_report
                                except Exception as e:
                                    st.error(
                                        f"Could not analyse learning gaps: {e}"
                                    )

                        if "learning_gap_report" in st.session_state:
                            st.markdown("### Your Personalised Report")
                            st.markdown(
                                st.session_state["learning_gap_report"]
                            )
                            st.download_button(
                                "Download Learning Gap Report",
                                data=st.session_state["learning_gap_report"],
                                file_name="learning_gap_report.txt",
                                mime="text/plain",
                                key="download_learning_gap"
                            )

                        if st.button(
                            "Try Again / Generate Another Quiz",
                            key="reset_quiz"
                        ):
                            st.session_state["quiz_questions"] = []
                            st.session_state["quiz_answers"] = {}
                            st.session_state["quiz_submitted"] = False
                            st.session_state.pop("learning_gap_report", None)
                            st.rerun()

    except Exception as e:
        st.error(f"Could not read this PDF: {e}")
