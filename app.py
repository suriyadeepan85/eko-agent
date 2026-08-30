"""
Streamlit UI for the Enterprise Knowledge Ops Agent.

Displays multi-agent coordination trace: plan, retrievals, precedence rules,
attempts, and failures. Per specs/ui-spec.md, this is display work only -
no LLM calls, no logic, just rendering what the orchestrator produces.

Includes password gate and 30-question session cap per specs/deployment-spec.md
when deployed to Streamlit Cloud (both features are skipped for local development).
"""

import streamlit as st
import os
from src import ingestion, storage
from src.agents import orchestrator
from chromadb.errors import NotFoundError

# Deployment settings
SESSION_QUESTION_CAP = 30


# --- DEPLOYMENT FEATURES (PASSWORD GATE & SESSION CAP) ---

def is_deployment_mode() -> bool:
    """Check if running in deployment mode (Streamlit Cloud with password).

    Returns True if APP_PASSWORD exists in secrets, False otherwise.
    Local development has no APP_PASSWORD, so features are skipped.
    """
    try:
        return 'APP_PASSWORD' in st.secrets
    except Exception:
        return False


def check_password() -> bool:
    """Password gate for deployed app.

    Returns True if authenticated or if APP_PASSWORD not set (local dev).
    Shows password prompt and returns False if not authenticated.
    """
    if not is_deployment_mode():
        # Local development - no password needed
        return True

    # Initialize session state for password
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    # Already authenticated
    if st.session_state.authenticated:
        return True

    # Show password prompt (before any other content)
    st.title("Auto Insurance Policy Agent")
    st.write("This is a demonstration deployment. Please enter the access password.")

    password = st.text_input("Password", type="password", key="password_input")

    if st.button("Access", key="password_submit"):
        if password == st.secrets['APP_PASSWORD']:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password. Please try again.")

    return False


def init_session_state():
    """Initialize session state for question counting."""
    if 'question_count' not in st.session_state:
        st.session_state.question_count = 0


def increment_question_count():
    """Increment question count and check cap."""
    st.session_state.question_count += 1


def is_cap_reached() -> bool:
    """Check if session question cap is reached."""
    if not is_deployment_mode():
        # Local development - no cap
        return False
    return st.session_state.question_count >= SESSION_QUESTION_CAP


def render_session_info():
    """Display session info and exit button (deployment mode only)."""
    if not is_deployment_mode():
        return

    remaining = SESSION_QUESTION_CAP - st.session_state.question_count

    # Show in sidebar
    with st.sidebar:
        st.write("### Session Info")
        st.write(f"Questions asked: {st.session_state.question_count}/{SESSION_QUESTION_CAP}")

        if is_cap_reached():
            st.warning("Question limit reached for this session.")
        else:
            st.info(f"{remaining} questions remaining")

        if st.button("Exit Session", key="exit_session"):
            # Reset session state
            st.session_state.authenticated = False
            st.session_state.question_count = 0
            st.rerun()

        st.write("---")
        st.caption("💡 This is a hosted demo running on personal AWS credits. "
                   "The 30-question cap prevents unbounded spend. "
                   "Click 'Exit Session' to restart your count.")


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
    cap_reached = is_cap_reached()

    # Show cap message if reached
    if cap_reached:
        st.error(f"**Session limit reached:** You've asked {SESSION_QUESTION_CAP} questions in this session. "
                 "Click 'Exit Session' in the sidebar to start a new session.")

    # Text input (disabled until corpus loaded OR if cap reached)
    input_disabled = not is_loaded or cap_reached
    placeholder = ("Loading corpus..." if not is_loaded
                  else "Session limit reached" if cap_reached
                  else "Enter your question...")

    question = st.text_input(
        "Ask a question about your policy:",
        disabled=input_disabled,
        placeholder=placeholder
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
        if st.button(ex, disabled=input_disabled, use_container_width=True):
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

    # Password gate (deployment mode only) - must be first
    if not check_password():
        return

    # Initialize session state
    init_session_state()

    st.title("Auto Insurance Policy Agent")

    st.write("This is an agentic AI system that answers questions using the documents listed below, "
             "with specialised agents handling the reasoning.")
    st.write("Note that the corpus is synthetic test data, not real insurance guidance.")
    st.write("")

    # Session info sidebar (deployment mode only)
    render_session_info()

    # Corpus used by this app
    st.subheader("Corpus used by this app")

    # Corpus status
    render_corpus_status()

    # Question input with examples
    question = render_question_input()

    # Process and display
    if question:
        # Increment question count (deployment mode only)
        if is_deployment_mode():
            increment_question_count()

        with st.spinner("Processing question..."):
            record = orchestrator.run_pipeline(question)

        render_question_and_answer(record)
        render_sources(record)
        render_trace(record)


if __name__ == "__main__":
    main()
