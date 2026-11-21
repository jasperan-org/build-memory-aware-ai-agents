"""LLM access for the labs: one LiteLLM model string, an ordered list of endpoint/key routes.

The workshop ships shared OCI Generative AI keys in `.env.example`: three keys on the primary
endpoint (`OCI_GENAI_ENDPOINT`, Phoenix) and three on the fallback endpoint
(`OCI_GENAI_FALLBACK_ENDPOINT`, Chicago); up to six per endpoint are read. Both serve the same model through OCI's
OpenAI-compatible API, which is why `OAMP_LLM` carries the `openai/` prefix. Every process
shuffles the keys within each endpoint so a full room spreads its load, and a route that is
rate limited, rejected, missing the model, or unreachable fails over to the next one.

Without an OCI endpoint configured, `OAMP_LLM` is a plain LiteLLM model string and LiteLLM
reads the provider's own key variable (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, ...).
"""

from __future__ import annotations

import os
import random
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, TypeVar

T = TypeVar("T")

ENDPOINT_GROUPS = (
    ("OCI_GENAI_ENDPOINT", "OCI_GENAI_API_KEY"),
    ("OCI_GENAI_FALLBACK_ENDPOINT", "OCI_GENAI_FALLBACK_API_KEY"),
)
MAX_KEYS_PER_ENDPOINT = 6
REQUEST_TIMEOUT_S = 120

# 404 covers a model that one region does not serve; 408/429/5xx are transient; 401/403 is a bad key.
_FAILOVER_STATUS = {401, 403, 404, 408, 429}
_FAILOVER_NAMES = (
    "ratelimit", "authentication", "permissiondenied", "notfound",
    "apiconnection", "timeout", "serviceunavailable", "internalserver", "badgateway",
)
_FAILOVER_TOKENS = (
    "429", "rate limit", "too many requests", "401", "unauthorized", "authentication",
    "timed out", "timeout", "connection", "service unavailable", "overloaded",
)


@dataclass(frozen=True)
class Route:
    """One way to reach the model: an endpoint and a key, or LiteLLM's provider defaults."""

    label: str
    api_base: str | None = None
    api_key: str | None = None

    def kwargs(self) -> dict[str, str]:
        out = {}
        if self.api_base:
            out["api_base"] = self.api_base
        if self.api_key:
            out["api_key"] = self.api_key
        return out


def llm_model() -> str:
    return os.environ.get("OAMP_LLM", "").strip()


def configured_routes(rng: random.Random | None = None) -> list[Route]:
    """Return the OCI endpoint/key routes in failover order (keys shuffled within an endpoint)."""

    rng = rng or random.Random()
    routes: list[Route] = []
    for endpoint_var, key_var in ENDPOINT_GROUPS:
        endpoint = os.environ.get(endpoint_var, "").strip()
        if not endpoint:
            continue
        names = [key_var] + [f"{key_var}_{i}" for i in range(2, MAX_KEYS_PER_ENDPOINT + 1)]
        keyed = [(name, os.environ[name].strip()) for name in names if os.environ.get(name, "").strip()]
        rng.shuffle(keyed)
        routes += [Route(f"{endpoint_var} + {name}", endpoint, key) for name, key in keyed]
    return routes


def llm_status() -> tuple[bool, str]:
    """Check the configuration without a network call: a model plus a credential that fits it."""

    model = llm_model()
    if not model:
        return False, "OAMP_LLM is not set; copy .env.example to .env"
    if any(os.environ.get(endpoint_var, "").strip() for endpoint_var, _ in ENDPOINT_GROUPS):
        routes = configured_routes()
        if not routes:
            return False, "OCI_GENAI_ENDPOINT is set but no OCI_GENAI_API_KEY* value is; copy them from .env.example"
        return True, f"{model} via {len(routes)} OCI Generative AI endpoint/key routes"
    if model.startswith("ollama/"):
        return True, f"{model} on the local Ollama server"
    import litellm

    missing = litellm.validate_environment(model=model).get("missing_keys") or []
    if missing:
        return False, f"{model} needs {', '.join(missing)} in .env or the shell"
    return True, f"{model} with the provider key from the environment"


def _status_of(exc: BaseException) -> int | None:
    for holder in (exc, getattr(exc, "response", None)):
        value = getattr(holder, "status_code", None)
        try:
            if value is not None and 100 <= int(value) <= 599:
                return int(value)
        except (TypeError, ValueError):
            continue
    return None


