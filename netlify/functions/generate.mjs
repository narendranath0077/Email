import {
  buildGeneratePrompt,
  generateEmail,
  handleOptions,
  jsonResponse,
  nextId,
  readJson,
  validateGenerate,
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
    const error = validateGenerate(payload);
    if (error) {
      return jsonResponse({ detail: error }, 400);
    }

    const email = await generateEmail(buildGeneratePrompt(payload));
    return jsonResponse({ id: nextId(), ...email });
  } catch (error) {
    return jsonResponse({ detail: error.message || "Something went wrong." }, 500);
  }
}
