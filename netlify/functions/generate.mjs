import {
  buildGeneratePrompt,
  generateEmail,
  handleOptions,
  jsonResponse,
  nextId,
  readJson,
  validateGenerate,
} from "./_shared/email.mjs";

export default async (req, context) => {
  if (req.method === "OPTIONS") {
    return handleOptions();
  }

  if (req.method !== "POST") {
    return jsonResponse({ detail: "Method not allowed." }, 405);
  }

  try {
    const payload = await readJson(req);
    const error = validateGenerate(payload);
    if (error) {
      return jsonResponse({ detail: error }, 400);
    }

    const email = await generateEmail(buildGeneratePrompt(payload), context.env);
    return jsonResponse({ id: nextId(), ...email });
  } catch (error) {
    return jsonResponse({ detail: error.message || "Something went wrong." }, 500);
  }
};

export const config = {
  path: "/api/generate",
};
