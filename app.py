import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from analysis.fit import calculate_fit
from analysis.matching import compare_requirements_with_retrieval
from analysis.job_requirements import extract_job_requirements
from copilot.service import JobPilotCopilot
from db.chroma import add_candidate_evidence, create_collection
from ingestion.parser import parse_resume_text
from ingestion.resume import extract_text


st.set_page_config(
    page_title="JobPilot",
    page_icon="🎯",
    layout="wide",
)

st.markdown("""
<style>

    /* ================================
       JOBPILOT — B&W 3D BOX-SHADOW UI
       ================================ */

    .stApp {
        background: #f5e6d8 !important;
        color: #111111 !important;
    }

    .main {
        background: #f5e6d8 !important;
    }

    .block-container {
        max-width: 820px !important;
        padding-top: 2rem !important;
        padding-bottom: 5rem !important;
    }

    [data-testid="stHeader"] {
        background: #f5e6d8 !important;
    }

    /* ================================
       BOTTOM CHAT BAR
       ================================ */

    [data-testid="stBottom"] {
        background: #f5e6d8 !important;
    }

    [data-testid="stBottom"] > div {
        background: #f5e6d8 !important;
    }

    [data-testid="stBottomBlockContainer"] {
        background: #f5e6d8 !important;
        max-width: 820px !important;
    }

    footer {
        background: #f5e6d8 !important;
    }

    /* ================================
       TYPOGRAPHY
       ================================ */

    h1,
    h2,
    h3 {
        color: #111111 !important;
        letter-spacing: -0.045em !important;
    }

    h1 {
        font-size: 2.8rem !important;
        line-height: 1 !important;
        font-weight: 750 !important;
        margin-bottom: 0.4rem !important;
    }

    h2 {
        font-size: 1.7rem !important;
        font-weight: 700 !important;
    }

    h3 {
        font-size: 1.15rem !important;
        font-weight: 650 !important;
    }

    p,
    label {
        color: #111111 !important;
    }

    .hero-subtitle {
        font-size: 1.02rem !important;
        color: #444444 !important;
        margin-bottom: 2.5rem !important;
    }

    /* ================================
       FILE UPLOADER
       ================================ */

    [data-testid="stFileUploader"] {
        background: #ffffff !important;
        border: 1.5px solid #111111 !important;
        border-radius: 16px !important;
        padding: 0.8rem !important;
        box-shadow: 6px 6px 0 #111111 !important;
        overflow: visible !important;
    }

    [data-testid="stFileUploader"] section {
        background: #ffffff !important;
    }

    [data-testid="stFileUploaderDropzone"] {
        background: #ffffff !important;
        border: 1px dashed #999999 !important;
        border-radius: 11px !important;
    }

    [data-testid="stFileUploaderDropzone"] button {
        background: #111111 !important;
        color: #ffffff !important;
        border: 1px solid #111111 !important;
        border-radius: 9px !important;
    }

    [data-testid="stFileUploaderDropzone"] button p,
    [data-testid="stFileUploaderDropzone"] button span {
        color: #ffffff !important;
    }

    /* ================================
       TEXTAREA
       ================================ */

    [data-testid="stTextArea"] {
        overflow: visible !important;
    }

    [data-testid="stTextArea"] > div {
        background: #ffffff !important;
        border: 1.5px solid #111111 !important;
        border-radius: 16px !important;
        box-shadow: 6px 6px 0 #111111 !important;
        overflow: visible !important;
    }

    [data-testid="stTextArea"] textarea::-webkit-resizer {
        display: none !important;
        background: transparent !important;
    }

    [data-testid="stTextArea"] textarea {
        background: #ffffff !important;
        color: #111111 !important;
        border: none !important;
        border-radius: 16px !important;
        padding: 1rem !important;
        box-shadow: none !important;
        resize: none !important;
        height: 160px !important;
        min-height: 160px !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
    }

    [data-testid="stTextArea"] textarea::placeholder {
        color: #999999 !important;
    }

    /* ================================
       BUTTONS
       ================================ */

    .stButton > button {
        background: #ffffff !important;
        color: #111111 !important;
        border: 1.5px solid #111111 !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 0.55rem 1rem !important;
        box-shadow: 4px 4px 0 #111111 !important;
        transition: all 0.08s ease !important;
    }

    .stButton > button p {
        color: #111111 !important;
    }

    .stButton > button:active {
        transform: translate(4px, 4px) !important;
        box-shadow: 0 0 0 #111111 !important;
        background: #111111 !important;
    }

    .stButton > button:active p {
        color: #ffffff !important;
    }

    /* ================================
       PRIMARY BUTTON — ANALYZE JOB
       ================================ */

    .stButton > button[kind="primary"] {
        background: #111111 !important;
        color: #ffffff !important;
        border: 1.5px solid #111111 !important;
        border-radius: 10px !important;
        font-weight: 650 !important;
        padding: 0.65rem 1.5rem !important;
        box-shadow: 5px 5px 0 #111111 !important;
        transition: all 0.08s ease !important;
    }

    .stButton > button[kind="primary"] p {
        color: #ffffff !important;
    }

    .stButton > button[kind="primary"]:active {
        transform: translate(5px, 5px) !important;
        box-shadow: 0 0 0 #111111 !important;
        background: #222222 !important;
    }

    /* ================================
       METRIC CARDS
       ================================ */

    [data-testid="metric-container"] {
        background: #ffffff !important;
        border: 1.5px solid #111111 !important;
        border-radius: 16px !important;
        padding: 1.25rem 1.3rem !important;
        box-shadow: 5px 5px 0 #111111 !important;
    }

    [data-testid="stMetricLabel"] {
        color: #666666 !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
    }

    [data-testid="stMetricValue"] {
        color: #111111 !important;
        font-size: 2rem !important;
        font-weight: 750 !important;
        letter-spacing: -0.04em !important;
    }

    /* ================================
       CHAT MESSAGE
       ================================ */

    [data-testid="stChatMessage"] {
        background: #ffffff !important;
        color: #111111 !important;
        border: 1px solid #dddddd !important;
        border-radius: 14px !important;
        padding: 1rem !important;
        margin-bottom: 0.8rem !important;
    }

    /* FORCE EVERYTHING INSIDE CHAT TO DARK */
    [data-testid="stChatMessage"] * {
        color: #111111 !important;
    }

    /* Markdown container */
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
        color: #111111 !important;
    }

    /* Paragraphs */
    [data-testid="stChatMessage"] p {
        color: #111111 !important;
    }

    /* Lists */
    [data-testid="stChatMessage"] ul,
    [data-testid="stChatMessage"] ol,
    [data-testid="stChatMessage"] li {
        color: #111111 !important;
    }

    /* Headings */
    [data-testid="stChatMessage"] h1,
    [data-testid="stChatMessage"] h2,
    [data-testid="stChatMessage"] h3,
    [data-testid="stChatMessage"] h4,
    [data-testid="stChatMessage"] h5,
    [data-testid="stChatMessage"] h6 {
        color: #111111 !important;
    }

    /* Bold / italic */
    [data-testid="stChatMessage"] strong,
    [data-testid="stChatMessage"] b,
    [data-testid="stChatMessage"] em,
    [data-testid="stChatMessage"] i {
        color: #111111 !important;
    }

   /* ================================
   CHAT TABLES — FIXED LAYOUT
   ================================ */

    [data-testid="stChatMessage"] table {
        width: 100% !important;
        max-width: 100% !important;
        table-layout: fixed !important;
        border-collapse: collapse !important;
        background: #ffffff !important;
        color: #111111 !important;
        margin: 1rem 0 !important;
        font-size: 0.88rem !important;
    }

    /* Column widths */
    [data-testid="stChatMessage"] table th:nth-child(1),
    [data-testid="stChatMessage"] table td:nth-child(1) {
        width: 36% !important;
    }

    [data-testid="stChatMessage"] table th:nth-child(2),
    [data-testid="stChatMessage"] table td:nth-child(2) {
        width: 42% !important;
    }

    [data-testid="stChatMessage"] table th:nth-child(3),
    [data-testid="stChatMessage"] table td:nth-child(3) {
        width: 22% !important;
    }

    /* Table cells */
    [data-testid="stChatMessage"] table th,
    [data-testid="stChatMessage"] table td {
        color: #111111 !important;
        background: #ffffff !important;
        border: 1px solid #d9d9d9 !important;
        padding: 0.65rem 0.75rem !important;
        text-align: left !important;
        vertical-align: top !important;

        /* IMPORTANT — allows long AI text to wrap */
        white-space: normal !important;
        overflow-wrap: anywhere !important;
        word-break: normal !important;
    }

    /* Header */
    [data-testid="stChatMessage"] table th {
        font-weight: 700 !important;
        color: #111111 !important;
        background: #fafafa !important;
    }

    /* Body */
    [data-testid="stChatMessage"] table td {
        font-weight: 400 !important;
        line-height: 1.5 !important;
    }

    /* Prevent markdown container from forcing overflow */
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
        width: 100% !important;
        max-width: 100% !important;
        overflow-x: hidden !important;
    }

    /* Make sure table wrapper doesn't create weird overflow */
    [data-testid="stChatMessage"] div {
        max-width: 100% !important;
    }

    /* ================================
       CHAT CODE
       ================================ */

    [data-testid="stChatMessage"] code {
        color: #111111 !important;
        background: #f5f5f5 !important;
    }

    [data-testid="stChatMessage"] pre {
        color: #111111 !important;
        background: #f5f5f5 !important;
    }

    [data-testid="stChatMessage"] pre code {
        color: #111111 !important;
        background: #f5f5f5 !important;
    }

    /* ================================
       CHAT LINKS
       ================================ */

    [data-testid="stChatMessage"] a {
        color: #111111 !important;
    }

    /* ================================
       CHAT INPUT
       ================================ */

    [data-testid="stChatInput"] {
        background: #ffffff !important;
        border: 1.5px solid #111111 !important;
        border-radius: 14px !important;
        box-shadow: 4px 4px 0 #111111 !important;
        overflow: visible !important;
    }

    [data-testid="stChatInput"] textarea {
        box-shadow: none !important;
        border: none !important;
        background: #ffffff !important;
        color: #111111 !important;
        caret-color: #111111 !important;
    }

    [data-testid="stChatInput"] textarea::placeholder {
        color: #999999 !important;
    }

    [data-testid="stChatInputSubmitButton"] {
        background: #111111 !important;
        border-radius: 8px !important;
    }

    [data-testid="stChatInputSubmitButton"] svg {
        fill: #ffffff !important;
    }

    [data-testid="stChatInputSubmitButton"]:disabled {
        background: #cccccc !important;
    }

    [data-testid="stChatInputSubmitButton"]:disabled svg {
        fill: #ffffff !important;
    }

    /* ================================
       DIVIDER
       ================================ */

    hr {
        border: none !important;
        border-top: 1px solid #dddddd !important;
        margin: 2.5rem 0 !important;
    }

    /* ================================
       CAPTIONS
       ================================ */

    [data-testid="stCaptionContainer"] {
        color: #111111 !important;
    }

    [data-testid="stCaptionContainer"] p {
        color: #111111 !important;
    }

    /* ================================
       ALERTS
       ================================ */

    [data-testid="stAlert"] {
        background: #ffffff !important;
        color: #111111 !important;
        border-radius: 12px !important;
        border: 1.5px solid #111111 !important;
        box-shadow: 4px 4px 0 #111111 !important;
    }

    [data-testid="stAlert"] * {
        color: #111111 !important;
    }

</style>
""", unsafe_allow_html=True)
st.title("🎯🛫 JobPilot")

