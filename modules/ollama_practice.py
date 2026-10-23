
import json
import re
import ollama


MODEL_NAME = "qwen2.5-coder:3b"


def _extract_json(response_text):
    """Extract a JSON object from the AI response."""
    response_text = response_text.strip()

    # Remove Markdown code fences if the model includes them.
    response_text = re.sub(
        r"^```(?:json)?\s*",
        "",
        response_text,
        flags=re.IGNORECASE,
    )
    response_text = re.sub(r"\s*```$", "", response_text)

    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        # Try to locate a JSON object inside the response.
        match = re.search(r"\{.*\}", response_text, re.DOTALL)

        if match:
            return json.loads(match.group(0))

        raise ValueError(
            "The AI did not return valid JSON. Please generate again."
        )


def _build_prompt(topic, language, difficulty, practice_type):
    """Create language-specific instructions for the AI."""

    language_rules = {
        "Python": """
- Write Python 3 code.
- The starter code and solution must both use Python syntax.
- Define a function named solve(input_data).
- The solve function must return its answer.
- Do not use input() or print() inside solve().
- Use JSON-compatible inputs and return values for automated tests.
""",
        "Java": """
- Write Java code only. NEVER write Python code.
- Use valid Java syntax, types, methods, and class declarations.
- The starter code must be Java code.
- The solution must be a complete Java program with a public class
  named Main and a public static void main(String[] args) method.
- Use System.out.println() to display output.
- Read input using Java-compatible input handling when required.
- Do not use Python syntax such as def, None, or print().
- Test cases must describe standard input and expected standard output.
""",
        "C++": """
- Write C++ code only. NEVER write Python code.
- Use valid C++ syntax and required #include statements.
- The solution must be a complete C++ program with int main().
- Use cout for output and cin when input is required.
- Do not use Python syntax such as def, None, or print().
- Test cases must describe standard input and expected standard output.
""",
        "JavaScript": """
- Write JavaScript code only. NEVER write Python code.
- Use valid modern JavaScript syntax.
- The solution must be runnable with Node.js.
- Use console.log() for output.
- Do not use Python syntax such as def, None, or print().
- Test cases must describe standard input or function input and expected output.
""",
        "C": """
- Write C code only. NEVER write Python code.
- Use valid C syntax and the necessary #include statements.
- The solution must be a complete C program with int main().
- Use printf() for output and scanf() when input is required.
- Do not use Python syntax such as def, None, or print().
- Test cases must describe standard input and expected standard output.
""",
    }

    selected_rules = language_rules.get(language)

    if selected_rules is None:
        raise ValueError(f"Unsupported programming language: {language}")

    return f"""
You are an experienced programming instructor.

Create one coding exercise using the EXACT programming language
selected by the student.

EXERCISE SETTINGS
Topic: {topic}
Programming language: {language}
Difficulty: {difficulty}
Practice type: {practice_type}

MANDATORY LANGUAGE REQUIREMENTS
{selected_rules}

GENERAL REQUIREMENTS
1. The starter_code must be written entirely in {language}.
2. The solution must be written entirely in {language}.
3. Never substitute Python code for another requested language.
4. The problem description must match the actual code and its interface.
5. Provide exactly three useful test cases.
6. Include normal, edge, and additional meaningful test cases.
7. Ensure the solution is logically correct.
8. Explain the solution in beginner-friendly language.
9. Do not put Markdown code fences inside starter_code or solution.
10. Return one valid JSON object, with no extra text.

RETURN THIS JSON STRUCTURE
{{
  "title": "Exercise title",
  "problem": "Detailed problem statement and input/output requirements",
  "starter_code": "Starter code in the selected language",
  "hints": [
    "First hint",
    "Second hint",
    "Third hint"
  ],
  "test_cases": [
    {{
      "input": "Input for test case 1",
      "expected_output": "Expected output for test case 1",
      "explanation": "Why this output is expected"
    }},
    {{
      "input": "Input for test case 2",
      "expected_output": "Expected output for test case 2",
      "explanation": "Why this output is expected"
    }},
    {{
      "input": "Input for test case 3",
      "expected_output": "Expected output for test case 3",
      "explanation": "Why this output is expected"
    }}
  ],
  "solution": "Complete solution in the selected language",
  "explanation": "Step-by-step explanation of the solution"
}}

SPECIAL PYTHON REQUIREMENTS
If the selected language is Python:
- Both starter_code and solution must define solve(input_data).
- The function must return the answer instead of printing it.
- Each test case input must be a JSON-compatible value.
- Each expected_output must be a JSON-compatible value.
- The solution must pass all three test cases.

SPECIAL NON-PYTHON REQUIREMENTS
If the selected language is Java, C++, C, or JavaScript:
- Use that language's correct syntax throughout.
- Ensure the solution's input and output format matches the problem.
- Provide test cases appropriate to the stated input/output format.
- Do not generate Python function definitions or Python solutions.

Return valid JSON. Escape quotation marks and newline characters correctly.
"""