def should_fail_over(exc: BaseException) -> bool:
    """True when another route may succeed: rate limit, bad key, missing model, network, 5xx.

    OAMP wraps LiteLLM errors, so the whole `__cause__`/`__context__` chain is inspected.
    """

    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        status = _status_of(current)
        if status is not None:
            return status in _FAILOVER_STATUS or status >= 500
        name = type(current).__name__.lower()
        message = str(current).lower()
        if isinstance(current, (ConnectionError, TimeoutError)) or any(n in name for n in _FAILOVER_NAMES):
            return True
        if any(token in message for token in _FAILOVER_TOKENS):
            return True
        current = current.__cause__ or current.__context__
    return False


class _Router:
    """Tries routes from the last one that worked; remembers the winner for the next call."""

    def __init__(self) -> None:
        self._routes: list[Route] | None = None
        self._active = 0

    @property
    def routes(self) -> list[Route]:
        if self._routes is None:
            self._routes = configured_routes() or [Route("provider key from the environment")]
        return self._routes

    def _order(self) -> list[int]:
        n = len(self.routes)
        return [(self._active + offset) % n for offset in range(n)]

    def _exhausted(self, errors: list[str]) -> RuntimeError:
        return RuntimeError("Every LLM route failed:\n  " + "\n  ".join(errors))

    def call(self, fn: Callable[[Route], T]) -> T:
        errors: list[str] = []
        for index in self._order():
            route = self.routes[index]
            try:
                result = fn(route)
            except Exception as exc:
                if not should_fail_over(exc):
                    raise
                errors.append(f"{route.label}: {type(exc).__name__}: {str(exc).splitlines()[0][:160]}")
                continue
            self._active = index
            return result
        raise self._exhausted(errors)

    async def acall(self, fn: Callable[[Route], Any]) -> Any:
        errors: list[str] = []
        for index in self._order():
            route = self.routes[index]
            try:
                result = await fn(route)
            except Exception as exc:
                if not should_fail_over(exc):
                    raise
                errors.append(f"{route.label}: {type(exc).__name__}: {str(exc).splitlines()[0][:160]}")
                continue
            self._active = index
            return result
        raise self._exhausted(errors)


_router = _Router()


def chat_completion(messages: Sequence[dict[str, str]], **kwargs: Any) -> Any:
    """Send chat messages to `OAMP_LLM` with failover across routes; return the full LiteLLM response."""

    import litellm

    litellm.suppress_debug_info = True
    model = llm_model()
    kwargs.setdefault("timeout", REQUEST_TIMEOUT_S)

    def send(route: Route) -> Any:
        return litellm.completion(model=model, messages=list(messages), **route.kwargs(), **kwargs)

    return _router.call(send)


def chat(messages: Sequence[dict[str, str]], **kwargs: Any) -> str:
    """Send chat messages to `OAMP_LLM` with failover across routes; return the reply text."""

    return chat_completion(messages, **kwargs).choices[0].message.content or ""


def ping() -> tuple[bool, str]:
    """Make one short live call; return (ok, detail)."""

    ready, detail = llm_status()
    if not ready:
        return False, detail
    started = time.monotonic()
    try:
        chat([{"role": "user", "content": "Reply with the single word OK."}])
    except Exception as exc:
        return False, f"{llm_model()} call failed: {str(exc).splitlines()[0][:300]}"
    route = _router.routes[_router._active]
    return True, f"{llm_model()} answered in {time.monotonic() - started:.1f}s via {route.label}"


def oamp_llm() -> Any:
    """Return an OAMP `ILlm` that routes extraction and summary calls through the same failover."""

    import litellm
    from oracleagentmemory.apis.llms.llm import ILlm
    from oracleagentmemory.core.llms import Llm

    litellm.suppress_debug_info = True
    model = llm_model()
    per_route: dict[Route, Llm] = {}

    def llm_for(route: Route) -> Llm:
        if route not in per_route:
            per_route[route] = Llm(model, **route.kwargs())
        return per_route[route]

    class FailoverLlm(ILlm):
        def generate(self, prompt, *, response_json_schema=None, **kwargs):
            return _router.call(
                lambda route: llm_for(route).generate(prompt, response_json_schema=response_json_schema, **kwargs)
            )

        async def generate_async(self, prompt, *, response_json_schema=None, **kwargs):
            return await _router.acall(
                lambda route: llm_for(route).generate_async(prompt, response_json_schema=response_json_schema, **kwargs)
            )

    return FailoverLlm()
