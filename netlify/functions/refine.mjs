import {
  buildRefinePrompt,
  generateEmail,
  handleOptions,
  jsonResponse,
  nextId,
  readJson,
  validateRefine,
} from "./_shared/email.mjs";

export async function handler(event) {
  if (event.httpMethod === "OPTIONS") {
    return handleOptions();
  }

  if (event.httpMethod !== "POST") {
    return jsonResponse({ detail: "Method not allowed." }, 405);
  }

  try {
    const payload = await readJson(event.body);
    const error = validateRefine(payload);
    if (error) {
      return jsonResponse({ detail: error }, 400);
    }

    const email = await generateEmail(buildRefinePrompt(payload));
    return jsonResponse({ id: nextId(), ...email });
  } catch (error) {
    return jsonResponse({ detail: error.message || "Something went wrong." }, 500);
  }
}
