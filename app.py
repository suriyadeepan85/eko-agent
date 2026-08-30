"""
Streamlit UI for the Enterprise Knowledge Ops Agent.

Displays multi-agent coordination trace: plan, retrievals, precedence rules,
attempts, and failures. Per specs/ui-spec.md, this is display work only -
no LLM calls, no logic, just rendering what the orchestrator produces.
"""

import streamlit as st
import os
from src import ingestion, storage
from src.agents import orchestrator
from chromadb.errors import NotFoundError


# --- CORPUS MANAGEMENT ---

@st.cache_resource
def get_chroma_client():
    """Cached Chroma client - survives reruns."""
    return storage.get_chroma_client()


def check_corpus_loaded() -> tuple[bool, int]:
    """Check if corpus is loaded and return (is_loaded, count)."""
    client = get_chroma_client()
    try:
        collection = client.get_collection("acme_auto_corpus")
        count = collection.count()
        return (count == 20, count)
    except NotFoundError:
        return (False, 0)


@st.cache_resource
def ensure_corpus_loaded() -> int:
    """Load corpus if not already loaded. Returns chunk count."""
    is_loaded, count = check_corpus_loaded()
    if not is_loaded:
        with st.spinner("Loading corpus (first run only)..."):
            count = ingestion.ingest("documents/")
    return count


# --- UI COMPONENTS ---

def render_corpus_status():
    """Display corpus loading status with expandable details."""
    count = ensure_corpus_loaded()

    with st.expander("Corpus Status", expanded=False):
        st.success(f"✓ Corpus loaded: {count} documents")

        # Document list with content viewer
        docs = sorted([f for f in os.listdir("documents") if f.endswith(".md")])
        st.write("**Documents:**")

        for doc in docs:
            with st.expander(f"📄 {doc}"):
                # Read and display document content
                doc_path = os.path.join("documents", doc)
                with open(doc_path, 'r') as f:
                    content = f.read()
                st.text(content)

        # Re-ingest button
        if st.button("Re-ingest Corpus"):
            st.cache_resource.clear()
            st.rerun()


def render_question_input() -> str | None:
    """Render question input with example buttons."""
    is_loaded, _ = check_corpus_loaded()

    # Text input (disabled until corpus loaded)
    question = st.text_input(
        "Ask a question about your policy:",
        disabled=not is_loaded,
        placeholder="Enter your question..." if is_loaded else "Loading corpus..."
    )

    # Example buttons (vertical layout with full question text)
    st.write("**Try these examples:**")

    examples = [
        "How many days of rental am I covered for and at what rate?",
        "A hailstorm damaged 200 cars in one county. How does that change handling?",
        "After my car is repaired, do you pay me for the lost resale value?"
    ]

    # Button handling with session state (vertical layout, full text)
    for ex in examples:
        if st.button(ex, disabled=not is_loaded, use_container_width=True):
            st.session_state.selected_question = ex
            st.rerun()

    # Return selected or typed question
    if 'selected_question' in st.session_state:
        q = st.session_state.selected_question
        del st.session_state.selected_question
        return q
    return question if question else None


def render_question_and_answer(record):
    """Display question and answer with same prominence for acceptance or refusal."""
    data = record.to_dict()

    st.header("Question")
    st.write(data['question'])

    st.header("Answer")
    st.write(data['answer'])


def render_sources(record):
    """Display cited documents."""
    data = record.to_dict()
    st.header("Sources")
    if data['sources']:
        for doc_id in data['sources']:
            st.text(f"• {doc_id}")
    else:
        st.text("No sources cited")


def render_trace(record):
    """Render complete trace with expandable panels."""
    data = record.to_dict()
    st.header("Trace")

    # Plan
    with st.expander("Plan", expanded=False):
        plan = data['plan']
        if plan.get('decomposed'):
            st.write("**Decomposed:** Yes")
            st.write("**Sub-questions:**")
            for sq in plan['sub_questions']:
                st.text(f"  • {sq}")
        else:
            st.write("**Decomposed:** No (direct query)")

    # Retrievals
    with st.expander("Retrievals", expanded=False):
        render_retrievals(data['retrievals'])

    # Attempts
    with st.expander("Attempts", expanded=False):
        render_attempts(data['attempts'])

    # Precedence (expanded by default per spec line 141)
    with st.expander("Precedence", expanded=True):
        render_precedence(data['precedence_applied'])

    # Failures
    with st.expander("Failures", expanded=False):
        render_failures(data['failures'])


def render_retrievals(retrievals: list):
    """Display retrieval results with scores as similarity."""
    SIMILARITY_FLOOR = 0.44
    st.write(f"**Similarity floor:** {SIMILARITY_FLOOR} (higher = better match)")
    st.write("")

    for i, ret in enumerate(retrievals, 1):
        st.write(f"**Sub-question {i}:** {ret['sub_question']}")
        st.write(f"Retrieved {len(ret['chunks'])} chunks (k={ret['k']})")

        if ret['chunks']:
            # Table header
            cols = st.columns([2, 1, 2, 2])
            with cols[0]: st.write("**Doc ID**")
            with cols[1]: st.write("**Score**")
            with cols[2]: st.write("**Effective Date**")
            with cols[3]: st.write("**Authority Tier**")

            # Chunks
            for chunk in ret['chunks']:
                cols = st.columns([2, 1, 2, 2])
                with cols[0]: st.text(chunk['doc_id'])
                with cols[1]: st.text(f"{chunk['score']:.4f}")
                with cols[2]: st.text(chunk.get('effective_date') or 'N/A')
                with cols[3]: st.text(chunk.get('authority_tier') or 'N/A')

        st.write("---")


def render_attempts(attempts: list):
    """Display reasoning attempts with verdicts."""
    for att in attempts:
        verdict_icon = "✓" if att['verdict'] == 'accepted' else "✗"
        st.write(f"**Attempt {att['attempt']}:** {verdict_icon} {att['verdict']}")

        with st.expander(f"View draft {att['attempt']}"):
            st.write(att['draft'])

        if att.get('reason'):
            st.warning(f"**Rejection reason:** {att['reason']}")

        # Claims
        st.write(f"**Claims ({len(att['claims'])}):**")
        for claim in att['claims']:
            doc_ids = ', '.join(claim['doc_ids'])
            st.text(f"  • {claim['claim']} → [{doc_ids}]")

        st.write("")


def render_precedence(precedence_list: list):
    """Display precedence rules applied."""
    if not precedence_list:
        st.text("No precedence rules applied")
        return

    for prec in precedence_list:
        st.write(f"**Rule:** `{prec['rule']}`")
        st.write(f"**Winner:** {prec['winner']} supersedes {prec['over']}")
        st.write("---")


def render_failures(failures: list):
    """Display failures or 'none detected'."""
    if not failures:
        st.success("None detected")
        return

    for fail in failures:
        st.error(f"**{fail['type']}**")
        if 'details' in fail:
            st.json(fail['details'])


# --- MAIN ---

def main():
    st.set_page_config(page_title="Acme Auto Insurance Agent", layout="wide")
    st.title("Acme Auto Insurance Policy Agent")

    # Corpus status
    render_corpus_status()

    # Question input with examples
    question = render_question_input()

    # Process and display
    if question:
        with st.spinner("Processing question..."):
            record = orchestrator.run_pipeline(question)

        render_question_and_answer(record)
        render_sources(record)
        render_trace(record)


if __name__ == "__main__":
    main()
