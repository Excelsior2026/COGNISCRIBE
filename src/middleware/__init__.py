"""Middleware helpers for authentication and rate limiting.

Keep imports here lightweight: importing any submodule (e.g. `src.middleware.auth`)
will execute this package `__init__`, so it must not raise on missing symbols.
"""

from src.middleware.auth import authenticate_request, verify_api_key
from src.middleware.rate_limit import check_rate_limit, cleanup_old_entries, rate_limit_middleware

__all__ = ["authenticate_request", "verify_api_key", "check_rate_limit", "cleanup_old_entries", "rate_limit_middleware"]
