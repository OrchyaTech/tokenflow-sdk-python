# TokenFlow Python SDK (local draft)

This is an **unpublished MIT-licensed review draft** for TokenFlow's current hosted BYOK text endpoint. Do not upload it to a public repository or package registry until the owner approves publication. It contains no gateway implementation or patent formulas.

TokenFlow accepts a TokenFlow tenant key and **your own provider key** separately. This client supports a bounded single-turn text call (one optional system message and one user message) and a text stream. It does not claim native compatibility with every IDE, desktop app, model, agent framework, or provider protocol.

## Local installation

From this directory, in a Python 3.10+ virtual environment:

```sh
python -m pip install -e .
```

Set your secrets in the local process environment, not in source control. This PowerShell example hides keystrokes; the plaintext still exists in the process environment while the example runs:

```powershell
function Set-SecretEnv([string]$Name) {
    $secure = Read-Host $Name -AsSecureString
    $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        [Environment]::SetEnvironmentVariable($Name, [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer), 'Process')
    } finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
        $secure.Dispose()
    }
}
Set-SecretEnv 'TOKENFLOW_API_KEY'
Set-SecretEnv 'OPENAI_API_KEY'
python examples\single_turn.py
Remove-Item Env:TOKENFLOW_API_KEY, Env:OPENAI_API_KEY
```

The keys are sent over HTTPS to TokenFlow as `Authorization: Bearer ...` and `X-Provider-Key`, respectively. TokenFlow receives the prompt and provider credential in order to forward this call; BYOK does **not** mean the gateway cannot see them in transit. Use a restricted provider key and review your provider's terms and limits. Do not expose either key in browser JavaScript, logs, screenshots, or a public repository.

## Python

```python
import os
from orchya_tokenflow import TokenFlowClient

with TokenFlowClient(os.environ["TOKENFLOW_API_KEY"], os.environ["OPENAI_API_KEY"]) as client:
    reply = client.complete("Reply with one short greeting.", model="gpt-4o-mini")
    print(reply.text)
    print(reply.usage)
    print(reply.routed_model, reply.provider, reply.engine)
```

The model must be available for the provider key supplied. `tokenflow-auto` uses routing within the identified provider; for ambiguous OpenAI-style `sk-` keys, set `provider_primary="openai"` explicitly. No model switch guarantees identical answers, latency, or price. Secondary-provider failover requires an explicitly named provider and its own key; only use it after the customer consents to sending prompts to that provider. There is no claim of in-flight reasoning-loop continuation.

The SDK has **no automatic retries**. Catch `TokenFlowAPIError` and inspect `status_code`, `code`, and `retry_after`. A retry can duplicate a request if an upstream response was lost. `stream()` yields raw SSE JSON events; if the stream ends before `[DONE]`, it raises `TokenFlowTransportError` and does not silently resume. These exceptions never include prompt or upstream error text.

## Setup by tool

| Tool or workflow | Current guidance |
| --- | --- |
| Python backend, script, or service | Use this SDK for supported single-turn text. |
| cURL, Node.js, no-code HTTP step | Use the [raw HTTP recipe](docs/RAW_HTTP.md) from a trusted server-side environment. A [Node.js example](examples/node_http.mjs) is included; it is not a separate Node SDK. |
| Agent or multi-agent orchestration | Use a [one-shot adapter](docs/AGENTS.md) for individual steps; keep memory, tools, and retries in your own application. Do not assume framework-native agent support. |
| IDE or desktop AI chat | [Check compatibility first](docs/DESKTOP_IDE.md). Full multi-turn, tool-calling, or native subscription-based workflows are not supported by this SDK. |

The gateway's supported-model list and API contract may change. Test your actual tool's request shape before advertising compatibility. The SDK does not intercept network packets or third-party desktop traffic.

## Development

```sh
python -m pip install -e '.[test]'
python -m pytest -q
```

Tests use a mock transport and do not require live provider keys. A live probe should be separately authorized, budgeted, and run with throwaway prompts and restricted credentials.

Security reports: [support@orchya.co.uk](mailto:support@orchya.co.uk). Do not include keys or private prompts in a report.
