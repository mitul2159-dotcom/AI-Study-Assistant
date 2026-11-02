import streamlit as st
from pypdf import PdfReader
import ollama
import re
import json
import sqlite3
import uuid
import os
import tempfile
import subprocess
from pathlib import Path
from datetime import date, datetime, timedelta

MODEL = "qwen2.5:7b"

st.set_page_config(
    page_title="Study Materials Hub | LearnSphere AI",
    page_icon="📚",
    layout="wide"
)

from pathlib import Path as _ThemePath
import sys as _theme_sys
_PROJECT_ROOT = _ThemePath(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in _theme_sys.path:
    _theme_sys.path.insert(0, str(_PROJECT_ROOT))
from modules.ui_theme import apply_theme
apply_theme()

st.title("📚 Study Materials Hub")
st.write(
    "Turn PDFs and lectures into answers, summaries, revision notes, quizzes, flashcards, and personalised study plans."
)


# ---------------- SQLITE DATABASE ----------------
# This database is created automatically beside app.py.
DB_PATH = "study_assistant.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS student_profile (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                study_goal TEXT NOT NULL DEFAULT 'Prepare for exams',
                exam_date TEXT,
                daily_hours REAL NOT NULL DEFAULT 2,
                preferred_level TEXT NOT NULL DEFAULT 'Balanced'
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attempt_key TEXT NOT NULL UNIQUE,
                document_name TEXT NOT NULL,
                score INTEGER NOT NULL,
                total INTEGER NOT NULL,
                percentage REAL NOT NULL,
                weak_pages TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS flashcards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_name TEXT NOT NULL,
                front TEXT NOT NULL,
                back TEXT NOT NULL,
                page INTEGER NOT NULL DEFAULT 1,
                interval_days INTEGER NOT NULL DEFAULT 0,
                repetitions INTEGER NOT NULL DEFAULT 0,
                due_at TEXT NOT NULL,
                last_rating TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(document_name, front)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS flashcard_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id INTEGER NOT NULL,
                rating TEXT NOT NULL,
                reviewed_at TEXT NOT NULL,
                FOREIGN KEY(card_id) REFERENCES flashcards(id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS exam_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attempt_key TEXT NOT NULL UNIQUE,
                document_name TEXT NOT NULL,
                score INTEGER NOT NULL,
                total INTEGER NOT NULL,
                percentage REAL NOT NULL,
                duration_minutes INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute(
            "INSERT OR IGNORE INTO student_profile "
            "(id, study_goal, exam_date, daily_hours, preferred_level) "
            "VALUES (1, 'Prepare for exams', NULL, 2, 'Balanced')"
        )

def get_profile():
    with get_connection() as conn:
        row = conn.execute(
            "SELECT study_goal, exam_date, daily_hours, preferred_level "
            "FROM student_profile WHERE id = 1"
        ).fetchone()
    return {
        "study_goal": row[0],
        "exam_date": row[1],
        "daily_hours": row[2],
        "preferred_level": row[3]
    }

def save_profile(study_goal, exam_date, daily_hours, preferred_level):
    with get_connection() as conn:
        conn.execute(
            "UPDATE student_profile SET study_goal=?, exam_date=?, "
            "daily_hours=?, preferred_level=? WHERE id=1",
            (study_goal, exam_date, daily_hours, preferred_level)
        )

def save_quiz_attempt(attempt_key, document_name, score, total, questions, answers):
    missed_pages = []
    for index, question in enumerate(questions):
        if answers.get(str(index)) != question.get("correct_answer"):
            page = question.get("page", 1)
            if isinstance(page, int):
                missed_pages.append(page)
    # Store unique page numbers as a comma-separated string.
    weak_pages = ",".join(str(p) for p in sorted(set(missed_pages)))
    percentage = (score / total * 100) if total else 0
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO quiz_attempts "
            "(attempt_key, document_name, score, total, percentage, weak_pages, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (attempt_key, document_name, score, total, percentage, weak_pages,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )

def get_quiz_history(limit=20):
    with get_connection() as conn:
        return conn.execute(
            "SELECT document_name, score, total, percentage, weak_pages, created_at "
            "FROM quiz_attempts ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()

def get_history_summary():
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*), AVG(percentage), MAX(percentage) FROM quiz_attempts"
        ).fetchone()
    return row


def create_flashcards(document_name, cards):
    now = datetime.now().isoformat(timespec="seconds")
    added = 0
    with get_connection() as conn:
        for card in cards:
            front = str(card.get("front", "")).strip()
            back = str(card.get("back", "")).strip()
            if not front or not back:
                continue
            cur = conn.execute(
                "INSERT OR IGNORE INTO flashcards "
                "(document_name, front, back, page, interval_days, repetitions, due_at, created_at) "
                "VALUES (?, ?, ?, ?, 0, 0, ?, ?)",
                (document_name, front, back, int(card.get("page", 1)), now, now)
            )
            added += cur.rowcount
    return added


def get_due_flashcards(document_name=None):
    now = datetime.now().isoformat(timespec="seconds")
    query = "SELECT id, document_name, front, back, page, interval_days, repetitions, due_at FROM flashcards WHERE due_at <= ?"
    params = [now]
    if document_name:
        query += " AND document_name = ?"
        params.append(document_name)
    query += " ORDER BY due_at, id"
    with get_connection() as conn:
        return conn.execute(query, params).fetchall()


def get_flashcard_stats():
    now = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM flashcards").fetchone()[0]
        due = conn.execute("SELECT COUNT(*) FROM flashcards WHERE due_at <= ?", (now,)).fetchone()[0]
        reviewed = conn.execute("SELECT COUNT(*) FROM flashcard_reviews").fetchone()[0]
    return total, due, reviewed


def rate_flashcard(card_id, rating, old_interval, old_repetitions):
    # Simple SM-2-inspired schedule: difficult cards return quickly; easy cards spread out.
    if rating == "Again":
        interval, repetitions = 0, 0
        due = datetime.now() + timedelta(minutes=10)
    elif rating == "Hard":
        interval, repetitions = max(1, old_interval or 1), old_repetitions + 1
        due = datetime.now() + timedelta(days=interval)
    elif rating == "Good":
        interval = 1 if old_repetitions == 0 else max(2, old_interval * 2)
        repetitions = old_repetitions + 1
        due = datetime.now() + timedelta(days=interval)
    else:  # Easy
        interval = 3 if old_repetitions == 0 else max(4, round(old_interval * 2.5))
        repetitions = old_repetitions + 1
        due = datetime.now() + timedelta(days=interval)
    with get_connection() as conn:
        conn.execute(
            "UPDATE flashcards SET interval_days=?, repetitions=?, due_at=?, last_rating=? WHERE id=?",
            (interval, repetitions, due.isoformat(timespec="seconds"), rating, card_id)
        )
        conn.execute(
            "INSERT INTO flashcard_reviews (card_id, rating, reviewed_at) VALUES (?, ?, ?)",
            (card_id, rating, datetime.now().isoformat(timespec="seconds"))
        )


def get_adaptive_level():
    with get_connection() as conn:
        rows = conn.execute("SELECT percentage FROM quiz_attempts ORDER BY id DESC LIMIT 3").fetchall()
    if not rows:
        return "Balanced", "No quiz history yet, so the first quiz will use balanced difficulty."
    avg = sum(row[0] for row in rows) / len(rows)
    if avg < 50:
        return "Easy", f"Recent average is {avg:.0f}%; starting with easier questions."
    if avg >= 85:
        return "Hard", f"Recent average is {avg:.0f}%; increasing question difficulty."
    return "Balanced", f"Recent average is {avg:.0f}%; keeping a balanced level."


def save_exam_attempt(attempt_key, document_name, score, total, duration_minutes):
    percentage = score / total * 100 if total else 0
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO exam_attempts "
            "(attempt_key, document_name, score, total, percentage, duration_minutes, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (attempt_key, document_name, score, total, percentage, duration_minutes,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )


initialize_database()

# ---------------- STUDENT PROFILE SIDEBAR ----------------
profile = get_profile()
with st.sidebar:
    st.header("🎯 My Study Profile")
    with st.form("student_profile_form"):
        study_goal = st.selectbox(
            "Main goal",
            ["Prepare for exams", "Understand concepts", "Improve quiz scores", "Revise a subject"],
            index=["Prepare for exams", "Understand concepts", "Improve quiz scores", "Revise a subject"].index(profile["study_goal"])
            if profile["study_goal"] in ["Prepare for exams", "Understand concepts", "Improve quiz scores", "Revise a subject"] else 0
        )
        saved_exam_date = None
        if profile["exam_date"]:
            try:
                saved_exam_date = date.fromisoformat(profile["exam_date"])
            except ValueError:
                saved_exam_date = None
        exam_date = st.date_input("Next exam date (optional)", value=saved_exam_date)
        daily_hours = st.slider("Study hours per day", 0.5, 10.0, float(profile["daily_hours"]), 0.5)
        level_options = ["Beginner", "Balanced", "Advanced"]
        preferred_level = st.selectbox(
            "Preferred explanation level", level_options,
            index=level_options.index(profile["preferred_level"]) if profile["preferred_level"] in level_options else 1
        )
        save_profile_button = st.form_submit_button("Save My Profile")
    if save_profile_button:
        save_profile(study_goal, exam_date.isoformat() if exam_date else None, daily_hours, preferred_level)
        st.success("Study profile saved in SQLite.")
        st.rerun()
    st.caption("Your profile and quiz history are stored locally in study_assistant.db.")


# ---------------- AI FUNCTION ----------------
def ask_ai(prompt, system_message=None):
    if system_message is None:
        system_message = (
            "You are a helpful study assistant. "
            "Use only the supplied PDF content. "
            "Do not invent facts or page numbers. "
            "Use simple language and cite supporting pages "
            "using [Page 1], [Page 2], etc. "
            "If information is missing, say so."
        )
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ],
        options={"temperature": 0.25, "num_predict": 8192}
    )
    return response["message"]["content"]


