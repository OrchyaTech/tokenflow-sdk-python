# Desktop and IDE compatibility gate

This Python SDK is **not** a drop-in proxy for a desktop application's bundled subscription or native model selector. TokenFlow cannot reroute traffic it does not receive.

An IDE or desktop tool can use this hosted endpoint only if it lets you:

1. Configure a custom OpenAI-compatible base URL ending in `/v1`.
2. Supply a TokenFlow tenant key **and** a separate provider BYOK key as distinct headers.
3. Send the supported single-turn text shape (one optional system and one user message), without required history, tool calls, images, audio, or framework-specific fields.
4. Choose a supported model that the supplied provider key can access.

If any condition fails, do not advertise the tool as supported. Many coding assistants send long histories and tool calls; merely changing a base URL is insufficient. A desktop app's own token counter may include local/tool tokens not present in gateway usage. TokenFlow can measure only calls it handles and provider usage returned on those calls.

For a bounded compatibility smoke test, use a throwaway prompt and restricted key, check HTTP status, actual routed model, response text, and usage. Then exercise the tool's real multi-turn and tool workflow: if it sends unsupported content, mark that workflow incompatible. Do not promise uninterrupted in-flight switching or zero 429s.
