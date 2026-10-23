
import ollama

MODEL_NAME = "qwen2.5-coder:3b"

SUPPORTED_LANGUAGES = [
    "Python",
    "Java",
    "C++",
    "C",
    "JavaScript",
]


def debug_code(
    code,
    language="Python",
    error_message="",
    expected_behavior="",
    explanation_level="Beginner",
):
    """
    Analyze code with a local Ollama model and return debugging guidance.
    The function does not execute the submitted code.
    """

    if not code or not code.strip():
        raise ValueError("Please enter some code to debug.")

    if language not in SUPPORTED_LANGUAGES:
        raise ValueError("The selected programming language is not supported.")

    prompt = f"""
You are an experienced programming tutor helping a college student
understand and debug code.

Programming language: {language}
Student level: {explanation_level}

Student's code:
```{language}
{code}
```

Error message, if supplied:
{error_message.strip() or "No error message supplied."}

Expected behavior, if supplied:
{expected_behavior.strip() or "Not specified."}

Provide your answer using these sections:

## 1. Problem Summary
Briefly explain what appears to be wrong.

## 2. Likely Errors
Identify the likely errors and point to relevant lines or expressions.
If there is insufficient information, clearly say so.
Do not invent an error message or claim certainty without evidence.

## 3. Corrected Code
Provide a complete corrected version of the code where possible.
Preserve the student's intended behavior.
If the intended behavior is unclear, explain your assumption.

## 4. Explanation of the Fix
Explain the important changes in simple language appropriate
for the student's level.

## 5. How to Avoid This Error
Give practical tips that help the student avoid similar mistakes.

## 6. Learning Check
Ask one short question that helps the student check their understanding.

Important rules:
- Use valid {language} syntax in the corrected code.
- Do not claim you ran or tested the code.
- If the code is incomplete, state what information is missing.
- Distinguish definite errors from possible bugs.
- Never ask the student to share passwords, API keys, or secrets.
- Be supportive and educational rather than judgmental.
"""

    response = ollama.generate(
        model=MODEL_NAME,
        prompt=prompt,
        options={"temperature": 0.2},
    )

    answer = response.get("response", "").strip()

    if not answer:
        raise RuntimeError(
            "The AI returned an empty response. Please try again."
        )

    return answer
