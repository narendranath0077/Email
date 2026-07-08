# BSS AI Email Generator

A tool that turns a purpose, recipient, key points, and tone into a ready-to-send,
human-sounding email — built for the BSS AI Automation Intern assignment.

## Stack & why

- **Groq** (`llama-3.3-70b-versatile`) — chosen for very low latency, which matters
  here since the UI does live round-trips (generate, then refine) and a recruiter
  shouldn't be staring at a spinner.
- **FastAPI** — the API layer that owns prompt construction, calls Groq, and persists history.
- **LangChain + LangGraph** — `langchain-groq` for the model client; a small 3-node
  LangGraph (`validate -> build_prompt -> generate`) so generate and refine share one
  validation/parsing path instead of duplicating logic.
- **SQLite (SQLAlchemy)** — every draft and every refinement is logged, so refine
  requests can pull the previous draft by ID and a "Recent Drafts" sidebar is free.
- **Streamlit** — the recruiter-facing UI, glassmorphism theme.

> **Note on the brief's "browser-only, no local servers" constraint:** this stack runs
> a real backend process. To satisfy "share a working link," deploy the FastAPI app
> (Render/Railway/Fly.io) and the Streamlit app (Streamlit Community Cloud), then point
> `BACKEND_URL` / `ALLOWED_ORIGINS` at each other. Locally, both run with the commands below.

## Project structure

```
bss-email-generator/
├── backend/
│   ├── main.py           # FastAPI app, CORS, rate-limit handler, request logging
│   ├── config.py         # env-driven settings + logging setup, one place only
│   ├── database.py       # SQLAlchemy engine/session
│   ├── models.py         # EmailLog table
│   ├── schemas.py        # Pydantic request/response models
│   ├── prompts.py        # system prompt + tone/length guides + repair prompt
│   ├── llm_service.py    # Groq call with retry/backoff + auth-error classification
│   ├── graph.py          # LangGraph: validate -> build_prompt -> generate (+ JSON self-repair)
│   └── routers/email.py  # POST /api/generate, POST /api/refine, GET /api/history (rate-limited)
├── frontend/app.py        # Streamlit UI (glassmorphism theme)
├── tests/                 # 40 automated tests - see "Testing" below
├── data/                   # emails.db lives here (gitignored)
├── requirements.txt
├── pytest.ini
└── .env.example
```

## Running locally

```bash
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # then add your GROQ_API_KEY (free at console.groq.com/keys)

# terminal 1
uvicorn backend.main:app --reload

# terminal 2
streamlit run frontend/app.py
```

Open the Streamlit URL it prints (usually `http://localhost:8501`).

## Testing

40 automated tests, all passing, no network calls to Groq required (the LLM call is
mocked at the boundary so tests are fast and deterministic):

```bash
pip install pytest httpx
pytest -v
```

Coverage:
- `tests/test_graph_logic.py` — edge-case validation (empty key points, missing
  recipient/purpose/tone/length, refine without an instruction) and prompt building
- `tests/test_generate_node.py` — JSON parsing, markdown-fence stripping, the
  self-repair pass on malformed output, and graceful fallback if repair also fails
- `tests/test_llm_service.py` — retry/backoff behavior, auth errors failing fast
  instead of retrying, and provider errors after exhausting retries
- `tests/test_api.py` — full FastAPI request/response cycle against a throwaway
  sqlite db: generate, refine, history, 400/404/422 paths, root/health checks

Beyond the automated suite, this was also verified with the real process running:
a live `uvicorn` server was booted and hit over an actual socket with `curl`
(generate/refine/history/error paths), and the Streamlit script was run headlessly
via Streamlit's `AppTest` framework to click through template-select → generate →
refine against that live server. The only thing mocked anywhere is the network call
to Groq itself (not reachable from this build environment) — everything else in the
stack is exercised for real.

## How the prompt engineering works (`backend/prompts.py`)

- One system prompt sets the persona ("you ARE the person writing it, not an AI
  describing an email") and hard rules: no generic openers, no placeholder-stuffing
  when real details exist, one reasonable assumption instead of a clarifying question
  when input is vague, strict JSON-only output.
- A worked example is embedded directly in the system prompt showing the exact input
  → output shape expected, since models follow a concrete example far more reliably
  than a prose description of a format.
- Tone and length are each expanded into a short natural-language guide
  (`TONE_GUIDE`, `LENGTH_GUIDE`) and injected into the user message per-request, so
  "Concise" and "Detailed" produce genuinely different line counts rather than the
  same email with a label.
- Refinement reuses the same system prompt but sends the previous subject/body plus
  the instruction, explicitly told to make a *real* change, not a cosmetic reword.
- **Self-repair**: if the model's JSON doesn't parse, `graph.py` sends the exact bad
  output back with `REPAIR_INSTRUCTION` and asks for a corrected reply before falling
  back to a raw-text response - one extra round trip buys a lot of reliability.

## Reliability & ops (`backend/llm_service.py`, `backend/main.py`)

- **Retry with backoff**: transient Groq failures retry up to 3x with exponential
  backoff (1s, 2s, 4s). Auth errors (bad/missing API key) fail immediately instead of
  wasting retries on something that will never succeed.
- **Rate limiting**: `/api/generate` and `/api/refine` are capped per-IP (`RATE_LIMIT`
  in `.env`, default 15/minute) via `slowapi`, since these are the two endpoints that
  cost money to call.
- **Structured logging**: every request gets a short request ID, logged with method,
  path, status, and duration; unhandled exceptions are caught and logged with a full
  traceback instead of leaking a raw 500 to the user.
- **Restricted CORS**: origins are read from `ALLOWED_ORIGINS`, not left as `*`.

## Edge cases handled

- **Empty key points**: blocked client-side with a warning, and server-side returns
  a 400 with a friendly message — never sent to the model with nothing to say.
- **Missing recipient name**: defaults to "there" so the email still reads naturally.
- **Missing/vague purpose**: defaults to "General Update" and the model is instructed
  to make one sensible assumption rather than stall.
- **Model returns malformed JSON**: one self-repair round trip is attempted; if that
  also fails, `graph.py` falls back to using the purpose as the subject and the raw
  text as the body, rather than crashing the request.
- **Refine on a stale/unknown ID**: returns a 404 with a clear message instead of a
  generic 500.
- **Backend unreachable from the UI**: Streamlit shows a specific "can't reach the
  backend" message rather than a raw connection traceback.
- **Rate limit hit**: Streamlit shows "you're generating a bit fast" instead of a
  raw 429.

## Known limitations

- Refinement chains off the last saved draft by `email_id`; if two tabs are open
  against the same session this can get out of sync — fine for a single-recruiter
  demo, would need a proper session/user concept for multi-user use.
- No auth — anyone with the link can generate/refine. Rate limiting caps abuse but
  doesn't replace real authentication; flagging it as the first thing I'd add.
- Rate limiting is in-memory (per-process) via slowapi - fine for a single instance,
  would need a shared backend (Redis) behind a load balancer.

## Ideas for later (not yet built)

- Export draft history to `.eml`/plain text.
- Per-recruiter saved "voice" preferences.
- Redis-backed rate limiting for multi-instance deployment.

