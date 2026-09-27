# Publication gate

This directory is a local draft, not a public release.

Before copying it into `OrchyaTech/tokenflow-sdk-python`:

1. **Done:** owner chose MIT for the SDK client and Orchya Tech Limited as its copyright holder; `LICENSE` and package metadata record that decision. This does not state who owns any separate patent. Publication still requires the later gates below. Do not reuse the old `tokenflow-python` repository or its Git history; its remote URL previously held a credential. Rotate that credential before further repository work.
2. Obtain access to the private target repository through normal GitHub authentication. Do not paste a personal access token into a remote URL, terminal command, file, issue, or chat.
3. Review the exact source, examples and wheel for secrets, customer data, patent internals and unsupported claims. Verify the target repository contains no private gateway code, test databases or internal reports.
4. Run the mock test suite and package build on the exact publication candidate. Run a separately authorized, low-cost live smoke test for each provider/model being documented. Do not infer reliability or savings from one success.
5. Have a reviewer sign off on the exact commit. Only then push to the private target and, if the owner approves, change visibility or publish a package. Registering a similarly named package on PyPI is separate and is **not** done by this draft.

Supported today in this draft: a synchronous Python client for one supported text call and a text SSE stream; raw HTTP instructions for server-side integrations. Full desktop, IDE, multi-turn agent, tool-call, multimodal, native Anthropic/Gemini protocol and JavaScript SDK support are **not** claimed.
