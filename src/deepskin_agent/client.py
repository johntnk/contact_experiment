"""Non-blocking, latest-value bridge from touch labels to the IM SSE API."""

from __future__ import annotations

from dataclasses import dataclass
import json
import threading
import time
from typing import Callable, Iterable
from urllib.request import ProxyHandler, Request, build_opener
from urllib.parse import urlsplit, urlunsplit


GESTURE_PROMPTS = {
    "STATIC_TOUCH": "用户正在持续、安静地触摸你。请把这次社交触摸作为当前输入并自然回应。",
    "STROKE": "用户正在轻柔地抚摸你。请把这次社交触摸作为当前输入并自然回应。",
    "RUB": "用户正在来回揉擦你。请把这次社交触摸作为当前输入并自然回应。",
    "TAP": "用户轻点了你一下。请把这次社交触摸作为当前输入并自然回应。",
    "POKE": "用户用手指戳了你一下。请把这次社交触摸作为当前输入并自然回应。",
    "PAT": "用户有节奏地轻拍了你。请把这次社交触摸作为当前输入并自然回应。",
    "IMPACT": "用户突然拍击或碰撞了你。请把这次社交触摸作为当前输入并自然回应。",
}


def gesture_prompt(label: str) -> str:
    try:
        return GESTURE_PROMPTS[label]
    except KeyError as exc:
        raise ValueError(f"unsupported gesture label: {label}") from exc


def im_frontend_url(frontend_url: str, session_id: str) -> str:
    """Build the IM page URL from either a frontend root or another app route."""
    parts = urlsplit(frontend_url)
    if not parts.scheme or not parts.netloc or not session_id:
        raise ValueError("valid frontend URL and session ID are required")
    return urlunsplit((parts.scheme, parts.netloc, f"/im/{session_id}", "", ""))


@dataclass(frozen=True)
class AgentResult:
    label: str
    text: str
    value: dict[str, int | float]
    raw_done: dict


def parse_sse_lines(lines: Iterable[bytes | str]) -> dict:
    """Return the JSON payload of the final SSE `done` event."""
    event = ""
    data_lines: list[str] = []
    for raw in lines:
        line = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
        line = line.rstrip("\r\n")
        if not line:
            if event == "done" and data_lines:
                return json.loads("\n".join(data_lines))
            event = ""
            data_lines = []
        elif line.startswith("event:"):
            event = line[6:].strip()
        elif line.startswith("data:"):
            data_lines.append(line[5:].lstrip())
    if event == "done" and data_lines:
        return json.loads("\n".join(data_lines))
    raise ValueError("SSE stream ended without a done event")


def extract_agent_text(done: dict) -> str:
    """Extract readable assistant text from documented and observed done payloads."""
    data = done.get("data") if isinstance(done, dict) else None
    messages = data.get("messages") if isinstance(data, dict) else None
    if isinstance(messages, list):
        parts = [item.get("text", "") for item in messages if isinstance(item, dict)]
        readable = "\n".join(str(part) for part in parts if part)
        if readable:
            return readable
    text = done.get("text", "") if isinstance(done, dict) else ""
    if isinstance(text, str) and text.lstrip().startswith("{"):
        try:
            nested = json.loads(text)
            nested_messages = nested.get("messages") if isinstance(nested, dict) else None
            if isinstance(nested_messages, list):
                parts = [item.get("text", "") for item in nested_messages if isinstance(item, dict)]
                readable = "\n".join(str(part) for part in parts if part)
                if readable:
                    return readable
        except json.JSONDecodeError:
            pass
    return str(text)


def post_agent_sse(*, url: str, user_id: str, session_id: str, label: str,
                   status: dict[str, int | float], timeout_s: float = 20.0) -> AgentResult:
    payload = {
        "payload": {
            "input": gesture_prompt(label),
            "status": {
                "Mood": status["Mood"],
                "Favor": status["Favor"],
                "Egy": status["Egy"],
                "Stress": status.get("Stress", 0),
            },
        }
    }
    request = Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "text/event-stream",
            "x-user-id": user_id,
            "x-session-id": session_id,
        },
        method="POST",
    )
    # Never route RFC1918 development traffic through a machine-wide proxy.
    with build_opener(ProxyHandler({})).open(request, timeout=timeout_s) as response:
        content_type = response.headers.get("Content-Type", "")
        if "text/event-stream" not in content_type:
            body = response.read(2048).decode("utf-8", errors="replace")
            raise ValueError(f"expected SSE response, got {content_type!r}: {body}")
        done = parse_sse_lines(response)
    data = done.get("data") if isinstance(done, dict) else None
    value = data.get("value") if isinstance(data, dict) else None
    if not isinstance(value, dict):
        value = dict(status)
    return AgentResult(label=label, text=extract_agent_text(done), value=value, raw_done=done)


class AgentDispatcher:
    """Single network worker with a bounded latest-value mailbox."""

    def __init__(self, *, url: str, user_id: str, session_id: str,
                 min_interval_s: float = 3.0, timeout_s: float = 20.0,
                 initial_status: dict[str, int | float] | None = None,
                 on_update: Callable[[str, object], None] | None = None,
                 send: Callable[..., AgentResult] = post_agent_sse) -> None:
        if min_interval_s < 0 or timeout_s <= 0:
            raise ValueError("agent timing values must be positive")
        if not url or not user_id or not session_id:
            raise ValueError("agent URL, user ID, and session ID are required")
        self.url = url
        self.user_id = user_id
        self.session_id = session_id
        self.min_interval_s = float(min_interval_s)
        self.timeout_s = float(timeout_s)
        self.status = dict(initial_status or {"Mood": 0, "Favor": 0, "Egy": -1, "Stress": 0})
        self.on_update = on_update or (lambda _kind, _payload: None)
        self.send = send
        self._condition = threading.Condition()
        self._pending: str | None = None
        self._stopping = False
        self._last_started = float("-inf")
        self._thread = threading.Thread(target=self._run, name="deepskin-agent", daemon=True)

    def start(self) -> None:
        self._thread.start()

    def submit(self, label: str) -> None:
        gesture_prompt(label)
        with self._condition:
            if self._stopping:
                return
            self._pending = label
            self._condition.notify_all()

    def close(self) -> None:
        with self._condition:
            self._stopping = True
            self._pending = None
            self._condition.notify_all()

    def _run(self) -> None:
        while True:
            with self._condition:
                while self._pending is None and not self._stopping:
                    self._condition.wait()
                if self._stopping:
                    return
                wait_s = self.min_interval_s - (time.monotonic() - self._last_started)
                if wait_s > 0:
                    self._condition.wait(timeout=wait_s)
                    continue
                label = self._pending
                self._pending = None
                self._last_started = time.monotonic()
            self.on_update("sending", label)
            try:
                result = self.send(
                    url=self.url, user_id=self.user_id, session_id=self.session_id,
                    label=label, status=dict(self.status), timeout_s=self.timeout_s)
                self.status.update(result.value)
                self.on_update("done", result)
            except Exception as exc:
                self.on_update("error", f"{type(exc).__name__}: {exc}")
