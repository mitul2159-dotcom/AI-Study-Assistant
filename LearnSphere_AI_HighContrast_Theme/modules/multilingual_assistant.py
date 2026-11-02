
import ollama

MODEL_NAME = "qwen2.5-coder:3b"


def explain_topic(
    topic,
    language="English",
    level="Beginner",
    include_example=True,
):
    """
    Explain a study topic in the requested language and at the
    requested difficulty level using the local Ollama model.
    """

    if not topic or not topic.strip():
        raise ValueError("Please enter a topic to explain.")

    prompt = f"""
You are a friendly, patient college study tutor.

Explain the following topic to a student.

Topic: {topic.strip()}
Output language: {language}
Student level: {level}
Include a practical example: {"Yes" if include_example else "No"}

Instructions:
1. Write the explanation in the requested output language.
2. Match the vocabulary and detail to the student's level.
3. Use clear headings and short paragraphs.
4. Explain technical terms simply.
5. If examples are requested, provide a relevant example.
6. Do not claim facts you are unsure about.
7. Keep the response useful for studying and revision.
8. Preserve standard programming keywords and mathematical
   notation where appropriate.

Return the explanation directly.
"""

    response = ollama.generate(
        model=MODEL_NAME,
        prompt=prompt,
        options={"temperature": 0.3},
    )

    explanation = response.get("response", "").strip()

    if not explanation:
        raise RuntimeError(
            "The AI returned an empty explanation. Please try again."
        )

    return explanation