def read_transcript_file(uploaded_file):
    """Read a text, PDF, or DOCX transcript into plain text."""
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix == ".txt":
        return uploaded_file.getvalue().decode("utf-8", errors="replace").strip()
    if suffix == ".pdf":
        reader = PdfReader(uploaded_file)
        parts = []
        for page_number, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            if page_text.strip():
                parts.append(f"[Transcript page {page_number}]\n{page_text.strip()}")
        return "\n\n".join(parts).strip()
    if suffix == ".docx":
        try:
            from docx import Document
        except ImportError as exc:
            raise RuntimeError("DOCX support is missing. Run: python -m pip install python-docx") from exc
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_path = temp_file.name
        try:
            document = Document(temp_path)
            paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
            for table in document.tables:
                for row in table.rows:
                    paragraphs.append(" | ".join(cell.text.strip() for cell in row.cells))
            return "\n".join(paragraphs).strip()
        finally:
            try:
                os.remove(temp_path)
            except OSError:
                pass
    raise ValueError("Unsupported transcript type. Use TXT, PDF, or DOCX.")


def transcribe_local_media(uploaded_file, language_choice="Auto-detect"):
    """Transcribe audio/video locally with faster-whisper; no paid API is used."""
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "Local speech-to-text is not installed yet. In PowerShell run: "
            "python -m pip install faster-whisper imageio-ffmpeg"
        ) from exc

    suffix = Path(uploaded_file.name).suffix.lower()
    source_path = None
    audio_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as source_file:
            source_file.write(uploaded_file.getvalue())
            source_path = source_file.name

        if suffix in {".mp4", ".mov", ".mkv", ".avi", ".webm", ".mpeg", ".mpg"}:
            try:
                import imageio_ffmpeg
            except ImportError as exc:
                raise RuntimeError(
                    "Video audio extraction is not installed. Run: "
                    "python -m pip install imageio-ffmpeg"
                ) from exc
            audio_path = str(Path(source_path).with_suffix(".wav"))
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            command = [ffmpeg_exe, "-y", "-i", source_path, "-vn", "-ac", "1", "-ar", "16000", audio_path]
            completed = subprocess.run(command, capture_output=True, text=True, timeout=900)
            if completed.returncode != 0 or not os.path.exists(audio_path):
                detail = (completed.stderr or "Audio extraction failed.")[-1200:]
                raise RuntimeError(f"Could not extract audio from this video. {detail}")
            media_path = audio_path
        else:
            media_path = source_path

        # The first run downloads the small model once; transcription thereafter is local.
        model = WhisperModel("base", device="cpu", compute_type="int8")
        language_codes = {
            "English": "en", "Hindi": "hi", "French": "fr", "Spanish": "es",
            "German": "de", "Japanese": "ja", "Chinese": "zh", "Korean": "ko",
            "Tamil": "ta", "Telugu": "te", "Bengali": "bn", "Marathi": "mr",
            "Gujarati": "gu", "Punjabi": "pa", "Urdu": "ur"
        }
        language = None if language_choice == "Auto-detect" else language_codes.get(language_choice)
        segments, info = model.transcribe(media_path, language=language, vad_filter=True)
        transcript_parts = []
        for segment in segments:
            text_piece = segment.text.strip()
            if text_piece:
                start = int(segment.start)
                end = int(segment.end)
                transcript_parts.append(f"[{start // 60:02d}:{start % 60:02d}-{end // 60:02d}:{end % 60:02d}] {text_piece}")
        transcript = "\n".join(transcript_parts).strip()
        if not transcript:
            raise ValueError("No speech was detected. Try a clearer recording or upload a transcript file.")
        return transcript, getattr(info, "language", "unknown")
    finally:
        for path in (source_path, audio_path):
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass


