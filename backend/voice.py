"""
Voice pipeline: streaming STT relay, prosody-based emotion extraction, and TTS proxy.

Architecture
------------
Browser mic --(AudioWorklet 16 kHz Int16 PCM chunks)--> /ws/stt/{room_id}
    ├── forwarded to Deepgram live STT  -> {"type": "partial"|"final", ...} back to client
    └── copied into a rolling buffer    -> ProsodyEmotionAnalyzer every ~2 s
                                        -> {"type": "emotion", ...} back to client

The emotion analyzer is intentionally *not* an ML model: the backend targets
Python 3.14 (no torch wheels), so we compute classical prosodic features
(RMS energy, pitch via autocorrelation, pitch variability, voiced ratio)
with numpy and map them to a continuous arousal/valence estimate with a
per-speaker adaptive baseline. It is an advisory signal for human escalation,
never an automated decision input.

TTS uses Deepgram Aura via simple streamed HTTP proxy so the API key never
reaches the browser. If DEEPGRAM_API_KEY is unset, STT reports itself
unavailable and /tts returns 501 (the client falls back to Web Speech API).
"""

from __future__ import annotations

import asyncio
import json
import math
import os
from dataclasses import dataclass, field

import numpy as np

SAMPLE_RATE = 16_000
EMOTION_WINDOW_SECONDS = 2.0
EMOTION_WINDOW_SAMPLES = int(SAMPLE_RATE * EMOTION_WINDOW_SECONDS)
EMOTION_HOP_SECONDS = 1.0
EMOTION_HOP_SAMPLES = int(SAMPLE_RATE * EMOTION_HOP_SECONDS)

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
DEEPGRAM_STT_URL = (
    "wss://api.deepgram.com/v1/listen"
    "?encoding=linear16&sample_rate=16000&channels=1"
    "&interim_results=true&punctuate=true&smart_format=true&model=nova-2"
    "&language=multi"  # Spanish-first product; customers may also speak English
)
DEEPGRAM_TTS_URL = "https://api.deepgram.com/v1/speak"
DEFAULT_TTS_MODEL = "aura-2-celeste-es"  # Spanish (Colombian); use aura-2-asteria-en for English


def stt_available() -> bool:
    return bool(DEEPGRAM_API_KEY)


def tts_available() -> bool:
    return bool(DEEPGRAM_API_KEY)


# ---------------------------------------------------------------------------
# Prosody-based emotion extraction
# ---------------------------------------------------------------------------

@dataclass
class _RunningStats:
    """Adaptive per-speaker baseline (exponential moving mean/std)."""

    mean: float = 0.0
    var: float = 1.0
    n: int = 0
    alpha: float = 0.05

    def update(self, x: float) -> None:
        if self.n == 0:
            self.mean, self.var = x, max(abs(x) * 0.25, 1e-6)
        else:
            d = x - self.mean
            self.mean += self.alpha * d
            self.var = (1 - self.alpha) * (self.var + self.alpha * d * d)
        self.n += 1

    def zscore(self, x: float) -> float:
        return (x - self.mean) / math.sqrt(max(self.var, 1e-9))


def _estimate_pitch_hz(frame: np.ndarray) -> float:
    """Fundamental frequency of one frame via autocorrelation (60-400 Hz band).
    Returns 0.0 for unvoiced/silent frames."""
    if float(np.abs(frame).max(initial=0.0)) < 1e-4:
        return 0.0
    frame = frame - frame.mean()
    corr = np.correlate(frame, frame, mode="full")[len(frame) - 1 :]
    if corr[0] <= 0:
        return 0.0
    corr = corr / corr[0]
    lag_min = SAMPLE_RATE // 400  # 400 Hz
    lag_max = SAMPLE_RATE // 60  # 60 Hz
    if lag_max >= len(corr):
        return 0.0
    segment = corr[lag_min:lag_max]
    peak = int(np.argmax(segment))
    if segment[peak] < 0.3:  # weak periodicity -> unvoiced
        return 0.0
    return SAMPLE_RATE / (lag_min + peak)


