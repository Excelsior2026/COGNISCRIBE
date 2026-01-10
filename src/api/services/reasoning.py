"""Optional integration with reasoning-core for concept and knowledge graph extraction."""
from typing import Any, Dict, Optional

from src.utils.logger import setup_logger
from src.utils.settings import (
    REASONING_CORE_DOMAIN,
    REASONING_CORE_ENABLED,
    REASONING_CORE_USE_LLM,
)

logger = setup_logger(__name__)

try:
    from reasoning_core import (
        ReasoningAPI,
        MedicalDomain,
        BusinessDomain,
        MeetingDomain,
    )

    _REASONING_CORE_AVAILABLE = True
except ImportError:
    ReasoningAPI = None  # type: ignore
    MedicalDomain = BusinessDomain = MeetingDomain = None  # type: ignore
    _REASONING_CORE_AVAILABLE = False


_DOMAIN_FACTORIES = {
    "medical": lambda: MedicalDomain() if MedicalDomain else None,
    "business": lambda: BusinessDomain() if BusinessDomain else None,
    "meeting": lambda: MeetingDomain() if MeetingDomain else None,
    "generic": lambda: None,
}

_api_cache: Dict[str, ReasoningAPI] = {}


def _normalize_domain_name(domain: Optional[str]) -> str:
    name = (domain or REASONING_CORE_DOMAIN or "generic").strip().lower()
    if name not in _DOMAIN_FACTORIES:
        if domain:
            logger.warning("Unknown reasoning-core domain '%s', defaulting to generic", name)
        return "generic"
    return name


def _resolve_domain(domain: Optional[str]):
    domain_name = _normalize_domain_name(domain)
    factory = _DOMAIN_FACTORIES.get(domain_name)
    try:
        return factory()
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Failed to initialize reasoning-core domain '%s': %s", domain_name, exc)
        return None


def _get_api(domain: Optional[str]) -> ReasoningAPI:
    """Get or create a cached ReasoningAPI instance for a domain."""
    domain_key = _normalize_domain_name(domain)
    if domain_key not in _api_cache:
        _api_cache[domain_key] = ReasoningAPI(
            domain=_resolve_domain(domain),
            use_llm=REASONING_CORE_USE_LLM,
        )
    return _api_cache[domain_key]


def analyze_text(text: str, domain: Optional[str] = None, enabled: Optional[bool] = None) -> Dict[str, Any]:
    """Run reasoning-core over text if available/allowed.

    Returns a structured envelope so callers can surface availability or errors
    without failing the main pipeline.
    """
    enabled_flag = REASONING_CORE_ENABLED if enabled is None else enabled
    response: Dict[str, Any] = {
        "enabled": enabled_flag,
        "available": _REASONING_CORE_AVAILABLE and ReasoningAPI is not None,
        "domain": _normalize_domain_name(domain),
        "data": None,
        "error": None,
    }

    if not enabled_flag:
        response["error"] = "Reasoning Core integration disabled"
        return response

    if not response["available"]:
        response["error"] = "reasoning-core package not installed"
        return response

    try:
        api = _get_api(domain)
        reasoning_result = api.process_text(text)
        response["data"] = reasoning_result
        try:
            info = api.get_domain_info()
            if isinstance(info, dict) and info.get("name"):
                response["domain"] = info["name"]
        except Exception:
            pass
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Reasoning Core processing failed: %s", exc)
        response["error"] = str(exc)

    return response