def generate_lecture_material(transcript, source_name, material_style):
    """Summarize transcript chunks and combine them into structured study material."""
    clean_text = transcript.strip()
    if not clean_text:
        raise ValueError("The transcript is empty. Please upload readable content.")
    chunk_size = 10000
    transcript_chunks = [clean_text[i:i + chunk_size] for i in range(0, len(clean_text), chunk_size)]
    section_notes = []
    for index, chunk in enumerate(transcript_chunks, start=1):
        section_notes.append(ask_ai(
            "Turn this lecture transcript section into accurate study notes. "
            "Keep important definitions, examples, formulas, steps, and lecturer warnings. "
            "Do not invent information. If speech is unclear, mark it as unclear rather than guessing. "
            f"Use the requested style: {material_style}.\n\n"
            f"Source file: {source_name}; transcript section {index} of {len(transcript_chunks)}.\n"
            f"LECTURE TRANSCRIPT SECTION:\n{chunk}",
            system_message=(
                "You are a careful study-material assistant. Use only the supplied lecture transcript. "
                "Do not make up facts, quotations, formulas, or speaker intent. Preserve timestamps when useful. "
                "Use simple, well-organized language."
            )
        ))
    if len(section_notes) == 1:
        combined = section_notes[0]
    else:
        combined = ask_ai(
            "Combine these lecture-section notes into one coherent study guide. Remove repeated points, "
            "keep important details from every section, and do not add facts not present in the notes. "
            f"Requested style: {material_style}.\n\nSECTION NOTES:\n" + "\n\n".join(section_notes),
            system_message=(
                "You organize notes derived from a lecture. Do not invent or silently fill gaps. "
                "Use headings and bullets, and mention when a detail in the source was unclear."
            )
        )
    return combined


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
def _generate_quiz_batch(pdf_text, number_of_questions, avoid_questions=None, difficulty="Balanced"):
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
- Overall difficulty must be {difficulty}: Easy means foundational recall and clear wording; Balanced means a mix of recall and understanding; Hard means application and comparison where the source supports it.
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
def generate_quiz(pdf_text, number_of_questions, difficulty="Balanced"):
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
                    avoid_questions=[q["question"] for q in all_questions],
                    difficulty=difficulty
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


# ---------------- PERSONAL PROGRESS DASHBOARD ----------------
st.subheader("📊 Your Learning Progress")
attempt_count, average_score, best_score = get_history_summary()
metric1, metric2, metric3 = st.columns(3)
metric1.metric("Quizzes completed", attempt_count)
metric2.metric("Average score", f"{average_score:.1f}%" if average_score is not None else "—")
metric3.metric("Best score", f"{best_score:.1f}%" if best_score is not None else "—")
flash_total, flash_due, flash_reviews = get_flashcard_stats()
with get_connection() as conn:
    exam_count_saved = conn.execute("SELECT COUNT(*) FROM exam_attempts").fetchone()[0]
progress_cols = st.columns(4)
progress_cols[0].metric("Flashcards created", flash_total)
progress_cols[1].metric("Cards due now", flash_due)
progress_cols[2].metric("Flashcard reviews", flash_reviews)
progress_cols[3].metric("Mock tests completed", exam_count_saved)
recent_history = get_quiz_history(limit=20)
if len(recent_history) >= 2:
    latest_pct = recent_history[0][3]
    previous_pct = recent_history[1][3]
    st.caption(f"Latest quiz vs previous quiz: {latest_pct:.1f}% vs {previous_pct:.1f}% ({latest_pct - previous_pct:+.1f} percentage points).")