st.markdown(
    '<div class="hero-subtitle">'
    'Evidence-grounded job application copilot'
    '</div>',
    unsafe_allow_html=True,
)


def clean_answer(text: str) -> str:
    """Strip stray HTML tags LLM sometimes emits, use markdown newlines instead."""
    return (
        text.replace("<br>", "\n")
        .replace("<br/>", "\n")
        .replace("<br />", "\n")
    )


resume_file = st.file_uploader(
    "Upload your resume",
    type=["pdf"],
)

jd_text = st.text_area(
    "Paste the job description",
    height=300,
    placeholder="Paste the full job description here...",
)

analyze = st.button(
    "Analyze Job",
    type="primary",
)


if analyze:

    if resume_file is None:
        st.error("Please upload your resume.")

    elif not jd_text.strip():
        st.error("Please paste the job description.")

    else:
        with st.spinner("Analyzing your resume and job..."):

            # -------------------------------------------------
            # 1. Parse resume
            # -------------------------------------------------

            resume_path = Path("data") / resume_file.name
            resume_path.parent.mkdir(parents=True, exist_ok=True)
            resume_path.write_bytes(resume_file.getvalue())

            resume_text = extract_text(resume_path)
            profile = parse_resume_text(resume_text)

            # -------------------------------------------------
            # 2. Store candidate evidence
            # -------------------------------------------------

            collection = create_collection()

            add_candidate_evidence(
                collection,
                profile,
            )

            # -------------------------------------------------
            # 3. Parse job description
            # -------------------------------------------------

            requirements = extract_job_requirements(
                jd_text
            )

            # -------------------------------------------------
            # 4. Match requirements
            # -------------------------------------------------

            job_match = compare_requirements_with_retrieval(
                requirements,
                collection,
            )

            # -------------------------------------------------
            # 5. Calculate fit
            # -------------------------------------------------

            fit = calculate_fit(job_match)

            # -------------------------------------------------
            # 6. Store everything in session
            # -------------------------------------------------

            st.session_state["profile"] = profile
            st.session_state["requirements"] = requirements
            st.session_state["job_match"] = job_match
            st.session_state["fit"] = fit

            st.session_state["analysis"] = {
                "fit": fit,
                "matches": [
                    match.model_dump()
                    for match in job_match.matches
                ],
            }

            st.session_state["chat_history"] = []

        st.success("Analysis complete.")


