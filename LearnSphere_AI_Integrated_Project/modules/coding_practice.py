
EXERCISES = {
    "Stack Operations": {
        "topic": "Stacks",
        "difficulty": "Beginner",
        "title": "Implement Stack Push and Pop",
        "description": (
            "A stack follows LIFO: Last In, First Out. "
            "Implement push(stack, item) to add an item "
            "and pop_item(stack) to remove and return the "
            "last item. If the stack is empty, return None."
        ),
        "starter_code": (
            "def push(stack, item):\n"
            "    # Add item to the stack\n"
            "    pass\n\n"
            "def pop_item(stack):\n"
            "    # Remove and return the last item\n"
            "    pass\n"
        ),
        "hints": [
            "A Python list can be used as a stack.",
            "Use append() to add an item. Use pop() to remove the last item.",
            "Before removing an item, check whether the stack is empty.",
        ],
        "solution": (
            "def push(stack, item):\n"
            "    stack.append(item)\n\n"
            "def pop_item(stack):\n"
            "    if not stack:\n"
            "        return None\n"
            "    return stack.pop()\n"
        ),
        "tests": [
            {
                "name": "Push an item",
                "input": "stack = []; push(stack, 10)",
                "expected": "[10]",
                "explanation": "Use append() to add an item to the list.",
            },
            {
                "name": "Pop the last item",
                "input": "stack = [10, 20]; pop_item(stack)",
                "expected": "20",
                "explanation": "A stack removes the most recently added item.",
            },
            {
                "name": "Pop an empty stack",
                "input": "stack = []; pop_item(stack)",
                "expected": "None",
                "explanation": "Check whether the stack is empty before popping.",
            },
        ],
    },
    "Even or Odd": {
        "topic": "Conditions",
        "difficulty": "Beginner",
        "title": "Check Even or Odd",
        "description": (
            "Implement is_even(number). Return True if the "
            "number is even and False otherwise."
        ),
        "starter_code": (
            "def is_even(number):\n"
            "    # Return True if even, otherwise False\n"
            "    pass\n"
        ),
        "hints": [
            "The remainder operator in Python is %.",
            "An even number has a remainder of zero when divided by 2.",
            "Try: number % 2 == 0",
        ],
        "solution": (
            "def is_even(number):\n"
            "    return number % 2 == 0\n"
        ),
        "tests": [
            {
                "name": "Even number",
                "input": "is_even(4)",
                "expected": "True",
                "explanation": "4 divided by 2 leaves a remainder of zero.",
            },
            {
                "name": "Odd number",
                "input": "is_even(7)",
                "expected": "False",
                "explanation": "7 divided by 2 leaves a remainder of one.",
            },
            {
                "name": "Zero",
                "input": "is_even(0)",
                "expected": "True",
                "explanation": "Zero is divisible by 2 without a remainder.",
            },
        ],
    },
    "Find the Largest Number": {
        "topic": "Lists and Loops",
        "difficulty": "Beginner",
        "title": "Find the Largest Number",
        "description": (
            "Implement find_largest(numbers) to return the "
            "largest number in a non-empty list."
        ),
        "starter_code": (
            "def find_largest(numbers):\n"
            "    # Return the largest number\n"
            "    pass\n"
        ),
        "hints": [
            "Start by assuming the first number is the largest.",
            "Loop through the numbers and compare each with the current largest.",
            "Update your largest variable whenever you find a bigger number.",
        ],
        "solution": (
            "def find_largest(numbers):\n"
            "    largest = numbers[0]\n"
            "    for number in numbers:\n"
            "        if number > largest:\n"
            "            largest = number\n"
            "    return largest\n"
        ),
        "tests": [
            {
                "name": "Positive numbers",
                "input": "find_largest([3, 8, 2, 5])",
                "expected": "8",
                "explanation": "Compare each number with the current largest.",
            },
            {
                "name": "Negative numbers",
                "input": "find_largest([-8, -2, -5])",
                "expected": "-2",
                "explanation": "Initialize with the first item, not zero.",
            },
            {
                "name": "Single item",
                "input": "find_largest([6])",
                "expected": "6",
                "explanation": "A list with one item has that item as its maximum.",
            },
        ],
    },
}


def get_exercise_names():
    """Return all available exercise names."""
    return list(EXERCISES.keys())


def get_exercise(exercise_name):
    """Return one exercise, or None if it does not exist."""
    return EXERCISES.get(exercise_name)


def get_hint(exercise_name, hint_number):
    """Return a progressive hint using a one-based hint number."""
    exercise = get_exercise(exercise_name)

    if exercise is None:
        return None

    hints = exercise["hints"]

    if 1 <= hint_number <= len(hints):
        return hints[hint_number - 1]

    return None
