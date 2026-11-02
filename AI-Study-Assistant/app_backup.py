
import streamlit as st
from pypdf import PdfReader
import ollama
import re

st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="📚"
)

st.title("📚 AI-Powered Personalized Study Assistant")
st.write("Upload a PDF and ask questions with page-wise citations.")

uploaded_file = st.file_uploader(
    "Upload your PDF",
    type=["pdf"]
)

if uploaded_file is not None:

    reader = PdfReader(uploaded_file)

    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text()

        if text and text.strip():
            pages.append(
                f"[Page {page_number}]\n{text.strip()}"
            )

    if not pages:
        st.warning(
            "No readable text found. "
            "This PDF may contain scanned images."
        )

    else:
        st.success(
            f"PDF processed! Total pages: {len(reader.pages)}"
        )

        pdf_text = "\n\n".join(pages)

        st.write(
            "Characters extracted:",
            len(pdf_text)
        )

        with st.expander("View extracted PDF text"):
            st.text_area(
                "PDF content",
                pdf_text,
                height=250
            )

        question = st.text_input(
            "Ask a question about your PDF"
        )

        if st.button("Get Answer"):

            if not question.strip():
                st.warning("Please enter a question.")

            else:
                with st.spinner("Finding an answer..."):

                    try:
                        # Keep the first 12,000 characters for now.
                        context = pdf_text[:12000]

                        response = ollama.chat(
                            model="qwen2.5:7b",
                            messages=[
                                {
                                    "role": "system",
                                    "content": (
                                        "You are a helpful study assistant. "
                                        "Answer using only the supplied PDF text. "
                                        "The text contains page labels such as "
                                        "[Page 1] and [Page 2]. "
                                        "Cite the relevant page number for "
                                        "each important factual claim, using "
                                        "the exact format [Page 2]. "
                                        "Only cite pages that support your answer. "
                                        "Never invent page numbers or citations. "
                                        "If the answer is not available in the "
                                        "provided text, clearly say so. "
                                        "Explain concepts in simple language."
                                    )
                                },
                                {
                                    "role": "user",
                                    "content": (
                                        f"PDF TEXT:\n{context}\n\n"
                                        f"QUESTION: {question}"
                                    )
                                }
                            ]
                        )

                        answer = response["message"]["content"]

                        st.subheader("💡 AI Answer")
                        st.markdown(answer)

                        # Display page numbers mentioned in the answer.
                        cited_pages = sorted(
                            set(
                                int(number)
                                for number in re.findall(
                                    r"\[Page\s+(\d+)\]",
                                    answer
                                )
                            )
                        )

                        if cited_pages:
                            st.subheader("📖 Cited PDF Pages")

                            for page_number in cited_pages:
                                if 1 <= page_number <= len(reader.pages):
                                    st.write(
                                        f"Page {page_number}"
                                    )

                                    with st.expander(
                                        f"View source: Page {page_number}"
                                    ):
                                        page_text = reader.pages[
                                            page_number - 1
                                        ].extract_text()

                                        st.write(
                                            page_text
                                            if page_text
                                            else "No readable text on this page."
                                        )
                        else:
                            st.info(
                                "No page citations were returned. "
                                "Try asking a more specific question."
                            )

                    except Exception as e:
                        st.error(
                            "Could not get an answer from Ollama. "
                            "Check that Ollama is running and the model "
                            "qwen2.5:7b is installed."
                        )
                        st.caption(str(e))