with st.expander("View saved quiz history"):
    history_rows = get_quiz_history()
    if history_rows:
        st.dataframe(
            [{"Date": row[5], "PDF": row[0], "Score": f"{row[1]}/{row[2]}",
              "Percentage": f"{row[3]:.1f}%", "Pages to revisit": row[4] or "None recorded"}
             for row in history_rows],
            use_container_width=True, hide_index=True
        )
    else:
        st.info("Your quiz attempts will appear here after you submit your first quiz.")


# ---------------- MULTI-PDF WORKSPACE ----------------
st.subheader("📚 Multi-PDF Study Workspace")
st.write("Upload several PDFs to ask one question across all of them. Answers should identify the source document and page.")
workspace_files = st.file_uploader(
    "Upload PDFs for cross-document questions", type=["pdf"], accept_multiple_files=True,
    key="multi_pdf_workspace"
)
if workspace_files:
    workspace_sources = []
    for workspace_file in workspace_files:
        try:
            workspace_reader = PdfReader(workspace_file)
            for page_no, page_obj in enumerate(workspace_reader.pages, start=1):
                extracted = page_obj.extract_text()
                if extracted and extracted.strip():
                    workspace_sources.append({"document": workspace_file.name, "page": page_no, "text": extracted.strip()})
        except Exception as workspace_error:
            st.warning(f"Could not read {workspace_file.name}: {workspace_error}")
    if workspace_sources:
        workspace_question = st.text_input("Ask across all uploaded PDFs", key="multi_pdf_question")
        if st.button("Search All PDFs", key="multi_pdf_ask_button"):
            if not workspace_question.strip():
                st.warning("Enter a question first.")
            else:
                # Keep context bounded while retaining document names and page labels.
                workspace_context = "\n\n".join(
                    f"[Document: {item['document']}, Page {item['page']}]\n{item['text']}"
                    for item in workspace_sources
                )[:22000]
                with st.spinner("Comparing your PDFs..."):
                    try:
                        multi_answer = ask_ai(
                            "Answer the question using only the source text. Cite every supported point as [Document: filename, Page N]. Do not mix page numbers across documents. If the PDFs do not contain the answer, say so.\n\n"
                            f"SOURCE MATERIAL:\n{workspace_context}\n\nQUESTION: {workspace_question}",
                            system_message=(
                                "You are a careful study assistant. Use only the supplied multi-document source text. "
                                "For every factual claim, cite the exact source as [Document: filename, Page N]. "
                                "Keep page numbers separate for each document and never invent a citation. "
                                "If the answer is not present, say so."
                            )
                        )
                        st.session_state["multi_pdf_answer"] = multi_answer
                    except Exception as multi_error:
                        st.error(f"Could not answer across PDFs: {multi_error}")
        if st.session_state.get("multi_pdf_answer"):
            st.markdown(st.session_state["multi_pdf_answer"])
    else:
        st.warning("No readable text found in these PDFs. Scanned PDFs may need OCR.")

st.divider()

# ---------------- LECTURE-TO-STUDY-MATERIAL CONVERTER ----------------
st.header("🎙️ Lecture-to-Study-Material Converter")
st.write(
    "Convert lecture audio, video, or an existing transcript into structured study material. "
    "Audio/video transcription runs locally with faster-whisper; Ollama creates the notes."
)
lecture_file = st.file_uploader(
    "Upload a lecture recording or transcript",
    type=["mp3", "wav", "m4a", "aac", "flac", "ogg", "mp4", "mov", "mkv", "avi", "webm", "mpeg", "mpg", "txt", "docx", "pdf"],
    key="lecture_converter_upload"
)
lecture_style = st.selectbox(
    "Study material style",
    ["Detailed exam notes", "Short revision notes", "Beginner-friendly explanation", "Definitions and key points", "Exam questions and answers"],
    key="lecture_material_style"
)
lecture_language = st.selectbox(
    "Lecture language for speech-to-text",
    ["Auto-detect", "English", "Hindi", "French", "Spanish", "German", "Japanese", "Chinese", "Korean", "Tamil", "Telugu", "Bengali", "Marathi", "Gujarati", "Punjabi", "Urdu"],
    key="lecture_language_choice"
)
if lecture_file is not None:
    ext = Path(lecture_file.name).suffix.lower()
    if ext in {".txt", ".docx", ".pdf"}:
        st.caption("Transcript file detected. It will be read directly without speech-to-text.")
    else:
        st.caption("Audio/video is processed locally. The first run may download the Whisper model once; no paid transcription API is used.")
    if st.button("Convert Lecture to Study Material", key="convert_lecture_button", type="primary"):
        try:
            with st.spinner("Preparing lecture transcript..."):
                if ext in {".txt", ".docx", ".pdf"}:
                    lecture_transcript = read_transcript_file(lecture_file)
                    detected_language = "from uploaded transcript"
                else:
                    lecture_transcript, detected_language = transcribe_local_media(lecture_file, lecture_language)
            if not lecture_transcript.strip():
                st.error("No readable transcript text was found in this file.")
            else:
                st.session_state["lecture_transcript"] = lecture_transcript
                st.session_state["lecture_source_name"] = lecture_file.name
                st.session_state["lecture_detected_language"] = detected_language
                with st.spinner("Creating study material with local Ollama qwen2.5:7b..."):
                    lecture_material = generate_lecture_material(
                        lecture_transcript, lecture_file.name, lecture_style
                    )
                st.session_state["lecture_material"] = lecture_material
                st.session_state["lecture_material_source"] = lecture_file.name
                st.session_state["lecture_material_style_saved"] = lecture_style
                st.success("Lecture converted successfully.")
        except Exception as lecture_error:
            st.error(f"Could not convert this lecture: {lecture_error}")
            st.info(
                "For audio/video, install the local packages listed in the setup instructions below. "
                "Also confirm Ollama is running and qwen2.5:7b is installed."
            )
