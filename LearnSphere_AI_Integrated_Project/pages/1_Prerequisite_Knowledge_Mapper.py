
import streamlit as st
import plotly.graph_objects as go
from collections import deque

def create_prerequisite_graph(target_topic, known_topics):
    """Create a clear, card-based prerequisite roadmap."""

    import plotly.graph_objects as go
    from collections import deque
    from modules.prerequisite_mapper import PREREQUISITES

    known_topics = set(known_topics or [])

    # Collect the target and all its prerequisite topics.
    nodes = []
    edges = []
    visited = set()
    queue = deque([target_topic])

    while queue:
        topic = queue.popleft()

        if topic in visited:
            continue

        visited.add(topic)
        nodes.append(topic)

        for prerequisite in PREREQUISITES.get(topic, []):
            edges.append((prerequisite, topic))
            queue.append(prerequisite)

    # Calculate each topic's stage in the learning journey.
    depths = {}

    def get_depth(topic, visiting=None):
        if topic in depths:
            return depths[topic]

        if visiting is None:
            visiting = set()

        if topic in visiting:
            return 0  # Safety against circular dependencies.

        visiting = visiting | {topic}
        prerequisites = PREREQUISITES.get(topic, [])

        if not prerequisites:
            depths[topic] = 0
        else:
            depths[topic] = 1 + max(
                get_depth(p, visiting) for p in prerequisites
            )

        return depths[topic]

    for topic in nodes:
        get_depth(topic)

    layers = {}
    for topic in nodes:
        layers.setdefault(depths[topic], []).append(topic)

    # Place foundation topics on the left and the target on the right.
    positions = {}

    for layer, topics_in_layer in layers.items():
        count = len(topics_in_layer)

        for index, topic in enumerate(topics_in_layer):
            positions[topic] = (
                layer * 2.8,
                (count - 1) / 2 - index,
            )

    fig = go.Figure()

    # Draw connections first so they sit behind the topic cards.
    for source, destination in edges:
        x1, y1 = positions[source]
        x2, y2 = positions[destination]

        fig.add_annotation(
            x=x2 - 0.83,
            y=y2,
            ax=x1 + 0.83,
            ay=y1,
            xref="x",
            yref="y",
            axref="x",
            ayref="y",
            text="",
            showarrow=True,
            arrowhead=3,
            arrowsize=1.1,
            arrowwidth=2,
            arrowcolor="#CBD5E1",
        )

    # Draw attractive rectangular topic cards.
    for topic in nodes:
        x, y = positions[topic]

        if topic == target_topic:
            fill = "#DBEAFE"
            border = "#2563EB"
            title_color = "#1D4ED8"
            status = "YOUR GOAL"
        elif topic in known_topics:
            fill = "#DCFCE7"
            border = "#16A34A"
            title_color = "#166534"
            status = "✓ ALREADY KNOW"
        else:
            fill = "#FEF3C7"
            border = "#D97706"
            title_color = "#92400E"
            status = "TO LEARN"

        fig.add_shape(
            type="rect",
            x0=x - 0.82,
            x1=x + 0.82,
            y0=y - 0.38,
            y1=y + 0.38,
            line=dict(color=border, width=2),
            fillcolor=fill,
            layer="above",
        )

        fig.add_annotation(
            x=x,
            y=y + 0.07,
            text=f"<b>{topic}</b>",
            showarrow=False,
            font=dict(size=12, color=title_color),
            align="center",
        )

        fig.add_annotation(
            x=x,
            y=y - 0.19,
            text=status,
            showarrow=False,
            font=dict(size=9, color=title_color),
            align="center",
        )

    # Label the learning stages.
    for layer in sorted(layers):
        x = layer * 2.8
        fig.add_annotation(
            x=x,
            y=max(positions[t][1] for t in layers[layer]) + 0.85,
            text=f"<b>STAGE {layer + 1}</b>",
            showarrow=False,
            font=dict(size=11, color="#64748B"),
        )

    max_y = max(y for x, y in positions.values())
    min_y = min(y for x, y in positions.values())
    max_x = max(x for x, y in positions.values())

    fig.update_layout(
        title=dict(
            text="YOUR LEARNING ROADMAP",
            font=dict(size=20, color="#0F172A"),
            x=0.02,
        ),
        height=max(460, (max_y - min_y + 3) * 100),
        margin=dict(l=35, r=35, t=100, b=35),
        paper_bgcolor="#F8FAFC",
        plot_bgcolor="#F8FAFC",
        showlegend=False,
        hovermode=False,
        font=dict(family="Arial, sans-serif"),
    )

    fig.update_xaxes(
        visible=False,
        range=[-1.4, max_x + 1.4],
        fixedrange=True,
    )
    fig.update_yaxes(
        visible=False,
        range=[min_y - 1.0, max_y + 1.2],
        fixedrange=True,
    )

    return fig

from modules.prerequisite_mapper import (
    create_learning_plan,
    get_available_topics,
)

st.set_page_config(
    page_title="Prerequisite Knowledge Mapper",
    page_icon="🧭",
    layout="wide",
)

from modules.ui_theme import apply_theme
apply_theme()

st.title("🧭 Prerequisite Knowledge Mapper")
st.write(
    "Discover what you should learn first and create a learning path "
    "based on the topics you already understand."
)

topics = get_available_topics()

target_topic = st.selectbox(
    "What topic do you want to learn?",
    topics,
    index=topics.index("Machine Learning Basics"),
)

st.subheader("What do you already know?")
st.write("Select all topics you feel comfortable with.")

possible_prerequisites = [
    topic for topic in topics if topic != target_topic
]

known_topics = st.multiselect(
    "Topics I already know",
    possible_prerequisites,
    default=["Python Basics"] if "Python Basics" in possible_prerequisites else [],
)

if st.button("Generate My Learning Path", type="primary"):
    plan = create_learning_plan(target_topic, known_topics)

    st.subheader("Your personalized learning path")

    if plan["missing_prerequisites"]:
        st.warning(
            f"You have {len(plan['missing_prerequisites'])} "
            "prerequisite topic(s) to review."
        )

        for number, topic in enumerate(
            plan["missing_prerequisites"], start=1
        ):
            st.write(f"{number}. 📘 {topic}")
    else:
        st.success("You have marked all listed prerequisites as known!")
    
    
    
    
    total_prerequisites = len(plan["known_prerequisites"]) + len(
        plan["missing_prerequisites"]
    )
    completed = len(plan["known_prerequisites"])
    progress = completed / total_prerequisites if total_prerequisites else 1.0

    col1, col2, col3 = st.columns(3)

    col1.metric("Prerequisites identified", total_prerequisites)
    col2.metric("Already known", completed)
    col3.metric("Still to learn", len(plan["missing_prerequisites"]))

    st.progress(progress, text=f"Prerequisite progress: {progress:.0%}")
    
    st.subheader("Visual prerequisite map")

    graph = create_prerequisite_graph(
        target_topic,
        known_topics,
    )

    st.plotly_chart(graph, use_container_width=True)

    st.caption(
        "🟦 Blue: target topic | "
        "🟩 Green: topics you know | "
        "🟧 Orange: topics to review"
    )
    st.subheader("Recommended study order")

    for number, topic in enumerate(plan["learning_order"], start=1):
        if topic == target_topic:
            st.success(f"{number}. 🎯 {topic} — Your target")
        else:
            st.write(f"{number}. 📖 {topic}")

    st.info(
        "This learning path uses a predefined prerequisite map. "
        "Check that the suggested topics match your course syllabus."
    )

