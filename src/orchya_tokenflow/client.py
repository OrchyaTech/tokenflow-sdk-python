"""Minimal synchronous client; no automatic retries or provider-key persistence."""

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterator, Optional
from urllib.parse import urlsplit

import httpx

from .errors import TokenFlowAPIError, TokenFlowTransportError

DEFAULT_BASE_URL = "https://tokenflow.orchya.co.uk/v1"
_SAFE_CODE = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")


@dataclass(frozen=True)
class Completion:
    data: Dict[str, Any]
    routed_model: Optional[str]
    provider: Optional[str]
    engine: Optional[str]

    @property
    def usage(self) -> Dict[str, Any]:
        value = self.data.get("usage")
        return value if isinstance(value, dict) else {}

    @property
    def text(self) -> str:
        choices = self.data.get("choices")
        if not isinstance(choices, list) or not choices:
            return ""
        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        return content if isinstance(content, str) else ""


class TokenFlowClient:
    """Send supported single-turn text calls with two separate credentials.

    The client keeps keys in memory for its lifetime; it does not write them to
    disk, print them, or place the provider key in Authorization. Close it when
    finished, or use it as a context manager.
    """

    def __init__(
        self,
        tokenflow_key: str,
        provider_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        transport: Optional[httpx.BaseTransport] = None,
    ):
        if not tokenflow_key or not tokenflow_key.strip():
            raise ValueError("tokenflow_key is required")
        if not provider_key or not provider_key.strip():
            raise ValueError("provider_key is required")
        parsed = urlsplit(base_url)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username
                or parsed.password or parsed.query or parsed.fragment or parsed.path.rstrip("/") != "/v1"):
            raise ValueError("base_url must be an HTTPS TokenFlow /v1 endpoint")
        self._tokenflow_key = tokenflow_key.strip()
        self._provider_key = provider_key.strip()
        self._http = httpx.Client(base_url=base_url.rstrip("/") + "/", timeout=timeout,
                                  follow_redirects=False, transport=transport)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "TokenFlowClient":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def _headers(
        self,
        provider_primary: Optional[str],
        secondary_provider: Optional[str],
        secondary_provider_key: Optional[str],
    ) -> Dict[str, str]:
        if bool(secondary_provider) != bool(secondary_provider_key):
            raise ValueError("secondary_provider and secondary_provider_key must be supplied together")
        headers = {
            "Authorization": f"Bearer {self._tokenflow_key}",
            "X-Provider-Key": self._provider_key,
        }
        if provider_primary:
            headers["X-Provider-Primary"] = provider_primary
        if secondary_provider:
            if secondary_provider_key is None:
                raise ValueError("secondary_provider_key is required with secondary_provider")
            headers["X-Provider-Secondary"] = secondary_provider
            headers["X-Provider-Key-Secondary"] = secondary_provider_key
        return headers

    @staticmethod
    def _error(response: httpx.Response) -> TokenFlowAPIError:
        code = "http_error"
        try:
            payload = response.json()
            candidate = payload.get("error", {}).get("code")
            if isinstance(candidate, str) and _SAFE_CODE.fullmatch(candidate):
                code = candidate
        except (ValueError, AttributeError, TypeError):
            pass
        return TokenFlowAPIError(response.status_code, code, response.headers.get("Retry-After"))

    @staticmethod
    def _payload(
        prompt: str,
        model: str,
        system: Optional[str],
        max_tokens: Optional[int],
        temperature: Optional[float],
        stream: bool,
    ) -> Dict[str, Any]:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be non-empty text")
        if not isinstance(model, str) or not model.strip():
            raise ValueError("model is required")
        if max_tokens is not None and (not isinstance(max_tokens, int) or max_tokens < 1):
            raise ValueError("max_tokens must be a positive integer")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload: Dict[str, Any] = {"model": model, "messages": messages, "stream": stream}
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if temperature is not None:
            payload["temperature"] = temperature
        return payload

    def complete(
        self,
        prompt: str,
        *,
        model: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        provider_primary: Optional[str] = None,
        secondary_provider: Optional[str] = None,
        secondary_provider_key: Optional[str] = None,
    ) -> Completion:
        payload = self._payload(prompt, model, system, max_tokens, temperature, False)
        headers = self._headers(provider_primary, secondary_provider, secondary_provider_key)
        try:
            response = self._http.post("chat/completions", json=payload, headers=headers)
        except httpx.RequestError:
            raise TokenFlowTransportError() from None
        if response.status_code >= 300:
            raise self._error(response)
        try:
            body = response.json()
        except ValueError:
            raise TokenFlowTransportError() from None
        if not isinstance(body, dict):
            raise TokenFlowTransportError()
        return Completion(body, response.headers.get("X-TokenFlow-Routed-Model"),
                          response.headers.get("X-TokenFlow-Cluster"),
                          response.headers.get("X-TokenFlow-Engine"))

    def stream(
        self,
        prompt: str,
        *,
        model: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        provider_primary: Optional[str] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Yield SSE JSON objects; a partial stream is never resumed silently."""
        payload = self._payload(prompt, model, system, max_tokens, temperature, True)
        headers = self._headers(provider_primary, None, None)
        try:
            with self._http.stream("POST", "chat/completions", json=payload, headers=headers) as response:
                if response.status_code >= 300:
                    response.read()
                    raise self._error(response)
                finished = False
                for line in response.iter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data == "[DONE]":
                        finished = True
                        break
                    try:
                        event = json.loads(data)
                    except ValueError:
                        raise TokenFlowTransportError() from None
                    if not isinstance(event, dict):
                        raise TokenFlowTransportError()
                    if "error" in event:
                        candidate = event["error"]
                        code = candidate.get("code") if isinstance(candidate, dict) else None
                        safe_code = code if isinstance(code, str) and _SAFE_CODE.fullmatch(code) else "stream_error"
                        raise TokenFlowAPIError(response.status_code, safe_code)
                    yield event
                if not finished:
                    raise TokenFlowTransportError()
        except httpx.RequestError:
            raise TokenFlowTransportError() from None