# =============================================================
# Analysis results
# =============================================================

if "fit" in st.session_state:

    fit = st.session_state["fit"]

    st.subheader("Job Fit")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Job Fit",
        f"{fit['fit_score']}/100",
    )

    col2.metric(
        "Strong",
        fit["strong_matches"],
    )

    col3.metric(
        "Partial",
        fit["partial_matches"],
    )

    col4.metric(
        "No Evidence",
        fit["no_evidence"],
    )

st.caption(
    "Job Fit measures how well this job's requirements are supported "
    "by evidence in your resume. It is not a hiring probability or resume quality score."
)

# =============================================================
# Chat
# =============================================================

if "analysis" in st.session_state:

    st.divider()

    st.subheader("Chat with JobPilot")

    st.caption(
        "Ask questions about your fit, gaps, resume, or the job."
    )

    suggested_questions = [
        "Should I apply?",
        "What should I improve?",
        "What should I learn?",
    ]

    cols = st.columns(3)

    for index, question in enumerate(
        suggested_questions
    ):
        if cols[index].button(question):
            st.session_state["pending_question"] = question


    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []


    # Display previous messages.

    for message in st.session_state["chat_history"]:

        with st.chat_message(message["role"]):
            st.markdown(clean_answer(message["content"]))


    user_question = st.chat_input(
        "Ask JobPilot anything about this job..."
    )


    question = (
        user_question
        or st.session_state.pop(
            "pending_question",
            None,
        )
    )


    if question:

        st.session_state["chat_history"].append(
            {
                "role": "user",
                "content": question,
            }
        )

        with st.chat_message("user"):
            st.markdown(question)


        with st.chat_message("assistant"):

            with st.spinner("Thinking..."):

                copilot = JobPilotCopilot()

                answer = copilot.answer(
                    question=question,
                    analysis=st.session_state["analysis"],
                    conversation_history=st.session_state["chat_history"][-6:-1],
                )

                answer = clean_answer(answer)

                st.markdown(answer)


        st.session_state["chat_history"].append(
            {
                "role": "assistant",
                "content": answer,
            }
        )