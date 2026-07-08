import os
import json
from html import escape

import requests
import streamlit as st
import streamlit.components.v1 as components

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

TEMPLATES = {
    "-- Select a template --": None,
    "Interview Scheduling": {
        "purpose": "Interview Scheduling",
        "key_points": "Interview scheduled for Monday at 11 AM over Microsoft Teams. Meeting link will follow separately.",
        "tone": "Professional",
        "length": "Concise",
    },
    "Offer Letter Follow-up": {
        "purpose": "Offer Letter Follow-up",
        "key_points": "Follow up on the offer letter sent last week. Ask if there are any questions and request confirmation by Friday.",
        "tone": "Friendly",
        "length": "Standard",
    },
    "Client Status Update": {
        "purpose": "Client Status Update",
        "key_points": "Weekly update on the candidate pipeline for the open role. 3 candidates shortlisted. First-round interviews scheduled next week.",
        "tone": "Formal",
        "length": "Detailed",
    },
    "Meeting Rescheduling": {
        "purpose": "Meeting Rescheduling",
        "key_points": "Reschedule the team meeting from Wednesday to Thursday at the same time, 3 PM. Updated calendar invite will follow.",
        "tone": "Professional",
        "length": "Concise",
    },
    "Onboarding Welcome": {
        "purpose": "Onboarding Welcome",
        "key_points": "Welcome the new employee to the team. Start date is next Monday. Orientation at 9 AM. Bring laptop and ID proof.",
        "tone": "Friendly",
        "length": "Standard",
    },
}

