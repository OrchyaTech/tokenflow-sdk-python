# Raw HTTP integration

Use a server-side HTTP step that can set **both** credential headers. Do not paste keys into browser code, a shared workflow export, or a URL/query parameter.

```http
POST https://tokenflow.orchya.co.uk/v1/chat/completions
Authorization: Bearer <TOKENFLOW_TENANT_KEY>
X-Provider-Key: <YOUR_PROVIDER_KEY>
Content-Type: application/json

{"model":"gpt-4o-mini","messages":[{"role":"user","content":"Reply with one greeting."}],"stream":false}
```

Supported request shape for this draft: one user text message, optionally preceded by one system text message. Choose a model your provider key can access. For `tokenflow-auto` with an ambiguous OpenAI-style key, add `X-Provider-Primary: openai` when that is the actual provider. Never guess a provider from the `sk-` prefix alone.

For Make, Zapier, n8n, Flowise, or similar tools, use a generic HTTP request node **only if** it can protect both keys as secrets and send the exact request. A built-in OpenAI node may not pass the TokenFlow key or may send unsupported history/tool fields. Test the node and inspect only redacted logs before publishing a setup recipe. Do not interpret a 200 from a different tool as proof of compatibility.

A `429` can still occur. Respect `Retry-After`, bound retries, and account for possible duplicate requests. A successful response's `usage` and `X-TokenFlow-Routed-Model` describe that call; neither proves a percentage cost or token saving versus a direct call.
