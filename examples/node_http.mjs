// Server-side Node.js 18+ example. Never run this with keys in browser code.
const tokenflowKey = process.env.TOKENFLOW_API_KEY;
const providerKey = process.env.OPENAI_API_KEY;
if (!tokenflowKey || !providerKey) {
  throw new Error("Set TOKENFLOW_API_KEY and OPENAI_API_KEY in the process environment");
}

const response = await fetch("https://tokenflow.orchya.co.uk/v1/chat/completions", {
  method: "POST",
  redirect: "error",
  headers: {
    Authorization: `Bearer ${tokenflowKey}`,
    "X-Provider-Key": providerKey,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    model: "gpt-4o-mini",
    messages: [{ role: "user", content: "Reply with one short greeting." }],
    stream: false,
  }),
});
if (!response.ok) {
  throw new Error(`TokenFlow returned HTTP ${response.status}`);
}
const result = await response.json();
console.log(result.choices?.[0]?.message?.content ?? "");
console.log("model:", response.headers.get("X-TokenFlow-Routed-Model"), "usage:", result.usage);
