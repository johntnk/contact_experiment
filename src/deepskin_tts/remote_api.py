"""Remote TTS synthesis and interruptible latest-value playback."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from array import array
import json
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Callable
from urllib.request import ProxyHandler, Request, build_opener
from uuid import uuid4
import wave
import winsound


@dataclass(frozen=True)
class RemoteSpeechRequest:
    text: str
    emotion: str = "excited_high"
    volume: int = 100

    def validate(self) -> None:
        if not self.text.strip() or not self.emotion.strip():
            raise ValueError("remote TTS text and emotion are required")
        if not 0 <= int(self.volume) <= 100:
            raise ValueError("remote TTS playback volume must be between 0 and 100")


def build_remote_payload(request: RemoteSpeechRequest, request_id: str) -> bytes:
    request.validate()
    if not request_id:
        raise ValueError("remote TTS request ID is required")
    return json.dumps({
        "request_id": request_id,
        "emotion": request.emotion,
        "text": request.text,
    }, ensure_ascii=False).encode("utf-8")


def inspect_wav(audio: bytes) -> dict[str, int | float]:
    with wave.open(BytesIO(audio), "rb") as stream:
        if stream.getcomptype() != "NONE":
            raise ValueError("remote TTS must return uncompressed PCM WAV")
        frames = stream.getnframes()
        rate = stream.getframerate()
        return {
            "channels": stream.getnchannels(),
            "sample_width": stream.getsampwidth(),
            "sample_rate": rate,
            "frames": frames,
            "duration_s": frames / rate,
        }


def scale_wav_volume(audio: bytes, volume: int) -> bytes:
    """Scale 16-bit PCM samples without changing the Windows master volume."""
    if not 0 <= int(volume) <= 100:
        raise ValueError("remote TTS playback volume must be between 0 and 100")
    source = BytesIO(audio)
    with wave.open(source, "rb") as stream:
        params = stream.getparams()
        if stream.getcomptype() != "NONE" or stream.getsampwidth() != 2:
            raise ValueError("volume scaling requires uncompressed 16-bit PCM WAV")
        frames = stream.readframes(stream.getnframes())
    samples = array("h")
    samples.frombytes(frames)
    if sys.byteorder != "little":
        samples.byteswap()
    factor = int(volume) / 100.0
    for index, sample in enumerate(samples):
        samples[index] = max(-32768, min(32767, round(sample * factor)))
    if sys.byteorder != "little":
        samples.byteswap()
    output = BytesIO()
    with wave.open(output, "wb") as stream:
        stream.setparams(params)
        stream.writeframes(samples.tobytes())
    return output.getvalue()


def synthesize_remote(*, url: str, request: RemoteSpeechRequest,
                      timeout_s: float = 20.0) -> tuple[bytes, dict[str, int | float]]:
    request_id = f"deepskin-{uuid4().hex}"
    http_request = Request(
        url,
        data=build_remote_payload(request, request_id),
        headers={"Content-Type": "application/json", "Accept": "audio/wav"},
        method="POST",
    )
    with build_opener(ProxyHandler({})).open(http_request, timeout=timeout_s) as response:
        content_type = response.headers.get("Content-Type", "")
        audio = response.read()
    if "audio/wav" not in content_type:
        detail = audio[:500].decode("utf-8", errors="replace")
        raise ValueError(f"expected audio/wav, got {content_type!r}: {detail}")
    return audio, inspect_wav(audio)


class RemoteTtsWorker:
    """Download and play one response at a time; replace pending/current speech."""

    def __init__(self, *, url: str, timeout_s: float = 20.0,
                 on_update: Callable[[str, object], None] | None = None,
                 synthesizer: Callable[..., tuple[bytes, dict]] = synthesize_remote) -> None:
        self.url = url
        self.timeout_s = float(timeout_s)
        self.on_update = on_update or (lambda _kind, _payload: None)
        self.synthesizer = synthesizer
        self._condition = threading.Condition()
        self._pending: RemoteSpeechRequest | None = None
        self._stopping = False
        self._thread = threading.Thread(target=self._run, name="deepskin-remote-tts", daemon=True)

    def start(self) -> None:
        self._thread.start()

    def submit(self, request: RemoteSpeechRequest) -> None:
        request.validate()
        with self._condition:
            if self._stopping:
                return
            self._pending = request
            winsound.PlaySound(None, 0)
            self._condition.notify_all()

    def close(self) -> None:
        with self._condition:
            self._stopping = True
            self._pending = None
            winsound.PlaySound(None, 0)
            self._condition.notify_all()

    def _run(self) -> None:
        while True:
            with self._condition:
                while self._pending is None and not self._stopping:
                    self._condition.wait()
                if self._stopping:
                    return
                request = self._pending
                self._pending = None
            self.on_update("synthesizing", request)
            path: Path | None = None
            try:
                audio, info = self.synthesizer(url=self.url, request=request, timeout_s=self.timeout_s)
                audio = scale_wav_volume(audio, request.volume)
                with tempfile.NamedTemporaryFile(prefix="deepskin_tts_", suffix=".wav", delete=False) as temp:
                    temp.write(audio)
                    path = Path(temp.name)
                self.on_update("speaking", {"request": request, "info": info})
                winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)
                deadline = time.monotonic() + float(info["duration_s"])
                with self._condition:
                    while not self._stopping and self._pending is None:
                        remaining = deadline - time.monotonic()
                        if remaining <= 0:
                            break
                        self._condition.wait(timeout=remaining)
                    interrupted = self._stopping or self._pending is not None
                if interrupted:
                    winsound.PlaySound(None, 0)
                else:
                    winsound.PlaySound(None, 0)
                    self.on_update("done", request)
            except Exception as exc:
                if not self._stopping:
                    self.on_update("error", f"{type(exc).__name__}: {exc}")
            finally:
                if path is not None:
                    try:
                        path.unlink(missing_ok=True)
                    except OSError:
                        pass
