import json

import httpx
import pytest

from orchya_tokenflow import TokenFlowAPIError, TokenFlowClient, TokenFlowTransportError


def client(handler, **kwargs):
    return TokenFlowClient(
        "tf_test_secret", "provider_test_secret",
        transport=httpx.MockTransport(handler), **kwargs,
    )


def test_complete_sends_two_keys_separately_and_reads_receipt():
    def handler(request):
        assert request.url == "https://tokenflow.orchya.co.uk/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer tf_test_secret"
        assert request.headers["X-Provider-Key"] == "provider_test_secret"
        body = json.loads(request.content)
        assert body == {
            "model": "gpt-4o-mini", "messages": [
                {"role": "system", "content": "Be brief"},
                {"role": "user", "content": "Hello"},
            ], "stream": False, "max_tokens": 16,
        }
        return httpx.Response(200, json={
            "choices": [{"message": {"content": "Hi"}}],
            "usage": {"total_tokens": 8},
        }, headers={"X-TokenFlow-Routed-Model": "gpt-4o-mini",
                    "X-TokenFlow-Cluster": "openai", "X-TokenFlow-Engine": "live"})

    with client(handler) as sdk:
        result = sdk.complete("Hello", model="gpt-4o-mini", system="Be brief", max_tokens=16)
    assert result.text == "Hi"
    assert result.usage == {"total_tokens": 8}
    assert (result.routed_model, result.provider, result.engine) == ("gpt-4o-mini", "openai", "live")


def test_secondary_requires_explicit_pair_and_never_substitutes_keys():
    def handler(request):
        assert request.headers["X-Provider-Primary"] == "openai"
        assert request.headers["X-Provider-Secondary"] == "anthropic"
        assert request.headers["X-Provider-Key-Secondary"] == "anthropic_test_secret"
        assert request.headers["X-Provider-Key"] == "provider_test_secret"
        return httpx.Response(200, json={"choices": []})

    with client(handler) as sdk:
        with pytest.raises(ValueError):
            sdk.complete("Hello", model="tokenflow-auto", secondary_provider="anthropic")
        sdk.complete("Hello", model="tokenflow-auto", provider_primary="openai",
                     secondary_provider="anthropic", secondary_provider_key="anthropic_test_secret")


@pytest.mark.parametrize("url", [
    "http://tokenflow.orchya.co.uk/v1", "https://user:pass@example.com/v1",
    "https://tokenflow.orchya.co.uk/v1?key=x", "https://tokenflow.orchya.co.uk/",
])
def test_rejects_unsafe_base_url(url):
    with pytest.raises(ValueError):
        TokenFlowClient("tf_test_secret", "provider_test_secret", base_url=url)


def test_error_redacts_body_and_credentials_but_preserves_retry_after():
    def handler(_request):
        return httpx.Response(429, json={"error": {
            "code": "rate_limited", "message": "provider_test_secret secret prompt"
        }}, headers={"Retry-After": "3"})

    with client(handler) as sdk, pytest.raises(TokenFlowAPIError) as exc:
        sdk.complete("secret prompt", model="gpt-4o-mini")
    assert (exc.value.status_code, exc.value.code, exc.value.retry_after) == (429, "rate_limited", "3")
    assert "secret" not in str(exc.value)
    assert "prompt" not in str(exc.value)


def test_redirect_not_followed_to_untrusted_host():
    calls = []

    def handler(request):
        calls.append(str(request.url))
        return httpx.Response(307, headers={"Location": "https://evil.example/collect"})

    with client(handler) as sdk, pytest.raises(TokenFlowAPIError) as exc:
        sdk.complete("Hello", model="gpt-4o-mini")
    assert exc.value.status_code == 307
    assert len(calls) == 1


def test_stream_yields_events_and_requires_done_marker():
    def handler(_request):
        return httpx.Response(200, text='data: {"choices":[{"delta":{"content":"Hi"}}]}\n\ndata: [DONE]\n\n')

    with client(handler) as sdk:
        events = list(sdk.stream("Hello", model="gpt-4o-mini"))
    assert events[0]["choices"][0]["delta"]["content"] == "Hi"


def test_truncated_stream_is_error_not_success():
    with client(lambda _request: httpx.Response(200, text='data: {"choices":[]}\n\n')) as sdk:
        with pytest.raises(TokenFlowTransportError):
            list(sdk.stream("Hello", model="gpt-4o-mini"))


def test_stream_error_is_redacted():
    def handler(_request):
        return httpx.Response(200, text='data: {"error":{"code":"upstream_error","message":"secret"}}\n\n')

    with client(handler) as sdk, pytest.raises(TokenFlowAPIError) as exc:
        list(sdk.stream("Hello", model="gpt-4o-mini"))
    assert exc.value.code == "upstream_error"
    assert "secret" not in str(exc.value)


def test_transport_error_does_not_expose_url_or_keys():
    def handler(_request):
        raise httpx.ConnectError("provider_test_secret")

    with client(handler) as sdk, pytest.raises(TokenFlowTransportError) as exc:
        sdk.complete("Hello", model="gpt-4o-mini")
    assert "provider_test_secret" not in str(exc.value)


def test_rejects_history_or_tool_messages_at_sdk_boundary():
    with client(lambda _request: pytest.fail("must not send")) as sdk:
        with pytest.raises(ValueError):
            sdk.complete([{"role": "user", "content": "Hello"}], model="gpt-4o-mini")
