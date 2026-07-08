"""
A small LangGraph state machine:

    validate -> build_prompt -> generate -> END

Kept to three nodes on purpose - the assignment's bar is prompt reliability,
not graph complexity. Structure earns its keep in one concrete way: generate
and refine share the exact same validation + parsing path instead of two
copies of it.
"""
import json
import logging
from typing import TypedDict, Optional

from langgraph.graph import StateGraph, END

from backend.llm_service import invoke_with_retry, LLMAuthError, LLMProviderError
from backend.prompts import SYSTEM_PROMPT, REPAIR_INSTRUCTION, build_generate_prompt, build_refine_prompt

logger = logging.getLogger("bss.graph")


class EmailState(TypedDict, total=False):
    mode: str  # "generate" | "refine"
    purpose: str
    recipient_name: str
    designation: str
    key_points: str
    tone: str
    length: str
    previous_subject: str
    previous_body: str
    refinement_instruction: str
    _prompt: str
    subject: str
    body: str
    error: Optional[str]


def validate_node(state: EmailState) -> EmailState:
    """All edge-case handling lives here, shared by both generate and refine."""
    if state.get("mode") == "refine":
        if not state.get("refinement_instruction", "").strip():
            state["error"] = "Tell me what to change - e.g. 'make it shorter' or 'add more urgency'."
        return state

    if not state.get("key_points", "").strip():
        state["error"] = "Add at least one key point so the email says something specific."
        return state

    # Soft defaults for genuinely optional fields - never block generation over these.
    state["purpose"] = state.get("purpose", "").strip() or "General Update"
    state["recipient_name"] = state.get("recipient_name", "").strip() or "there"
    state["tone"] = state.get("tone") or "Professional"
    state["length"] = state.get("length") or "Standard"
    return state


def build_prompt_node(state: EmailState) -> EmailState:
    if state.get("error"):
        return state
    if state.get("mode") == "refine":
        state["_prompt"] = build_refine_prompt(state)
    else:
        state["_prompt"] = build_generate_prompt(state)
    return state


def _extract_json(raw: str) -> str:
    """Strip markdown code fences if the model added them despite instructions."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    return text


def _parse_email_json(raw: str) -> tuple[Optional[str], Optional[str]]:
    try:
        parsed = json.loads(_extract_json(raw))
        subject = (parsed.get("subject") or "").strip()
        body = (parsed.get("body") or "").strip()
        if subject and body:
            return subject, body
    except (json.JSONDecodeError, AttributeError):
        pass
    return None, None


def generate_node(state: EmailState) -> EmailState:
    if state.get("error"):
        return state

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": state["_prompt"]},
    ]

    try:
        raw = invoke_with_retry(messages)
    except LLMAuthError as exc:
        state["error"] = str(exc)
        return state
    except LLMProviderError as exc:
        state["error"] = f"The AI service didn't respond in time - please try again. ({exc})"
        return state

    subject, body = _parse_email_json(raw)

    if subject is None:
        # Self-heal once: ask the model to fix its own malformed output before giving up.
        logger.warning("First response was not valid JSON, attempting one repair pass.")
        repair_messages = messages + [
            {"role": "assistant", "content": raw},
            {"role": "user", "content": REPAIR_INSTRUCTION.format(previous_raw=raw)},
        ]
        try:
            raw_repaired = invoke_with_retry(repair_messages, max_attempts=2)
            subject, body = _parse_email_json(raw_repaired)
            raw = raw_repaired  # keep the freshest text for the fallback path below
        except (LLMAuthError, LLMProviderError):
            subject, body = None, None

    if subject is None:
        # Still nothing usable - fail soft with the raw text rather than crash the request.
        logger.error("Model output could not be parsed as JSON after repair attempt.")
        state["subject"] = state.get("purpose", "Update") or "Update"
        state["body"] = raw
    else:
        state["subject"] = subject
        state["body"] = body

    return state


def build_graph():
    graph = StateGraph(EmailState)
    graph.add_node("validate", validate_node)
    graph.add_node("build_prompt", build_prompt_node)
    graph.add_node("generate", generate_node)

    graph.set_entry_point("validate")
    graph.add_edge("validate", "build_prompt")
    graph.add_edge("build_prompt", "generate")
    graph.add_edge("generate", END)

    return graph.compile()


email_graph = build_graph()