@dataclass
class ProsodyEmotionAnalyzer:
    """Rolling-window prosody analysis for one speaker.

    feed() PCM float32 [-1, 1]; when at least one full window + hop has
    accumulated, analyze() returns an emotion frame dict (or None).
    """

    speaker: str = "speaker"
    _buffer: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=np.float32))
    _since_last: int = 0
    _energy_stats: _RunningStats = field(default_factory=_RunningStats)
    _pitch_stats: _RunningStats = field(default_factory=_RunningStats)
    _last_labels: list[str] = field(default_factory=list)

    def feed(self, pcm_int16: bytes) -> None:
        samples = np.frombuffer(pcm_int16, dtype=np.int16).astype(np.float32) / 32768.0
        self._buffer = np.concatenate([self._buffer, samples])
        self._since_last += len(samples)
        # Keep at most one window of history
        if len(self._buffer) > EMOTION_WINDOW_SAMPLES:
            self._buffer = self._buffer[-EMOTION_WINDOW_SAMPLES:]

    def ready(self) -> bool:
        return (
            len(self._buffer) >= EMOTION_WINDOW_SAMPLES
            and self._since_last >= EMOTION_HOP_SAMPLES
        )

    def analyze(self) -> dict | None:
        if not self.ready():
            return None
        self._since_last = 0
        window = self._buffer[-EMOTION_WINDOW_SAMPLES:]

        # --- frame-level features (25 ms frames, 10 ms hop) -----------------
        frame_len = int(0.025 * SAMPLE_RATE)
        hop = int(0.010 * SAMPLE_RATE)
        n_frames = max(1 + (len(window) - frame_len) // hop, 0)
        if n_frames < 10:
            return None

        rms = np.empty(n_frames)
        pitches = []
        for i in range(n_frames):
            fr = window[i * hop : i * hop + frame_len]
            rms[i] = float(np.sqrt(np.mean(fr**2)))
            # pitch every 3rd frame (cheap enough, ~66 est/window)
            if i % 3 == 0:
                p = _estimate_pitch_hz(fr)
                if p > 0:
                    pitches.append(p)

        energy = float(rms.mean())
        speech_ratio = float((rms > max(energy * 0.5, 1e-4)).mean())

        if energy < 1e-4 or speech_ratio < 0.1 or len(pitches) < 4:
            # silence / no voiced speech: report neutral-calm, don't update baseline
            return self._frame(arousal=0.15, valence=0.55, energy=energy, pitch=0.0, speaking=False)

        pitch_arr = np.array(pitches)
        pitch_mean = float(pitch_arr.mean())
        pitch_cv = float(pitch_arr.std() / max(pitch_mean, 1.0))  # variability
        energy_dyn = float(rms.std() / max(energy, 1e-6))

        # --- adaptive per-speaker normalization ------------------------------
        self._energy_stats.update(energy)
        self._pitch_stats.update(pitch_mean)
        e_z = self._energy_stats.zscore(energy)
        p_z = self._pitch_stats.zscore(pitch_mean)

        # --- map to arousal / valence  ---------------------------------------
        # Arousal: louder-than-baseline, higher pitch, more pitch movement, more dynamics.
        arousal_raw = 0.35 * e_z + 0.30 * p_z + 0.20 * (pitch_cv * 10) + 0.15 * (energy_dyn * 2)
        arousal = 1.0 / (1.0 + math.exp(-arousal_raw))  # sigmoid -> (0, 1)

        # Valence (crude, prosody-only): monotone + low-energy speech reads
        # negative/flat; moderate variability with stable energy reads positive.
        valence_raw = 0.5 * (pitch_cv * 10 - 0.8) - 0.4 * max(e_z, 0) * max(p_z, 0)
        valence = max(0.0, min(1.0, 0.5 + 0.3 * math.tanh(valence_raw)))

        return self._frame(arousal, valence, energy, pitch_mean, speaking=True)

    def _frame(
        self, arousal: float, valence: float, energy: float, pitch: float, speaking: bool
    ) -> dict:
        label = self._label(arousal, valence, speaking)
        self._last_labels = (self._last_labels + [label])[-3:]
        sustained_distress = self._last_labels[-2:] == ["distressed", "distressed"]
        return {
            "type": "emotion",
            "speaker": self.speaker,
            "arousal": round(arousal, 3),
            "valence": round(valence, 3),
            "energy": round(energy, 5),
            "pitch_hz": round(pitch, 1),
            "speaking": speaking,
            "label": label,
            "sustained_distress": sustained_distress,
        }

    @staticmethod
    def _label(arousal: float, valence: float, speaking: bool) -> str:
        if not speaking:
            return "silent"
        if arousal >= 0.7 and valence <= 0.35:
            return "distressed"
        if arousal >= 0.7:
            return "elevated"
        if arousal <= 0.3:
            return "calm"
        return "neutral"


# ---------------------------------------------------------------------------
# Deepgram live STT relay
# ---------------------------------------------------------------------------

class DeepgramSession:
    """Thin async wrapper around one Deepgram live-transcription websocket."""

    def __init__(self) -> None:
        self._ws = None
        self._keepalive_task: asyncio.Task | None = None

    async def __aenter__(self) -> "DeepgramSession":
        import websockets  # provided by uvicorn[standard]

        self._ws = await websockets.connect(
            DEEPGRAM_STT_URL,
            additional_headers={"Authorization": f"Token {DEEPGRAM_API_KEY}"},
        )
        self._keepalive_task = asyncio.create_task(self._keepalive())
        return self

    async def __aexit__(self, *exc) -> None:
        if self._keepalive_task:
            self._keepalive_task.cancel()
        if self._ws:
            try:
                await self._ws.send(json.dumps({"type": "CloseStream"}))
            except Exception:
                pass
            await self._ws.close()

    async def _keepalive(self) -> None:
        while True:
            await asyncio.sleep(8)
            try:
                await self._ws.send(json.dumps({"type": "KeepAlive"}))
            except Exception:
                return

    async def send_audio(self, chunk: bytes) -> None:
        await self._ws.send(chunk)

    async def transcripts(self):
        """Yield {"type": "partial"|"final", "text": str} dicts."""
        async for raw in self._ws:
            try:
                msg = json.loads(raw)
            except (TypeError, ValueError):
                continue
            if msg.get("type") != "Results":
                continue
            alt = (msg.get("channel") or {}).get("alternatives") or [{}]
            text = (alt[0].get("transcript") or "").strip()
            if not text:
                continue
            yield {
                "type": "final" if msg.get("is_final") else "partial",
                "text": text,
            }


# ---------------------------------------------------------------------------
# TTS proxy (Deepgram Aura)
# ---------------------------------------------------------------------------

async def stream_tts(text: str, model: str = DEFAULT_TTS_MODEL, encoding: str = "mp3"):
    """Async generator yielding TTS audio chunks for the given text."""
    import httpx  # provided by fastapi[standard]

    params = {"model": model}
    if encoding == "linear16":
        params.update({"encoding": "linear16", "sample_rate": "24000", "container": "none"})

    async with httpx.AsyncClient(timeout=30.0) as client:
        async with client.stream(
            "POST",
            DEEPGRAM_TTS_URL,
            params=params,
            headers={
                "Authorization": f"Token {DEEPGRAM_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"text": text[:2000]},
        ) as resp:
            resp.raise_for_status()
            async for chunk in resp.aiter_bytes(chunk_size=8192):
                yield chunk