st.set_page_config(page_title="BSS AI Email Generator", page_icon="\U0001F4E7", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

    :root {
        --bg: #f5f7fb;
        --surface: #ffffff;
        --surface-soft: #f8fafc;
        --text: #172033;
        --muted: #5f6b7a;
        --border: #d9e0ea;
        --primary: #236a68;
        --primary-dark: #184f4d;
        --accent: #c2410c;
        --accent-soft: #fff1e8;
        --success: #2f7d4f;
        --success-soft: #e8f5ed;
        --shadow: 0 10px 28px rgba(29, 41, 57, 0.08);
    }

    html, body, [class*="css"] {
        font-family: 'Manrope', sans-serif;
    }

    .stApp {
        background:
            linear-gradient(rgba(217, 224, 234, 0.36) 1px, transparent 1px),
            linear-gradient(90deg, rgba(217, 224, 234, 0.36) 1px, transparent 1px),
            var(--bg);
        background-size: 28px 28px;
        color: var(--text);
    }

    .block-container {
        max-width: 1180px;
        padding-top: 1rem;
        padding-bottom: 1.5rem;
    }

    .app-titlebar {
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        gap: 1rem;
        padding: 0.55rem 0 0.9rem;
        border-bottom: 1px solid var(--border);
        margin-bottom: 1rem;
    }

    .app-titlebar h1 {
        color: var(--text);
        font-size: 1.9rem;
        line-height: 1.12;
        margin: 0.1rem 0 0.25rem;
        letter-spacing: 0;
        font-weight: 800;
    }

    .app-titlebar p {
        color: var(--muted) !important;
        margin: 0;
        font-size: 0.92rem;
    }

    .eyebrow {
        color: var(--primary) !important;
        font-size: 0.72rem !important;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .backend-pill {
        flex: 0 0 auto;
        border: 1px solid var(--border);
        background: var(--surface);
        border-radius: 8px;
        padding: 0.55rem 0.7rem;
        color: var(--muted);
        font-size: 0.78rem;
        box-shadow: var(--shadow);
    }

    .backend-pill strong {
        display: block;
        color: var(--text);
        font-size: 0.75rem;
        margin-bottom: 0.1rem;
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        box-shadow: var(--shadow);
        padding: 0.65rem 0.55rem;
    }

    [data-testid="stSidebar"] {
        background: #eef3f7;
        border-right: 1px solid var(--border);
    }

    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: var(--text);
        font-size: 1rem;
        letter-spacing: 0;
    }

    [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] p {
        color: var(--muted) !important;
    }

    [data-testid="stSidebar"] .stButton > button {
        min-height: 44px;
        justify-content: flex-start;
        text-align: left;
        white-space: normal;
        background: var(--surface) !important;
        color: var(--text) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        box-shadow: none !important;
        font-weight: 650 !important;
        padding: 0.55rem 0.65rem !important;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        border-color: var(--primary) !important;
        background: #f9fbfc !important;
        color: var(--primary-dark) !important;
    }

    [data-testid="stSidebar"] .stButton > button p,
    .stButton > button p {
        color: inherit !important;
    }

    .section-head {
        display: flex;
        gap: 0.65rem;
        align-items: flex-start;
        margin-bottom: 0.9rem;
    }

    .section-number {
        width: 1.65rem;
        height: 1.65rem;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        flex: 0 0 auto;
        border-radius: 6px;
        background: var(--primary);
        color: #ffffff;
        font-size: 0.82rem;
        font-weight: 800;
    }

    .section-head strong {
        color: var(--text);
        font-size: 1rem;
        line-height: 1.2;
    }

    .section-head p {
        color: var(--muted) !important;
        margin: 0.15rem 0 0;
        font-size: 0.84rem;
    }

    .hint-row {
        display: flex;
        gap: 0.45rem;
        flex-wrap: wrap;
        margin: 0.15rem 0 0.8rem;
    }

    .hint-pill {
        border-radius: 999px;
        border: 1px solid var(--border);
        background: var(--surface-soft);
        color: var(--muted);
        padding: 0.28rem 0.55rem;
        font-size: 0.72rem;
        font-weight: 700;
    }

    label, .stMarkdown p {
        color: #3e4856 !important;
    }

    .stTextInput label, .stTextArea label, .stSelectbox label {
        font-weight: 700 !important;
        font-size: 0.9rem !important;
    }

    .stTextInput input,
    .stTextArea textarea,
    div[data-baseweb="select"] > div {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--text) !important;
        box-shadow: none !important;
        min-height: 42px;
    }

    .stTextInput input:focus,
    .stTextArea textarea:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(35, 106, 104, 0.14) !important;
    }

    .stButton > button {
        border-radius: 8px !important;
        min-height: 42px;
        font-weight: 750 !important;
    }

    .stButton > button[kind="primary"] {
        background: var(--primary) !important;
        border: 1px solid var(--primary) !important;
        color: #ffffff !important;
        box-shadow: 0 8px 20px rgba(35, 106, 104, 0.22) !important;
    }

    .stButton > button[kind="primary"]:hover {
        background: var(--primary-dark) !important;
        border-color: var(--primary-dark) !important;
    }

    .stButton > button:not([kind="primary"]) {
        background: var(--surface-soft) !important;
        border: 1px solid var(--border) !important;
        color: var(--text) !important;
    }

    .stButton > button:not([kind="primary"]):hover {
        border-color: var(--primary) !important;
        color: var(--primary-dark) !important;
    }

    .char-counter {
        text-align: right;
        font-size: 0.72rem;
        color: var(--muted);
        margin-top: -0.35rem;
    }
    .char-counter.warn { color: #9a5b00; }
    .char-counter.over { color: #b42318; }

    .email-card-native {
        border: 1px solid var(--border);
        border-radius: 8px;
        background: #ffffff;
        margin: 0.65rem 0 0.75rem;
        overflow: hidden;
    }

    .email-subject {
        display: flex;
        align-items: center;
        gap: 0.55rem;
        padding: 0.8rem 0.9rem;
        border-bottom: 1px solid var(--border);
        color: var(--text);
        font-size: 0.98rem;
        font-weight: 800;
        flex-wrap: wrap;
    }

    .badge {
        display: inline-flex;
        align-items: center;
        border-radius: 999px;
        padding: 0.18rem 0.45rem;
        background: var(--success-soft);
        color: var(--success);
        font-size: 0.68rem;
        font-weight: 800;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    .email-body {
        padding: 0.9rem;
        background: linear-gradient(180deg, #ffffff, #fbfcfd);
    }

    .email-body p {
        color: #344054 !important;
        line-height: 1.65;
        margin: 0 0 0.78rem;
        font-size: 0.95rem;
    }

    .preview-topline {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
        margin-bottom: 0.25rem;
    }

    .preview-status {
        border-radius: 999px;
        background: var(--success-soft);
        color: var(--success);
        padding: 0.28rem 0.55rem;
        font-size: 0.72rem;
        font-weight: 800;
        white-space: nowrap;
    }

    .empty-state {
        min-height: 330px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 0.55rem;
        border: 1px dashed #b9c4d1;
        border-radius: 8px;
        background: var(--surface-soft);
        padding: 1.2rem;
    }

    .empty-state h4 {
        color: var(--text);
        margin: 0;
        font-size: 1.05rem;
    }

    .empty-state p {
        color: var(--muted) !important;
        margin: 0;
        font-size: 0.9rem;
    }

    .empty-steps {
        display: grid;
        gap: 0.5rem;
        margin-top: 0.65rem;
    }

    .empty-step {
        display: grid;
        grid-template-columns: 1.5rem 1fr;
        align-items: center;
        gap: 0.55rem;
        color: #344054;
        font-size: 0.86rem;
    }

    .empty-step span {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 1.5rem;
        height: 1.5rem;
        border-radius: 6px;
        background: #e6edf3;
        color: var(--primary-dark);
        font-weight: 800;
    }

    @media (max-width: 900px) {
        .block-container { padding-top: 0.75rem; }
        .app-titlebar { align-items: flex-start; flex-direction: column; }
        .backend-pill { width: 100%; box-sizing: border-box; }
        .app-titlebar h1 { font-size: 1.55rem; }
        .preview-topline { align-items: flex-start; flex-direction: column; }
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="app-titlebar">
        <div>
            <p class="eyebrow">Bangalore Strategic Solutions</p>
            <h1>BSS AI Email Generator</h1>
            <p>Create a polished recruiting email from purpose, recipient details, and a few key points.</p>
        </div>
        <div class="backend-pill">
            <strong>Backend</strong>
            {escape(BACKEND_URL)}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

for key, default in {
    "purpose": "",
    "recipient_name": "",
    "sender_name": "",
    "designation": "",
    "key_points": "",
    "tone": "Professional",
    "length": "Standard",
    "current_email": None,
    "selected_history_id": None,
    "history_error": "",
}.items():
    st.session_state.setdefault(key, default)


def apply_template():
    tpl = TEMPLATES.get(st.session_state.template_choice)
    if tpl:
        st.session_state.purpose = tpl["purpose"]
        st.session_state.key_points = tpl["key_points"]
        st.session_state.tone = tpl["tone"]
        st.session_state.length = tpl["length"]


def clear_form():
    st.session_state.purpose = ""
    st.session_state.recipient_name = ""
    st.session_state.sender_name = ""
    st.session_state.designation = ""
    st.session_state.key_points = ""
    st.session_state.tone = "Professional"
    st.session_state.length = "Standard"
    st.session_state.current_email = None
    st.session_state.selected_history_id = None
    st.session_state.history_error = ""


def render_panel_header(number: str, title: str, helper: str):
    st.markdown(
        f"""
        <div class="section-head">
            <div class="section-number">{escape(number)}</div>
            <div>
                <strong>{escape(title)}</strong>
                <p>{escape(helper)}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_email_native(subject: str, body: str):
    subject_safe = escape(subject or "Untitled")
    body_parts = [part.strip() for part in (body or "").split("\n") if part.strip()]
    paragraphs = "".join(f"<p>{escape(part)}</p>" for part in body_parts)
    st.markdown(
        f"""
        <div class="email-card-native">
            <div class="email-subject">
                <span class="badge">Draft</span>
                <span>Subject: {subject_safe}</span>
            </div>
            <div class="email-body">{paragraphs}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def copy_email_button(subject: str, body: str):
    full_text = f"Subject: {subject}\n\n{body}"
    safe_text = json.dumps(full_text)
    copy_html = f"""
    <button id="copyBtn" onclick="
        navigator.clipboard.writeText({safe_text}).then(function() {{
            document.getElementById('copyBtn').innerHTML = 'Copied';
            setTimeout(function() {{
                document.getElementById('copyBtn').innerHTML = 'Copy email';
            }}, 1600);
        }});
    " style="
        background: #236a68;
        color: #ffffff;
        border: 1px solid #236a68;
        border-radius: 8px;
        padding: 0.62rem 1rem;
        font: 700 14px Manrope, sans-serif;
        cursor: pointer;
        width: 100%;
        min-height: 42px;
    ">Copy email</button>
    """
    components.html(copy_html, height=48)


def call_backend(path: str, payload: dict):
    try:
        resp = requests.post(f"{BACKEND_URL}{path}", json=payload, timeout=30)
    except requests.exceptions.ConnectionError:
        st.error(
            f"Can't reach the backend at {BACKEND_URL}. Start it with "
            "`uvicorn backend.main:app --reload`."
        )
        return None

    if resp.status_code == 429:
        st.error("You're generating a bit fast. Wait a few seconds and try again.")
        return None
    if resp.status_code >= 400:
        try:
            detail = resp.json().get("detail", "Something went wrong.")
        except ValueError:
            detail = "Something went wrong."
        st.error(detail)
        return None
    return resp.json()


def load_history_email(email_id: int) -> bool:
    try:
        resp = requests.get(f"{BACKEND_URL}/api/email/{email_id}", timeout=10)
    except requests.exceptions.ConnectionError:
        st.session_state.history_error = "Backend is not running, so history cannot open yet."
        return False

    if resp.status_code == 200:
        st.session_state.current_email = resp.json()
        st.session_state.selected_history_id = email_id
        st.session_state.history_error = ""
        return True

    st.session_state.history_error = "That draft could not be opened. Generate a new one or restart the backend."
    return False


def fetch_history():
    try:
        resp = requests.get(f"{BACKEND_URL}/api/history", params={"limit": 10}, timeout=10)
    except requests.exceptions.ConnectionError:
        return None, "Backend not running yet."
    if resp.status_code != 200:
        return None, "History unavailable."
    return resp.json(), ""


left, right = st.columns([0.92, 1.08], gap="large")

with left:
    with st.container(border=True):
        render_panel_header("1", "Email details", "Choose a template, then adjust the fields for the exact message you need.")
        st.markdown(
            """
            <div class="hint-row">
                <span class="hint-pill">Purpose</span>
                <span class="hint-pill">Recipient</span>
                <span class="hint-pill">Key points</span>
                <span class="hint-pill">Tone</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.selectbox(
            "Quick-start template",
            list(TEMPLATES.keys()),
            key="template_choice",
            on_change=apply_template,
        )

        st.text_input("Email purpose", key="purpose", placeholder="Interview scheduling, offer follow-up, client update")

        c1, c2 = st.columns(2)
        with c1:
            st.text_input("Recipient name", key="recipient_name", placeholder="Rahul Sharma")
        with c2:
            st.text_input("Designation", key="designation", placeholder="Senior Developer")

        st.text_input("Sender name", key="sender_name", placeholder="Priya Menon")

        st.text_area(
            "Key points to include",
            key="key_points",
            placeholder="Monday interview at 11 AM, Teams link to follow, confirm availability by Friday",
            height=120,
        )
        kp_len = len(st.session_state.key_points)
        counter_class = "char-counter"
        if kp_len > 400:
            counter_class += " over"
        elif kp_len > 300:
            counter_class += " warn"
        st.markdown(f'<div class="{counter_class}">{kp_len} / 500 characters</div>', unsafe_allow_html=True)

        tone_col, length_col = st.columns(2)
        with tone_col:
            st.selectbox("Tone", ["Professional", "Friendly", "Formal", "Assertive"], key="tone")
        with length_col:
            st.selectbox("Length", ["Concise", "Standard", "Detailed"], key="length")

        generate_col, reset_col = st.columns([3, 1])
        with generate_col:
            generate_clicked = st.button("Generate Email", type="primary", use_container_width=True)
        with reset_col:
            st.button("Reset", on_click=clear_form, use_container_width=True)

    if generate_clicked:
        if not st.session_state.key_points.strip():
            st.warning("Add at least one key point so the email says something specific.")
        else:
            with st.spinner("Writing your email..."):
                result = call_backend(
                    "/api/generate",
                    {
                        "purpose": st.session_state.purpose,
                        "recipient_name": st.session_state.recipient_name,
                        "designation": st.session_state.designation,
                        "key_points": st.session_state.key_points,
                        "tone": st.session_state.tone,
                        "length": st.session_state.length,
                    },
                )
            if result:
                if st.session_state.sender_name.strip():
                    result["body"] = result["body"].replace("[Your Name]", st.session_state.sender_name.strip())
                st.session_state.current_email = result
                st.session_state.selected_history_id = result.get("id")
                st.toast("Email generated")
                st.rerun()

with right:
    with st.container(border=True):
        render_panel_header("2", "Draft preview", "Review, copy, or refine the generated email.")

        if st.session_state.current_email:
            email = st.session_state.current_email
            st.markdown(
                """
                <div class="preview-topline">
                    <div class="hint-pill">Generated email</div>
                    <div class="preview-status">Ready to review</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            render_email_native(email["subject"], email["body"])
            copy_email_button(email["subject"], email["body"])

            st.divider()
            refine_instruction = st.text_input(
                "Refinement instruction",
                placeholder="Make it shorter, sound friendlier, add urgency, or include a deadline",
                key="refine_instruction",
            )
            if st.button("Regenerate & Refine", use_container_width=True):
                if not refine_instruction.strip():
                    st.warning("Type what you want changed, for example: make it shorter.")
                else:
                    with st.spinner("Refining your draft..."):
                        result = call_backend(
                            "/api/refine",
                            {"email_id": email["id"], "refinement_instruction": refine_instruction},
                        )
                    if result:
                        if st.session_state.sender_name.strip():
                            result["body"] = result["body"].replace("[Your Name]", st.session_state.sender_name.strip())
                        st.session_state.current_email = result
                        st.session_state.selected_history_id = result.get("id")
                        st.toast("Email refined")
                        st.rerun()
        else:
            st.markdown(
                """
                <div class="empty-state">
                    <h4>Your email will appear here</h4>
                    <p>Start with a template or type your own purpose and key points.</p>
                    <div class="empty-steps">
                        <div class="empty-step"><span>1</span><div>Fill in the message details.</div></div>
                        <div class="empty-step"><span>2</span><div>Generate a draft.</div></div>
                        <div class="empty-step"><span>3</span><div>Open older drafts from Recent Drafts.</div></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

with st.sidebar:
    st.markdown("### Recent Drafts")
    st.caption("Click a draft to reopen it in the preview panel.")

    if st.session_state.history_error:
        st.warning(st.session_state.history_error)

    history_items, history_error = fetch_history()
    if history_error:
        st.caption(history_error)
    elif not history_items:
        st.caption("No drafts yet. Generated emails will appear here.")
    else:
        for item in history_items:
            subject = item.get("subject") or item.get("purpose") or "Untitled draft"
            purpose = item.get("purpose") or "General"
            recipient = item.get("recipient_name") or "No recipient"
            created_at = (item.get("created_at") or "")[:16].replace("T", " ")
            label = subject[:48] + ("..." if len(subject) > 48 else "")
            help_text = f"{purpose} | {recipient}\n{created_at}"

            if st.button(label, key=f"history_{item['id']}", use_container_width=True, help=help_text):
                if load_history_email(item["id"]):
                    st.rerun()