
import streamlit as st
from pypdf import PdfReader
import ollama
import re

MODEL = "qwen2.5:7b"

st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="📚",
    layout="wide"
)

st.title("📚 AI-Powered Personalized Study Assistant")
st.write(
    "Upload your study material to ask questions, "
    "generate summaries, and prepare revision notes."
)


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
                    "Use simple language and cite supporting "
                    "pages using [Page 1], [Page 2], etc. "
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

            tab_qa, tab_summary, tab_notes = st.tabs([
                "💬 Ask PDF",
                "📝 PDF Summary",
                "📖 Revision Notes"
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
                                # Existing simple context limit
                                context = pdf_text[:12000]

                                answer = ask_ai(
                                    f"PDF CONTENT:\n{context}\n\n"
                                    f"QUESTION: {question}\n\n"
                                    "Answer clearly and cite the relevant "
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
                    "Create a short summary of the whole PDF, "
                    "processed in smaller page groups."
                )

                if st.button(
                    "Generate Summary",
                    key="summary_button"
                ):
                    summaries = []

                    try:
                        chunks = make_chunks(pages)

                        progress = st.progress(0)

                        for i, chunk in enumerate(chunks):
                            with st.spinner(
                                f"Summarizing section {i + 1} of "
                                f"{len(chunks)}..."
                            ):
                                part_summary = ask_ai(
                                    "Summarize the following section "
                                    "of a student's PDF. Include the main "
                                    "ideas, important facts, and key terms. "
                                    "Use simple language. Keep relevant "
                                    "page citations exactly in the form "
                                    "[Page N]. Do not add information "
                                    "that is not in the text.\n\n"
                                    f"PDF SECTION:\n{chunk}"
                                )

                                summaries.append(part_summary)

                            progress.progress(
                                (i + 1) / len(chunks)
                            )

                        with st.spinner("Combining section summaries..."):
                            final_summary = ask_ai(
                                "Combine these section summaries into one "
                                "clear, well-organized summary of the PDF. "
                                "Remove repetition, keep the important "
                                "points, and preserve relevant page "
                                "citations in the form [Page N]. "
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
                    "Generate definitions, key concepts, important "
                    "points, and a quick revision checklist."
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
                                    "from this PDF section. Organize them "
                                    "under headings and include:\n"
                                    "1. Important definitions\n"
                                    "2. Key concepts and facts\n"
                                    "3. Lists, steps, or formulas if present\n"
                                    "4. Important points to remember\n"
                                    "Use simple language and preserve "
                                    "relevant page citations as [Page N]. "
                                    "Do not invent facts or formulas.\n\n"
                                    f"PDF SECTION:\n{chunk}"
                                )

                                notes_parts.append(part_notes)

                            progress.progress(
                                (i + 1) / len(chunks)
                            )

                        with st.spinner("Organizing your revision notes..."):
                            final_notes = ask_ai(
                                "Combine the following revision notes into "
                                "one organized set of exam revision notes. "
                                "Use headings, bullet points, and a final "
                                "quick-revision checklist. Remove repeated "
                                "points and preserve relevant [Page N] "
                                "citations. Do not add new facts.\n\n"
                                + "\n\n".join(notes_parts)
                            )

                        st.session_state["revision_notes"] = final_notes

                    except Exception as e:
                        st.error(f"Could not generate revision notes: {e}")

                if "revision_notes" in st.session_state:
                    st.markdown("### Your Revision Notes")
                    st.markdown(st.session_state["revision_notes"])

                    st.download_button(
                        "Download Revision Notes",
                        data=st.session_state["revision_notes"],
                        file_name="revision_notes.txt",
                        mime="text/plain"
                    )

    except Exception as e:
        st.error(f"Could not read this PDF: {e}")

else:
    st.info("Upload a PDF to get started.")
