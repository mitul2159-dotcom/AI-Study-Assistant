import json
import subprocess
import sys
import tempfile
from pathlib import Path


def run_python_tests(student_code, test_cases, timeout_seconds=3):
    """
    Run a student's solve(input_data) function against test cases.

    Note: a subprocess and timeout are not a secure sandbox for untrusted
    code. Use this only for a local college demo with trusted users/code.
    """

    if not isinstance(student_code, str) or not student_code.strip():
        return {
            "success": False,
            "error": "Please write your Python solution first.",
            "results": [],
        }

    if not test_cases:
        return {
            "success": False,
            "error": "No test cases are available for this exercise.",
            "results": [],
        }

    results = []

    for index, case in enumerate(test_cases, start=1):
        harness = r'''
import json
import runpy
import sys
import traceback

code_path = sys.argv[1]
case_input = json.loads(sys.argv[2])

try:
    namespace = runpy.run_path(code_path)
    solve_function = namespace.get("solve")

    if not callable(solve_function):
        raise ValueError("Your code must define solve(input_data).")

    result = solve_function(case_input)
    print(json.dumps({"ok": True, "result": result}))
except Exception as exc:
    print(json.dumps({
        "ok": False,
        "error": f"{type(exc).__name__}: {exc}"
    }))
'''

        try:
            input_json = json.dumps(case["input"])

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                student_file = temp_path / "student_solution.py"
                harness_file = temp_path / "test_harness.py"

                student_file.write_text(student_code, encoding="utf-8")
                harness_file.write_text(harness, encoding="utf-8")

                completed = subprocess.run(
                    [
                        sys.executable,
                        "-I",
                        str(harness_file),
                        str(student_file),
                        input_json,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                    cwd=temp_dir,
                )

                output_lines = completed.stdout.strip().splitlines()

                if not output_lines:
                    error_message = completed.stderr.strip() or (
                        "Your program did not return a result."
                    )
                    results.append({
                        "test": index,
                        "passed": False,
                        "expected": case["expected_output"],
                        "actual": None,
                        "message": error_message,
                    })
                    continue

                try:
                    payload = json.loads(output_lines[-1])
                except json.JSONDecodeError:
                    results.append({
                        "test": index,
                        "passed": False,
                        "expected": case["expected_output"],
                        "actual": None,
                        "message": "Could not read the result. Return a JSON-compatible value.",
                    })
                    continue

                if not payload.get("ok"):
                    results.append({
                        "test": index,
                        "passed": False,
                        "expected": case["expected_output"],
                        "actual": None,
                        "message": payload.get("error", "Execution failed."),
                    })
                    continue

                actual = payload.get("result")
                expected = case["expected_output"]
                passed = actual == expected

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
                "expected": case.get("expected_output"),
                "actual": None,
                "message": f"Timed out after {timeout_seconds} seconds.",
            })

        except Exception as exc:
            results.append({
                "test": index,
                "passed": False,
                "expected": case.get("expected_output"),
                "actual": None,
                "message": f"Could not run test: {exc}",
            })

    passed_count = sum(result["passed"] for result in results)

    return {
        "success": passed_count == len(results),
        "passed": passed_count,
        "total": len(results),
        "results": results,
    }