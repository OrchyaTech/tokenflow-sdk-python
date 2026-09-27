"""Errors intentionally avoid embedding upstream bodies or credentials."""

from typing import Optional


class TokenFlowAPIError(Exception):
    def __init__(self, status_code: int, code: str, retry_after: Optional[str] = None):
        self.status_code = status_code
        self.code = code
        self.retry_after = retry_after
        super().__init__(f"TokenFlow returned HTTP {status_code} ({code})")


class TokenFlowTransportError(Exception):
    def __init__(self):
        super().__init__("Could not reach the TokenFlow gateway")
