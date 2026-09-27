# Agent and multi-agent integration

Treat TokenFlow as a **single inference step** in your orchestrator, not as the orchestrator itself. The application owns conversation memory, tool execution, authorization, and consent.

At each supported step: construct one bounded text prompt, choose a model and provider key, call `TokenFlowClient.complete`, validate the returned text, then persist your own state. Never let model-generated text choose credential headers, change provider consent, or trigger a call without your policy checks. Do not send a raw multi-turn message array or tool schema to this SDK.

For secondary-provider failover, specify the provider name and its matching key explicitly after gaining customer consent. The gateway may retry or move a request only within its supported boundary; it cannot transplant an in-progress reasoning state into another model. A partially delivered stream must be treated as failed, reconciled by your application, and not presented as a complete answer.

Record per-call status, model, provider, latency, and usage **without prompt text or keys**. Use a bounded test set to compare outcomes with direct provider calls. Do not publish savings, carbon, or reliability percentages from an unpaired anecdotal probe.
