
"""
Prerequisite Knowledge Mapper
Builds a learning path from prerequisite relationships.
"""

from collections import deque


# Each topic lists the topics a student should know first.
PREREQUISITES = {
    "Python Basics": [],
    "Variables and Data Types": ["Python Basics"],
    "Conditions and Loops": ["Variables and Data Types"],
    "Functions": ["Conditions and Loops"],
    "Lists and Dictionaries": ["Variables and Data Types"],
    "Basic Mathematics": [],
    "Algebra": ["Basic Mathematics"],
    "Statistics": ["Basic Mathematics"],
    "Probability": ["Statistics"],
    "NumPy": ["Python Basics", "Lists and Dictionaries"],
    "Pandas": ["Python Basics", "Lists and Dictionaries"],
    "Data Visualization": ["Pandas", "Basic Mathematics"],
    "Machine Learning Basics": [
        "Python Basics",
        "Algebra",
        "Statistics",
        "Probability",
        "NumPy",
    ],
    "Deep Learning Basics": ["Machine Learning Basics"],
}

def get_all_prerequisites(target_topic):
    """Return prerequisites with foundations before advanced topics."""
    if target_topic not in PREREQUISITES:
        return []

    ordered = []
    visited = set()

    def visit(topic):
        if topic in visited:
            return

        visited.add(topic)

        for prerequisite in PREREQUISITES.get(topic, []):
            visit(prerequisite)

        if topic != target_topic:
            ordered.append(topic)

    visit(target_topic)
    return ordered



def create_learning_plan(target_topic, known_topics=None):
    """
    Create a learning plan excluding topics the student already knows.

    Returns a dictionary containing the target, known prerequisites,
    and topics recommended for study.
    """
    known_topics = set(known_topics or [])
    prerequisites = get_all_prerequisites(target_topic)

    missing_topics = [
        topic for topic in prerequisites if topic not in known_topics
    ]

    return {
        "target_topic": target_topic,
        "known_prerequisites": [
            topic for topic in prerequisites if topic in known_topics
        ],
        "missing_prerequisites": missing_topics,
        "learning_order": missing_topics + [target_topic],
    }


def get_available_topics():
    """Return all available topics."""
    return list(PREREQUISITES.keys())