if st.session_state.get("lecture_material"):
    st.subheader("📘 Generated Study Material")
    st.caption(
        f"Source: {st.session_state.get('lecture_material_source', 'lecture')} · "
        f"Style: {st.session_state.get('lecture_material_style_saved', 'study notes')} · "
        f"Language: {st.session_state.get('lecture_detected_language', 'unknown')}"
    )
    st.markdown(st.session_state["lecture_material"])
    st.download_button(
        "Download Study Material",
        data=st.session_state["lecture_material"],
        file_name=f"{Path(st.session_state.get('lecture_material_source', 'lecture')).stem}_study_material.md",
        mime="text/markdown",
        key="download_lecture_material"
    )
    with st.expander("View or download the transcript"):
        st.text_area("Lecture transcript", st.session_state.get("lecture_transcript", ""), height=250, key="lecture_transcript_preview")
        st.download_button(
            "Download Transcript",
            data=st.session_state.get("lecture_transcript", ""),
            file_name=f"{Path(st.session_state.get('lecture_source_name', 'lecture')).stem}_transcript.txt",
            mime="text/plain",
            key="download_lecture_transcript"
        )

st.divider()

# ---------------- PDF UPLOAD ----------------
uploaded_file = st.file_uploader("Upload your main study PDF for summaries, flashcards, quizzes and study plans", type=["pdf"])

if uploaded_file is None:
    st.info("Upload a PDF to get started.")
