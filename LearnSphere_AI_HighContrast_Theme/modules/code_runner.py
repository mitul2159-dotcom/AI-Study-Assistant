
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _normalise_output(value):
    """Normalize output for comparison while ignoring trailing whitespace."""
    return str(value).strip()


def run_code_tests(language, student_code, test_cases, timeout_seconds=5):
    """
    Run test cases for Python, Java, C++, C, or JavaScript.

    Python uses solve(input_data) with JSON test values.
    Other languages use standard input and standard output.

    WARNING: This is not a secure sandbox for untrusted code.
    """

    supported = {"Python", "Java", "C++", "C", "JavaScript"}

    if language not in supported:
        return {"error": f"Unsupported language: {language}"}

    if not student_code or not student_code.strip():
        return {"error": "Please write your code first."}

    if not test_cases:
        return {"error": "No test cases are available."}

    results = []

    with tempfile.TemporaryDirectory(prefix="coding_practice_") as temp:
        folder = Path(temp)

        # Check that the required compiler/runtime is installed.
        commands = {
            "Python": ["python"],
            "Java": ["javac", "java"],
            "C++": ["g++"],
            "C": ["gcc"],
            "JavaScript": ["node"],
        }

        missing = [
            command
            for command in commands[language]
            if shutil.which(command) is None
        ]

        if missing:
            return {
                "error": (
                    "Required tool(s) not found: "
                    + ", ".join(missing)
                    + ". Install them and add them to your Windows PATH."
                )
            }

        # Write the student's source code.
        source_names = {
            "Python": "student.py",
            "Java": "Main.java",
            "C++": "student.cpp",
            "C": "student.c",
            "JavaScript": "student.js",
        }

        source_file = folder / source_names[language]
        source_file.write_text(student_code, encoding="utf-8")

        # Python uses a function-based JSON input contract.
        if language == "Python":
            harness_file = folder / "test_harness.py"
            harness_file.write_text(
                """
import json
import runpy
import sys

source_file = sys.argv[1]
input_value = json.loads(sys.stdin.read())

namespace = runpy.run_path(source_file)
solve = namespace.get("solve")

if not callable(solve):
    raise ValueError("Your code must define solve(input_data).")

result = solve(input_value)
print(json.dumps(result))
""".strip(),
                encoding="utf-8",
            )

        # Compile Java, C++, or C once before running test cases.
        compile_command = None
        executable = None

        if language == "Java":
            compile_command = ["javac", str(source_file)]
            executable = ["java", "-cp", str(folder), "Main"]

        elif language == "C++":
            executable = [str(folder / "student.exe")]
            compile_command = [
                "g++",
                str(source_file),
                "-o",
                str(folder / "student.exe"),
            ]

        elif language == "C":
            executable = [str(folder / "student.exe")]
            compile_command = [
                "gcc",
                str(source_file),
                "-o",
                str(folder / "student.exe"),
            ]

        elif language == "JavaScript":
            executable = ["node", str(source_file)]

        if compile_command:
            try:
                compiled = subprocess.run(
                    compile_command,
                    capture_output=True,
                    text=True,
                    timeout=20,
                    cwd=folder,
                    shell=False,
                )

                if compiled.returncode != 0:
                    return {
                        "error": "Compilation failed.",
                        "details": (
                            compiled.stderr.strip()
                            or compiled.stdout.strip()
                        ),
                    }

            except subprocess.TimeoutExpired:
                return {"error": "Compilation timed out."}

            except Exception as exc:
                return {"error": f"Could not compile code: {exc}"}

        # Run each test case.
        for index, case in enumerate(test_cases, start=1):
            if not isinstance(case, dict):
                results.append({
                    "test": index,
                    "passed": False,
                    "expected": "",
                    "actual": "",
                    "message": "Invalid test case format.",
                })
                continue

            if "input" not in case or "expected_output" not in case:
                results.append({
                    "test": index,
                    "passed": False,
                    "expected": case.get("expected_output", ""),
                    "actual": "",
                    "message": "Test case needs input and expected_output.",
                })
                continue

            test_input = case["input"]
            expected = case["expected_output"]

            try:
                if language == "Python":
                    stdin_text = json.dumps(test_input)
                    command = [
                        sys.executable,
                        str(harness_file),
                        str(source_file),
                    ]
                else:
                    # Non-Python languages use stdin/stdout text.
                    stdin_text = (
                        test_input
                        if isinstance(test_input, str)
                        else json.dumps(test_input)
                    )
                    command = executable

                completed = subprocess.run(
                    command,
                    input=stdin_text,
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                    cwd=folder,
                    shell=False,
                )

                actual = completed.stdout.strip()

                if completed.returncode != 0:
                    results.append({
                        "test": index,
                        "passed": False,
                        "expected": expected,
                        "actual": actual,
                        "message": (
                            completed.stderr.strip()
                            or "Program exited with an error."
                        ),
                    })
                    continue

                if language == "Python":
                    try:
                        actual_value = json.loads(actual)
                        passed = actual_value == expected
                    except json.JSONDecodeError:
                        actual_value = actual
                        passed = (
                            _normalise_output(actual_value)
                            == _normalise_output(expected)
                        )
                else:
                    passed = (
                        _normalise_output(actual)
                        == _normalise_output(expected)
                    )

                results.append({
                    "test": index,
                    "passed": passed,
                    "expected": expected,
                    "actual": actual,
                    "message": "Passed" if passed else "Output did not match.",
                })

            except subprocess.TimeoutExpired:
                results.append({
                    "test": index,
                    "passed": False,
                    "expected": expected,
                    "actual": "",
                    "message": f"Timed out after {timeout_seconds} seconds.",
                })

            except Exception as exc:
                results.append({
                    "test": index,
                    "passed": False,
                    "expected": expected,
                    "actual": "",
                    "message": str(exc),
                })

    passed_count = sum(item["passed"] for item in results)

    return {
        "success": passed_count == len(results),
        "passed": passed_count,
        "total": len(results),
        "results": results,
    }
