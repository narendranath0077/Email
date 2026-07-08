# BSS AI Email Generator

A polished AI-powered email assistant for creating recruiter-ready outreach messages. The repo keeps the existing FastAPI backend for local development, and now also includes Netlify-native serverless functions so the app can be deployed on Netlify as a single project.

## Features

- Generate emails from a purpose, recipient, tone, length, and key points
- Preview the result in an email-style layout before copying it
- Refine an existing draft with a plain-language instruction
- Run locally with FastAPI, or deploy the frontend plus API on Netlify

## Project layout

- `bss-email-generator/frontend`: static UI served locally or by Netlify
- `bss-email-generator/backend`: existing FastAPI backend for local development
- `netlify/functions`: Netlify serverless API endpoints for deployed use
- `netlify.toml`: Netlify publish directory and routing config

## Local development

1. Create and activate a Python virtual environment.
2. Install dependencies:
   ```bash
   pip install -r bss-email-generator/requirements.txt
   ```
3. Create `bss-email-generator/.env` with at least:
   ```env
   GROQ_API_KEY=your_groq_api_key
   ```
4. Start the backend:
   ```bash
   uvicorn backend.main:app --reload --host 127.0.0.1 --port 8002
   ```
   Run this from the `bss-email-generator` directory.
5. Serve the frontend:
   ```bash
   cd frontend
   python -m http.server 8001
   ```
6. Open `http://127.0.0.1:8001/`.

## Netlify deployment

1. Push this repo to GitHub.
2. In Netlify, create a new site from that repo.
3. Keep the base directory empty so Netlify uses the repo root.
4. Netlify will pick up `netlify.toml` and use:
   - publish directory: `bss-email-generator/frontend`
   - functions directory: `netlify/functions`
5. Add these environment variables in Netlify:
   - `GROQ_API_KEY` required
   - `GROQ_MODEL` optional
6. Deploy.

After deploy:

- `/` serves the frontend
- `/api/generate` runs the Netlify function
- `/api/refine` runs the Netlify function

## Important note

The Netlify deployment path does not use the FastAPI SQLite history flow. Refinement on Netlify works from the current email content in the browser, which is enough for the shipped UI. If you want persistent history, keep using the Python backend locally or move storage to a hosted database.