else:
    try:
        st.session_state["quiz_document_name"] = uploaded_file.name
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

            tab_qa, tab_summary, tab_notes, tab_flashcards, tab_quiz, tab_exam, tab_coach = st.tabs([
                "💬 Ask PDF",
                "📝 PDF Summary",
                "📖 Revision Notes",
                "🃏 Flashcards",
                "🧠 MCQ Quiz",
                "⏱️ Exam Mode",
                "🗓️ Study Coach"
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

            # ---------------- FLASHCARDS + SPACED REPETITION ----------------
            with tab_flashcards:
                st.subheader("🃏 AI Flashcards + Spaced Repetition")
                st.write("Generate question-and-answer cards from this PDF. Rate each card honestly so difficult cards return sooner.")
                card_count = st.selectbox("Number of flashcards to generate", [5, 10, 15], key="flashcard_count")
                if st.button("Generate Flashcards", key="generate_flashcards"):
                    flash_prompt = f"""
Create exactly {card_count} useful study flashcards from the supplied PDF text.
Return JSON only as {{"cards":[{{"front":"a clear question or term","back":"a concise answer with a short example if the source supports one","page":1}}]}}.
Use only the PDF. Do not invent examples, facts, or page numbers. The page number must match the [Page N] marker supporting the card. Avoid duplicate cards.
PDF TEXT:
{pdf_text[:16000]}
"""
                    try:
                        def parse_flashcard_json(ai_text):
                            """Parse JSON from Ollama and repair invalid backslashes inside strings."""
                            cleaned = ai_text.strip()
                            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
                            cleaned = re.sub(r"\s*```$", "", cleaned)
                            start_pos = cleaned.find("{")
                            end_pos = cleaned.rfind("}")
                            if start_pos < 0 or end_pos < start_pos:
                                raise ValueError("No JSON object was found in the AI response.")
                            json_text = cleaned[start_pos:end_pos + 1]

                            try:
                                data = json.loads(json_text)
                            except json.JSONDecodeError:
                                # Ollama sometimes writes math such as \( \delta Q \)
                                # with backslashes that are not legal JSON escapes. Repair only
                                # invalid escapes while respecting quoted JSON strings.
                                repaired_chars = []
                                in_string = False
                                i = 0
                                valid_escapes = set('"\\/bfnrtu')
                                while i < len(json_text):
                                    char = json_text[i]
                                    if char == '"':
                                        # A quote is escaped only when preceded by an odd
                                        # number of consecutive backslashes already emitted.
                                        slash_count = 0
                                        j = len(repaired_chars) - 1
                                        while j >= 0 and repaired_chars[j] == "\\":
                                            slash_count += 1
                                            j -= 1
                                        if slash_count % 2 == 0:
                                            in_string = not in_string
                                        repaired_chars.append(char)
                                        i += 1
                                        continue
                                    if char == "\\" and in_string:
                                        if i + 1 >= len(json_text):
                                            repaired_chars.append("\\\\")
                                            i += 1
                                            continue
                                        next_char = json_text[i + 1]
                                        if next_char not in valid_escapes:
                                            repaired_chars.append("\\\\")
                                            i += 1
                                            continue
                                        if next_char == "u":
                                            digits = json_text[i + 2:i + 6]
                                            if len(digits) != 4 or any(c not in "0123456789abcdefABCDEF" for c in digits):
                                                repaired_chars.append("\\\\")
                                                i += 1
                                                continue
                                    repaired_chars.append(char)
                                    i += 1
                                repaired_json = "".join(repaired_chars)
                                try:
                                    data = json.loads(repaired_json)
                                except json.JSONDecodeError as second_error:
                                    excerpt = repaired_json[max(0, second_error.pos - 35):second_error.pos + 35]
                                    raise ValueError(
                                        f"The AI returned malformed JSON near character {second_error.pos}: {excerpt!r}"
                                    ) from second_error

                            # Accept common schema variations from local models.
                            if isinstance(data, list):
                                cards = data
                            elif isinstance(data, dict):
                                cards = None
                                for key in ("cards", "flashcards", "items", "results", "questions", "data"):
                                    candidate = data.get(key)
                                    if isinstance(candidate, list):
                                        cards = candidate
                                        break
                                # Some models wrap the card list one level deeper.
                                if cards is None:
                                    for value in data.values():
                                        if isinstance(value, dict):
                                            for key in ("cards", "flashcards", "items", "results"):
                                                if isinstance(value.get(key), list):
                                                    cards = value[key]
                                                    break
                                        if cards is not None:
                                            break
                            else:
                                cards = None
                            if not isinstance(cards, list):
                                raise ValueError("The AI response did not contain a recognizable list of flashcards.")
                            valid_cards = []
                            seen_fronts = set()
                            for item in cards:
                                if not isinstance(item, dict):
                                    continue
                                front = str(item.get("front", item.get("question", item.get("term", item.get("prompt", ""))))).strip()
                                back = str(item.get("back", item.get("answer", item.get("definition", item.get("response", ""))))).strip()
                                if not front or not back:
                                    continue
                                # Avoid duplicate questions in the same generation.
                                front_key = re.sub(r"\s+", " ", front).casefold()
                                if front_key in seen_fronts:
                                    continue
                                seen_fronts.add(front_key)
                                try:
                                    page = int(item.get("page", 1))
                                except (TypeError, ValueError):
                                    page = 1
                                valid_cards.append({"front": front, "back": back, "page": max(1, page)})
                            if not valid_cards:
                                raise ValueError("The AI response contained no usable question-and-answer cards.")
                            return valid_cards

                        def generate_flashcard_json(prompt):
                            # Ollama's JSON mode greatly reduces malformed JSON responses.
                            response = ollama.chat(
                                model=MODEL,
                                messages=[
                                    {"role": "system", "content": "Return one valid JSON object only, with no Markdown. Use the requested schema."},
                                    {"role": "user", "content": prompt}
                                ],
                                format="json",
                                options={"temperature": 0.1, "num_predict": 8192}
                            )
                            return response["message"]["content"]

                        with st.spinner("Creating flashcards with local AI..."):
                            raw_cards = generate_flashcard_json(flash_prompt)
                            try:
                                parsed_cards = parse_flashcard_json(raw_cards)
                            except (ValueError, json.JSONDecodeError):
                                # One repair attempt helps when the model adds text or malformed JSON.
                                repair_prompt = f"""
Convert the content below into valid JSON only. Do not use Markdown fences or explanations.
Required format: {{"cards":[{{"front":"question","back":"answer","page":1}}]}}
Return exactly {card_count} valid, unique cards. Each card must have non-empty front and back text and an integer page number. If a card contains math, write math using plain text (for example, delta Q = 0), not LaTeX backslashes.
Use only the source content. Keep the page numbers already supported by [Page N] markers.

CONTENT TO REPAIR:
{raw_cards}
"""
                                repaired_text = generate_flashcard_json(repair_prompt)
                                parsed_cards = parse_flashcard_json(repaired_text)

                            # If the model returns fewer than requested, ask only for the missing cards.
                            if len(parsed_cards) < int(card_count):
                                missing_count = int(card_count) - len(parsed_cards)
                                existing_questions = "\n".join(
                                    f"- {item['front']}" for item in parsed_cards
                                )
                                fill_prompt = f"""
Create exactly {missing_count} additional, unique flashcards from the PDF text below.
Return valid JSON only in this format: {{"cards":[{{"front":"question","back":"answer","page":1}}]}}.
Do not repeat or rephrase any of these existing questions:
{existing_questions}
Use plain text for equations; do not use LaTeX backslashes. Use only the PDF text and supported [Page N] markers.
PDF TEXT:
{pdf_text[:16000]}
"""
                                extra_text = generate_flashcard_json(fill_prompt)
                                extra_cards = parse_flashcard_json(extra_text)
                                existing_keys = {re.sub(r"\s+", " ", item["front"]).casefold() for item in parsed_cards}
                                for item in extra_cards:
                                    key = re.sub(r"\s+", " ", item["front"]).casefold()
                                    if key not in existing_keys and len(parsed_cards) < int(card_count):
                                        parsed_cards.append(item)
                                        existing_keys.add(key)

                        # Replace this PDF's existing cards so the selected count is respected.
                        # This resets spaced-repetition history for this PDF only.
                        with get_connection() as conn:
                            old_ids = conn.execute(
                                "SELECT id FROM flashcards WHERE document_name=?", (uploaded_file.name,)
                            ).fetchall()
                            for (old_id,) in old_ids:
                                conn.execute("DELETE FROM flashcard_reviews WHERE card_id=?", (old_id,))
                            conn.execute("DELETE FROM flashcards WHERE document_name=?", (uploaded_file.name,))
                        added_cards = create_flashcards(uploaded_file.name, parsed_cards[:int(card_count)])
                        st.success(f"Generated and saved {added_cards} flashcards for this PDF.")
                    except Exception as flash_error:
                        st.error(f"Could not generate flashcards: {flash_error}")
                        st.caption("Tip: try again. Local models sometimes return incomplete cards; use a text-based PDF and ensure Ollama is running.")
                due_cards = get_due_flashcards(uploaded_file.name)
                st.write(f"**Cards due for review from this PDF:** {len(due_cards)}")
                if due_cards:
                    card = due_cards[0]
                    st.markdown(f"### Card {1} of {len(due_cards)}")
                    st.info(f"**Front:** {card[2]}")
                    # Keep the button's widget key separate from the answer visibility state.
                    reveal_button_key = f"reveal_button_card_{card[0]}"
                    reveal_state_key = f"answer_revealed_card_{card[0]}"
                    if st.button("Reveal Answer", key=reveal_button_key):
                        st.session_state[reveal_state_key] = True
                    if st.session_state.get(reveal_state_key, False):
                        st.success(f"**Back:** {card[3]}")
                        st.caption(f"Source: {uploaded_file.name}, PDF page {card[4]}")
                        st.write("How well did you remember it?")
                        rating_cols = st.columns(4)
                        for col, rating in zip(rating_cols, ["Again", "Hard", "Good", "Easy"]):
                            if col.button(rating, key=f"rate_{card[0]}_{rating}"):
                                rate_flashcard(card[0], rating, card[5], card[6])
                                st.session_state.pop(reveal_state_key, None)
                                st.rerun()
                    st.caption(f"Previous interval: {card[5]} day(s) · Reviews: {card[6]} · Last due: {card[7]}")
                else:
                    st.success("No cards are due from this PDF right now. Generate cards or come back later for review.")
                with st.expander("View all saved flashcards for this PDF"):
                    with get_connection() as conn:
                        all_cards = conn.execute("SELECT front, back, page, due_at, last_rating FROM flashcards WHERE document_name=? ORDER BY id DESC", (uploaded_file.name,)).fetchall()
                    if all_cards:
                        st.dataframe([{"Question": r[0], "Answer": r[1], "Page": r[2], "Due": r[3], "Last rating": r[4] or "Not reviewed"} for r in all_cards], use_container_width=True, hide_index=True)
                    else:
                        st.info("No flashcards saved for this PDF yet.")

            # ---------------- TIMED EXAM MODE ----------------
            with tab_exam:
                st.subheader("⏱️ Exam Mode and Mock Tests")
                st.write("Take a timed mock test. Answers and explanations stay hidden until you submit.")
                exam_count = st.selectbox("Questions in mock test", [5, 10, 15], key="exam_question_count")
                exam_minutes = st.selectbox("Time limit (minutes)", [5, 10, 15, 20, 30], index=1, key="exam_time_limit")
                if st.button("Start New Mock Test", key="start_mock_exam"):
                    try:
                        with st.spinner("Preparing your mock exam..."):
                            exam_questions = generate_quiz(pdf_text[:12000], exam_count, difficulty="Balanced")
                        st.session_state["exam_questions"] = exam_questions
                        st.session_state["exam_started_at"] = datetime.now().isoformat(timespec="seconds")
                        st.session_state["exam_duration_minutes"] = exam_minutes
                        st.session_state["exam_submitted"] = False
                        st.session_state["exam_attempt_key"] = uuid.uuid4().hex
                        st.success("Mock test started. Submit before the time limit ends.")
                    except Exception as exam_error:
                        st.error(f"Could not start mock test: {exam_error}")
                exam_questions = st.session_state.get("exam_questions", [])
                if exam_questions and not st.session_state.get("exam_submitted", False):
                    # Streamlit reruns this fragment every second, so the countdown visibly decreases.
                    @st.fragment(run_every="1s")
                    def render_timed_exam():
                        started = datetime.fromisoformat(st.session_state["exam_started_at"])
                        limit = st.session_state["exam_duration_minutes"]
                        elapsed = (datetime.now() - started).total_seconds()
                        remaining = max(0, int(limit * 60 - elapsed))
                        st.metric("Time remaining", f"{remaining // 60:02d}:{remaining % 60:02d}")
                        if remaining == 0:
                            st.warning("Time has expired. Submit your answers now; the app will mark this attempt as timed out.")
                        with st.form("timed_exam_form"):
                            exam_answers = {}
                            for i, q in enumerate(exam_questions):
                                st.markdown(f"**Question {i+1}.** {q['question']}")
                                exam_answers[str(i)] = st.radio("Select answer", ["A", "B", "C", "D"], format_func=lambda letter, opts=q["options"]: f"{letter}. {opts[letter]}", index=None, key=f"exam_{st.session_state['exam_attempt_key']}_{i}")
                            exam_submit = st.form_submit_button("Submit Mock Test")
                        if exam_submit:
                            st.session_state["exam_answers"] = exam_answers
                            st.session_state["exam_submitted"] = True
                            st.session_state["exam_timed_out"] = remaining == 0
                            st.rerun()
                    render_timed_exam()
                elif exam_questions and st.session_state.get("exam_submitted", False):
                    exam_answers = st.session_state.get("exam_answers", {})
                    exam_score = sum(1 for i, q in enumerate(exam_questions) if exam_answers.get(str(i)) == q["correct_answer"])
                    exam_total = len(exam_questions)
                    elapsed_minutes = max(1, round((datetime.now() - datetime.fromisoformat(st.session_state["exam_started_at"])).total_seconds() / 60))
                    save_exam_attempt(st.session_state["exam_attempt_key"], uploaded_file.name, exam_score, exam_total, elapsed_minutes)
                    st.metric("Mock test score", f"{exam_score}/{exam_total}")
                    st.progress(exam_score / exam_total if exam_total else 0)
                    if st.session_state.get("exam_timed_out"):
                        st.error("This attempt was submitted after the time limit.")
                    st.subheader("Answer Review")
                    for i, q in enumerate(exam_questions):
                        chosen = exam_answers.get(str(i))
                        st.markdown(f"**Q{i+1}. {q['question']}**")
                        st.write(f"Your answer: {chosen or 'Not answered'} · Correct answer: {q['correct_answer']}")
                        st.write(q["explanation"])
                        st.caption(f"Source: {uploaded_file.name}, page {q.get('page', 1)}")
                    if st.button("Clear Mock Test", key="clear_mock_exam"):
                        for key in ["exam_questions", "exam_started_at", "exam_duration_minutes", "exam_submitted", "exam_attempt_key", "exam_answers", "exam_timed_out"]:
                            st.session_state.pop(key, None)
                        st.rerun()

            # ---------------- PERSONALIZED STUDY COACH ----------------
            with tab_coach:
                st.subheader("🗓️ AI Personalized Study Coach")
                current_profile = get_profile()
                st.write(
                    f"Goal: **{current_profile['study_goal']}** · "
                    f"Daily study time: **{current_profile['daily_hours']} hours** · "
                    f"Explanation level: **{current_profile['preferred_level']}**"
                )
                if current_profile["exam_date"]:
                    days_left = (date.fromisoformat(current_profile["exam_date"]) - date.today()).days
                    if days_left >= 0:
                        st.info(f"Your exam is in {days_left} day(s).")
                    else:
                        st.info("The saved exam date has passed. Update it in the sidebar if needed.")

                if st.button("Create My Personalized Study Plan", key="personalized_plan_button"):
                    history = get_quiz_history(limit=10)
                    history_text = "No previous quiz attempts yet."
                    if history:
                        history_text = "\n".join(
                            f"Date: {row[5]}; PDF: {row[0]}; Score: {row[1]}/{row[2]} "
                            f"({row[3]:.1f}%); pages to revisit: {row[4] or 'not recorded'}"
                            for row in history
                        )
                    exam_info = current_profile["exam_date"] or "No exam date supplied"
                    days_until_exam = None
                    if current_profile["exam_date"]:
                        try:
                            days_until_exam = (
                                date.fromisoformat(current_profile["exam_date"]) - date.today()
                            ).days
                        except ValueError:
                            days_until_exam = None

                    if days_until_exam is not None and days_until_exam >= 0:
                        schedule_rule = (
                            f"The exam is in exactly {days_until_exam} day(s). "
                            f"Create exactly {max(1, days_until_exam)} numbered day(s) of preparation, "
                            "ending on the exam date. Do NOT use a 7-day plan unless the exam is actually "
                            "7 days away. Do NOT change the supplied number of days."
                        )
                    elif days_until_exam is not None:
                        schedule_rule = (
                            "The saved exam date is in the past. Tell the student to update the exam date "
                            "and do not pretend the exam is in the future."
                        )
                    else:
                        schedule_rule = "No valid exam date is saved, so create a 7-day plan."

                    plan_prompt = f"""
Create a practical personalised study plan for this student using ONLY the PDF material and the student information below.

IMPORTANT SCHEDULING RULE:
{schedule_rule}

STUDENT PROFILE:
- Goal: {current_profile['study_goal']}
- Exam date: {exam_info}
- Days until exam: {days_until_exam if days_until_exam is not None else 'unknown'}
- Available study time: {current_profile['daily_hours']} hours per day
- Preferred level: {current_profile['preferred_level']}

PAST QUIZ PERFORMANCE (historical evidence, may be empty):
{history_text}

CURRENT PDF CONTENT:
{pdf_text[:16000]}

MANDATORY OUTPUT FORMAT:
- If Days until exam is a number N greater than 0, output exactly N day headings: Day 1, Day 2, ... Day N. Never output Day N+1 and never stop at Day 7 when N is greater than 7.
- If Days until exam is 0, provide a short Exam Day checklist only.
- If no valid exam date is saved, provide a 7-day plan.
- Before answering, verify the final heading is exactly Day {max(1, days_until_exam) if days_until_exam is not None and days_until_exam >= 0 else 7} when an exam date is valid and not today.

Requirements:
1. Follow the IMPORTANT SCHEDULING RULE exactly. If an exam date is saved, the number of plan days must match the computed days until the exam; do not default to 7 days.
2. Fit tasks within the student's daily study time.
3. Prioritise pages mentioned in missed quiz questions, but do not claim a whole topic is weak based on one mistake.
4. Include reading, active recall, quiz practice, and revision.
5. Cite PDF pages as [Page N] only when supported by the supplied PDF.
6. Use clear simple language and realistic tasks. Do not invent topics or page numbers.
"""
                    with st.spinner("Using your profile, PDF, and saved quiz history to make a plan..."):
                        try:
                            plan = ask_ai(plan_prompt)
                            st.session_state["personalized_study_plan"] = plan
                        except Exception as e:
                            st.error(f"Could not create your study plan: {e}")

                if "personalized_study_plan" in st.session_state:
                    st.markdown(st.session_state["personalized_study_plan"])
                    st.download_button(
                        "Download Personalized Study Plan",
                        data=st.session_state["personalized_study_plan"],
                        file_name="personalized_study_plan.txt",
                        mime="text/plain",
                        key="download_personalized_plan"
                    )

            # ---------------- MCQ QUIZ ----------------
            with tab_quiz:
                st.subheader("🧠 Test Your Knowledge")
                st.write(
                    "Generate MCQs from your PDF, select your answers, "
                    "and submit to see your score and explanations."
                )

                adaptive_level, adaptive_reason = get_adaptive_level()
                st.info(f"Adaptive difficulty: **{adaptive_level}**. {adaptive_reason}")
                number_of_questions = st.selectbox(
                    "Number of questions",
                    [5, 10, 15],
                    index=0,
                    key="quiz_question_count"
                )

                if st.button("Generate New Quiz", key="generate_quiz"):
                    try:
                        quiz_context = pdf_text[:12000]
                        with st.spinner(f"Creating {adaptive_level.lower()}-difficulty questions from your PDF..."):
                            new_questions = generate_quiz(
                                quiz_context,
                                number_of_questions,
                                difficulty=adaptive_level
                            )

                        st.session_state["quiz_questions"] = new_questions
                        st.session_state["quiz_answers"] = {}
                        st.session_state["quiz_submitted"] = False
                        st.session_state["quiz_id"] = (
                            st.session_state.get("quiz_id", 0) + 1
                        )
                        st.session_state["quiz_attempt_key"] = uuid.uuid4().hex
                        st.session_state.pop("learning_gap_report", None)
                        st.session_state.pop("personalized_study_plan", None)
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

                        # Save each submitted quiz once; the unique key prevents duplicates on reruns.
                        current_attempt_key = st.session_state.get(
                            "quiz_attempt_key",
                            f"{st.session_state.get('quiz_id', 0)}-{st.session_state.get('quiz_document_name', 'uploaded-pdf')}"
                        )
                        try:
                            save_quiz_attempt(
                                current_attempt_key,
                                st.session_state.get("quiz_document_name", "Uploaded PDF"),
                                score, total, quiz_questions, answers
                            )
                        except sqlite3.Error as db_error:
                            st.warning(f"Quiz result could not be saved to history: {db_error}")

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
