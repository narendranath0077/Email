const SYSTEM_PROMPT = `You are a sharp, experienced recruiting coordinator at a staffing firm,
writing an email on behalf of a colleague. You are NOT an AI assistant describing an email -
you ARE the person writing it.

Non-negotiable rules:
1. Sound like a specific human wrote this for a specific situation, never like a mail-merge
template. Use the exact details given (names, dates, times, tools mentioned) - never
substitute generic placeholders like "[Date]" or "[Company]" unless that information was
truly never provided.
2. Never open with tired filler like "I hope this email finds you well." Vary your openings
naturally based on the purpose of the email.
3. Every sentence must earn its place. Do not repeat the same point in different words to
sound "complete." Padding is worse than brevity.
4. If the input is vague (e.g. a one-word purpose, or key points that are just a fragment),
make one reasonable, professional assumption to fill the gap rather than asking a
clarifying question back - the recruiter needs a usable draft right now, not a
conversation. Do not flag the assumption inside the email itself.
5. Match the requested tone and length exactly (guides are provided in the user message).
Length is a hard constraint, not a suggestion.
6. Always end with a sign-off appropriate to the tone, and a placeholder name only if no
sender name was given (use "[Your Name]" only in that one spot, never elsewhere).
7. Never use markdown - no **bold**, no bullet symbols, no headers. Plain email prose only.

OUTPUT FORMAT - read this twice, it is checked programmatically:
- Respond with ONE JSON object and NOTHING else: no markdown fences, no "Here is the email:",
  no trailing commentary, no explanation of your reasoning.
- The JSON object has EXACTLY two keys: "subject" and "body". Both are plain strings.
- Inside "body", use a literal \\n\\n between paragraphs (a real newline escape inside the
  JSON string, not the word "newline"). Do not add \\n after every sentence - only between
  actual paragraph breaks.
- The first character of your reply must be { and the last character must be }.`;

const REPAIR_INSTRUCTION = `Your previous reply could not be parsed as JSON.
Resend your answer. Output ONLY a single JSON object shaped exactly like
{"subject": "...", "body": "..."} - no markdown fences, no commentary.`;

const TONE_GUIDE = {
  Professional: "Polished and businesslike, but still warm - like a competent colleague, not a legal notice.",
  Friendly: "Warm and personable, first-name energy, light conversational touches - still competent, never sloppy.",
  Formal: "Reserved and precise, minimal contractions, appropriate for a first contact with a senior client or executive.",
  Assertive: "Direct and confident, clear on what is needed and by when, without being rude or demanding - firm, not aggressive.",
};

const LENGTH_GUIDE = {
  Concise: "3-4 lines total INCLUDING greeting and sign-off. Only the one or two facts that matter. No throat-clearing.",
  Standard: "5-8 lines. A short greeting, the key points in 1-2 short paragraphs, a clear closing line, sign-off.",
  Detailed: "9-14 lines. Full context, all key points given, but still tightly written - detailed does not mean padded.",
};

function jsonResponse(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json",
      "access-control-allow-origin": "*",
      "access-control-allow-headers": "content-type",
      "access-control-allow-methods": "POST, OPTIONS",
    },
  });
}

export function handleOptions() {
  return new Response(null, {
    status: 204,
    headers: {
      "access-control-allow-origin": "*",
      "access-control-allow-headers": "content-type",
      "access-control-allow-methods": "POST, OPTIONS",
    },
  });
}

export async function readJson(req) {
  try {
    return await req.json();
  } catch {
    throw new Error("Please send valid JSON in the request body.");
  }
}

export function validateGenerate(payload) {
  if (!String(payload?.key_points ?? "").trim()) {
    return "Add at least one key point so the email says something specific.";
  }
  return null;
}

export function validateRefine(payload) {
  if (!String(payload?.refinement_instruction ?? "").trim()) {
    return "Tell me what to change - e.g. 'make it shorter' or 'add more urgency'.";
  }
  if (!String(payload?.current_body ?? "").trim()) {
    return "Generate an email first so there is something to refine.";
  }
  return null;
}

export function buildGeneratePrompt(payload) {
  const designationPart = payload.designation ? `, ${payload.designation}` : "";
  const tone = payload.tone || "Professional";
  const length = payload.length || "Standard";
  return `Write a professional email.

Purpose: ${payload.purpose || "General Update"}
Recipient: ${payload.recipient_name || "there"}${designationPart}
Key points to include: ${payload.key_points}
Tone: ${tone} - ${TONE_GUIDE[tone] || ""}
Length: ${length} - ${LENGTH_GUIDE[length] || ""}

Respond ONLY as JSON: {"subject": "...", "body": "..."}`;
}

export function buildRefinePrompt(payload) {
  return `Here is an email that was previously generated:

SUBJECT: ${payload.current_subject || "Update"}
BODY:
${payload.current_body}

The user wants it refined with this instruction: "${payload.refinement_instruction}"

Rewrite the subject and body so the instruction is genuinely reflected in the result - if asked
to shorten, actually cut length; if asked to add urgency, actually tighten pacing and raise
stakes; do not just return a superficial rewording of the same draft.

Keep the original tone (${payload.tone || "Professional"}) and overall length category
(${payload.length || "Standard"}) unless the instruction explicitly asks to change either.

Respond ONLY as JSON: {"subject": "...", "body": "..."}`;
}

function extractJson(raw) {
  const text = String(raw || "").trim();
  if (!text.startsWith("```")) {
    return text;
  }

  const stripped = text.replace(/^```(?:json)?/i, "").replace(/```$/, "").trim();
  return stripped;
}

function parseEmail(raw) {
  try {
    const parsed = JSON.parse(extractJson(raw));
    const subject = String(parsed?.subject || "").trim();
    const body = String(parsed?.body || "").trim();
    if (subject && body) {
      return { subject, body };
    }
  } catch {
  }
  return null;
}

async function groqChat(messages, env) {
  const apiKey = env.get("GROQ_API_KEY");
  if (!apiKey) {
    throw new Error("GROQ_API_KEY is not set in Netlify environment variables.");
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 25000);

  try {
    const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      signal: controller.signal,
      headers: {
        authorization: `Bearer ${apiKey}`,
        "content-type": "application/json",
      },
      body: JSON.stringify({
        model: env.get("GROQ_MODEL") || "llama-3.3-70b-versatile",
        temperature: 0.7,
        messages,
      }),
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail = data?.error?.message || data?.message || "Groq request failed.";
      throw new Error(detail);
    }

    return String(data?.choices?.[0]?.message?.content || "").trim();
  } finally {
    clearTimeout(timeout);
  }
}

export async function generateEmail(prompt, env) {
  const messages = [
    { role: "system", content: SYSTEM_PROMPT },
    { role: "user", content: prompt },
  ];

  let raw = await groqChat(messages, env);
  let parsed = parseEmail(raw);

  if (!parsed) {
    raw = await groqChat(
      [
        ...messages,
        { role: "assistant", content: raw },
        { role: "user", content: REPAIR_INSTRUCTION },
      ],
      env,
    );
    parsed = parseEmail(raw);
  }

  if (!parsed) {
    return {
      subject: "Update",
      body: raw || "The AI service returned an empty response.",
    };
  }

  return parsed;
}

export function nextId() {
  return Date.now();
}

export { jsonResponse };
