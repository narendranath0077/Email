# AI Email Generator

A polished AI-powered email assistant for creating recruiter-ready outreach messages. The app generates, previews, copies, and refines email drafts through a lightweight frontend and a FastAPI backend powered by Groq and LangGraph.

## Features

- Generate emails from a purpose, recipient, tone, length, and key points
- Preview the result in an email-style layout before copying it
- Refine an existing draft with a plain-language instruction
- Store generated emails locally in SQLite for lightweight history tracking
- Deploy the frontend and API together through Vercel

## Tech stack

- Frontend: static HTML, CSS, and JavaScript
- Backend: FastAPI, Pydantic, SQLAlchemy
- AI orchestration: LangChain and LangGraph with Groq
- Deployment: Vercel-compatible Python entrypoint and static frontend routing

## Local development

1. Create and activate a Python virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with at least:
   ```env
   GROQ_API_KEY=your_groq_api_key
   ```
4. Start the backend:
   ```bash
   uvicorn backend.main:app --reload --host 127.0.0.1 --port 8002
   ```
5. Serve the frontend from the `frontend` directory:
   ```bash
   cd frontend
   python -m http.server 8001
   ```
6. Open http://127.0.0.1:8001/ in your browser.

## Environment variables

- `GROQ_API_KEY`: required for AI email generation
- `GROQ_MODEL`: optional override for the Groq model
- `DATABASE_URL`: optional database location; defaults to a local SQLite file
- `ALLOWED_ORIGINS`: optional comma-separated list of allowed frontend origins
- `RATE_LIMIT`: optional request rate limit for the API

## Deployment

The repository includes Vercel configuration in `vercel.json` and a Python entrypoint in `api/index.py` so the frontend and API can be served from a single deployment.

When deploying, configure the same environment variables above in the Vercel project settings.
