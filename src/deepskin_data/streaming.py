"""Online contact-event state machine for continuous Deepskin inference."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class CompletedContactEvent:
    event_index: int
    matrix: np.ndarray
    timestamps_ms: np.ndarray
    forced_max_duration: bool


@dataclass(frozen=True)
class DetectorUpdate:
    contact_started: bool = False
    completed: CompletedContactEvent | None = None


def count_micro_contacts(
    matrix: np.ndarray,
    timestamps_ms: np.ndarray,
    *,
    start_threshold: float = 3.0,
    baseline_margin: float = 2.0,
    min_gap_ms: float = 100.0,
    min_contact_ms: float = 40.0,
) -> int:
    """Count separated, non-trivial contacts in one completed episode."""
    matrix = np.asarray(matrix, dtype=float)
    timestamps = np.asarray(timestamps_ms, dtype=float)
    if matrix.ndim != 3 or timestamps.ndim != 1 or len(matrix) != len(timestamps) or not len(timestamps):
        raise ValueError("micro-contact input must be non-empty [T,H,W] data with T timestamps")
    peak = np.maximum(matrix, 0.0).max(axis=(1, 2))
    # Completed streaming events contain 150 ms of pre-roll. Use only its first
    # half so a long first contact cannot raise its own baseline.
    baseline = peak[timestamps <= min(75.0, float(timestamps[-1]))]
    threshold = max(float(start_threshold), float(np.median(baseline)) + float(baseline_margin))
    active_indices = np.flatnonzero(peak >= threshold)
    if not active_indices.size:
        return 0
    active = peak >= threshold
    for left, right in zip(active_indices[:-1], active_indices[1:]):
        if right > left + 1 and timestamps[right] - timestamps[left] < min_gap_ms:
            active[left : right + 1] = True
    runs: list[tuple[int, int]] = []
    start: int | None = None
    for index, value in enumerate(active):
        if value and start is None:
            start = index
        if start is not None and (not value or index == len(active) - 1):
            end = index if value and index == len(active) - 1 else index - 1
            if timestamps[end] - timestamps[start] >= min_contact_ms:
                runs.append((start, end))
            start = None
    return len(runs)


def apply_episode_label_rule(model_prediction: str, micro_contact_count: int) -> tuple[str, str]:
    """Apply the frozen repeated-impulse definition of PAT to an IMPACT candidate."""
    if model_prediction == "IMPACT" and 2 <= micro_contact_count <= 4:
        return "PAT", "impact_to_pat_repeated_episode"
    return model_prediction, "model"


def episode_gate_reference_label(model_prediction: str, classification_rule: str) -> str:
    """Gate the model evidence before an episode-level semantic relabel."""
    if classification_rule == "impact_to_pat_repeated_episode":
        return model_prediction
    return model_prediction


class ContactEventDetector:
    """Detect debounced contact episodes while retaining pre/post-release frames."""

    def __init__(self, *, start_threshold: float = 3.0, baseline_margin: float = 2.0,
                 start_debounce_ms: float = 40.0, end_hold_ms: float = 300.0,
                 pre_roll_ms: float = 150.0, baseline_window_ms: float = 1000.0,
                 max_event_ms: float = 8000.0) -> None:
        if min(start_debounce_ms, end_hold_ms, pre_roll_ms, baseline_window_ms, max_event_ms) < 0:
            raise ValueError("streaming detector durations must be non-negative")
        self.start_threshold = float(start_threshold)
        self.baseline_margin = float(baseline_margin)
        self.start_debounce_ms = float(start_debounce_ms)
        self.end_hold_ms = float(end_hold_ms)
        self.pre_roll_ms = float(pre_roll_ms)
        self.baseline_window_ms = float(baseline_window_ms)
        self.max_event_ms = float(max_event_ms)
        self._pre_roll: deque[tuple[float, np.ndarray, float]] = deque()
        self._idle_peaks: deque[tuple[float, float]] = deque()
        self._event_frames: list[tuple[float, np.ndarray]] = []
        self._candidate_since: float | None = None
        self._event_start: float | None = None
        self._last_active: float | None = None
        self._active = False
        self._last_timestamp: float | None = None
        self._event_index = 0

    @property
    def active(self) -> bool:
        return self._active

    @property
    def threshold(self) -> float:
        baseline = np.median([peak for _, peak in self._idle_peaks]) if self._idle_peaks else 0.0
        return max(self.start_threshold, float(baseline) + self.baseline_margin)

    @staticmethod
    def _peak(matrix: np.ndarray) -> float:
        frame = np.asarray(matrix, dtype=float)
        if frame.ndim != 2 or not np.isfinite(frame).all():
            raise ValueError("streaming frame must be a finite 2D matrix")
        return float(np.maximum(frame, 0.0).max())

    def update(self, matrix: np.ndarray, timestamp_ms: float) -> DetectorUpdate:
        timestamp_ms = float(timestamp_ms)
        if self._last_timestamp is not None and timestamp_ms < self._last_timestamp:
            raise ValueError("streaming timestamps must be monotonic")
        self._last_timestamp = timestamp_ms
        frame = np.asarray(matrix, dtype=np.float64).copy()
        peak = self._peak(frame)
        active_now = peak >= self.threshold

        if not self._active:
            self._pre_roll.append((timestamp_ms, frame, peak))
            while self._pre_roll and timestamp_ms - self._pre_roll[0][0] > self.pre_roll_ms:
                self._pre_roll.popleft()
            if active_now:
                if self._candidate_since is None:
                    self._candidate_since = timestamp_ms
                if timestamp_ms - self._candidate_since >= self.start_debounce_ms:
                    self._active = True
                    self._event_start = self._candidate_since
                    self._last_active = timestamp_ms
                    self._event_frames = [(time_ms, item) for time_ms, item, _ in self._pre_roll]
                    self._pre_roll.clear()
                    return DetectorUpdate(contact_started=True)
            else:
                self._candidate_since = None
                self._idle_peaks.append((timestamp_ms, peak))
                while self._idle_peaks and timestamp_ms - self._idle_peaks[0][0] > self.baseline_window_ms:
                    self._idle_peaks.popleft()
            return DetectorUpdate()

        self._event_frames.append((timestamp_ms, frame))
        if active_now:
            self._last_active = timestamp_ms
        forced = bool(self._event_start is not None and timestamp_ms - self._event_start >= self.max_event_ms)
        released = bool(self._last_active is not None and timestamp_ms - self._last_active >= self.end_hold_ms)
        if not forced and not released:
            return DetectorUpdate()
        self._event_index += 1
        times = np.asarray([item[0] for item in self._event_frames], dtype=np.float64)
        matrices = np.stack([item[1] for item in self._event_frames])
        completed = CompletedContactEvent(self._event_index, matrices, times - times[0], forced)
        self._active = False
        self._candidate_since = None
        self._event_start = None
        self._last_active = None
        self._event_frames = []
        self._pre_roll.clear()
        self._idle_peaks.clear()
        return DetectorUpdate(completed=completed)