def generate_practice(topic, language, difficulty, practice_type):
    """
    Generate a coding exercise in the language selected by the student.

    Automated test execution in the current project supports Python only.
    Other languages are generated for display and download.
    """

    if not topic or not topic.strip():
        raise ValueError("Please enter a topic.")

    supported_languages = [
        "Python",
        "Java",
        "C++",
        "JavaScript",
        "C",
    ]

    if language not in supported_languages:
        raise ValueError(
            f"Unsupported language: {language}. "
            f"Choose one of: {', '.join(supported_languages)}."
        )

    prompt = _build_prompt(
        topic=topic.strip(),
        language=language,
        difficulty=difficulty,
        practice_type=practice_type,
    )

    try:
        response = ollama.generate(
            model=MODEL_NAME,
            prompt=prompt,
            format="json",
            options={
                "temperature": 0.2,
            },
        )

        response_text = response.get("response", "")
        exercise = _extract_json(response_text)

        required_keys = [
            "title",
            "problem",
            "starter_code",
            "hints",
            "test_cases",
            "solution",
            "explanation",
        ]

        for key in required_keys:
            if key not in exercise:
                raise ValueError(
                    f"The generated exercise is missing '{key}'. "
                    "Please generate again."
                )

        if not isinstance(exercise["starter_code"], str):
            raise ValueError("The generated starter code is invalid.")

        if not isinstance(exercise["solution"], str):
            raise ValueError("The generated solution is invalid.")

        if not exercise["starter_code"].strip():
            raise ValueError("The AI generated empty starter code.")

        if not exercise["solution"].strip():
            raise ValueError("The AI generated an empty solution.")

        if not isinstance(exercise["hints"], list):
            exercise["hints"] = []

        if not isinstance(exercise["test_cases"], list):
            raise ValueError("The generated test cases are invalid.")

        # Keep at most three test cases.
        exercise["test_cases"] = exercise["test_cases"][:3]

        if not exercise["test_cases"]:
            raise ValueError("The AI did not generate any test cases.")

        # Validate Python exercises against the existing Python runner.
        if language == "Python":
            if "def solve(" not in exercise["starter_code"]:
                raise ValueError(
                    "The AI did not generate the required Python "
                    "solve(input_data) function. Please generate again."
                )

            if "def solve(" not in exercise["solution"]:
                raise ValueError(
                    "The AI solution does not define solve(input_data). "
                    "Please generate again."
                )

            for index, case in enumerate(
                exercise["test_cases"],
                start=1,
            ):
                if not isinstance(case, dict):
                    raise ValueError(
                        f"Test case {index} must be a JSON object."
                    )

                if "input" not in case or "expected_output" not in case:
                    raise ValueError(
                        f"Test case {index} is missing input or expected_output."
                    )

                # Python runner expects JSON-compatible values.
                try:
                    json.dumps(case["input"])
                    json.dumps(case["expected_output"])
                except (TypeError, ValueError) as error:
                    raise ValueError(
                        f"Test case {index} contains invalid JSON values."
                    ) from error

        return exercise

    except Exception as error:
        raise RuntimeError(
            f"Could not generate a valid {language} exercise: {error}"
        ) from error
