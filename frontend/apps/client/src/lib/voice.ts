/**
 * Voice pipeline helpers: mic capture -> 16 kHz PCM chunks (AudioWorklet),
 * TTS playback that is mixed into the outgoing call stream, and shared types.
 */

/** Deterministic PeerJS id for a customer's call portal (so the AI agent can dial them). */
export function customerPeerId(customerId: string): string {
  return `bancobranza-cust-${customerId}`;
}

/** Deterministic-prefix PeerJS id for the AI agent side (random suffix avoids collisions). */
export function agentPeerId(): string {
  return `bancobranza-agent-${Math.random().toString(36).slice(2, 8)}`;
}

export interface TranscriptEvent {
  type: 'partial' | 'final';
  text: string;
  speaker: string;
  persisted?: boolean;
  escalated?: boolean;
}

export interface EmotionEvent {
  type: 'emotion';
  speaker: string;
  arousal: number;
  valence: number;
  energy: number;
  pitch_hz: number;
  speaking: boolean;
  label: 'silent' | 'calm' | 'neutral' | 'elevated' | 'distressed';
  sustained_distress: boolean;
}

export type VoiceSocketEvent =
  | TranscriptEvent
  | EmotionEvent
  | { type: 'ready'; stt: boolean; emotion: boolean; speaker: string };

export interface PcmCapture {
  stop: () => void;
}

/**
 * Pipe a MediaStream through an AudioWorklet that emits ~100 ms Int16 PCM
 * chunks at 16 kHz and forward each chunk to `onChunk`.
 */
export async function startPcmCapture(
  stream: MediaStream,
  onChunk: (chunk: ArrayBuffer) => void,
): Promise<PcmCapture> {
  const ctx = new AudioContext({ sampleRate: 16000 });
  await ctx.audioWorklet.addModule('/pcm-worklet.js');
  const source = ctx.createMediaStreamSource(stream);
  const node = new AudioWorkletNode(ctx, 'pcm-writer');
  node.port.onmessage = (e: MessageEvent<ArrayBuffer>) => onChunk(e.data);
  source.connect(node);
  // Worklet has no output; connect through a muted gain to keep the graph alive.
  const silent = ctx.createGain();
  silent.gain.value = 0;
  node.connect(silent);
  silent.connect(ctx.destination);

  return {
    stop: () => {
      node.port.onmessage = null;
      source.disconnect();
      node.disconnect();
      void ctx.close();
    },
  };
}

/** Deepgram Aura voices per language (Spanish-first product policy). */
export const TTS_VOICES: Record<string, string> = {
  es: 'aura-2-celeste-es',
  en: 'aura-2-asteria-en',
};

export interface PlayTtsOptions {
  localMonitor?: boolean;
  language?: string;
  signal?: AbortSignal;
}

export interface CallAudioGraph {
  /** Stream to hand to peer.call(): mic + TTS mixed together. */
  outgoingStream: MediaStream;
  /** Play AI TTS audio into the call (both parties hear it). */
  playTts: (text: string, opts?: PlayTtsOptions) => Promise<void>;
  /** Stop any TTS currently playing or pending. */
  stopTts: () => void;
  close: () => void;
}

/**
 * Build the outgoing audio graph:
 *   mic ----------------.
 *                        +--> MediaStreamDestination --> PeerJS track
 *   TTS (decoded) ------'                     `--> (optional) local speakers
 */
export function createCallAudioGraph(micStream: MediaStream): CallAudioGraph {
  const ctx = new AudioContext();
  const dest = ctx.createMediaStreamDestination();

  const micSource = ctx.createMediaStreamSource(micStream);
  const micGain = ctx.createGain();
  micSource.connect(micGain);
  micGain.connect(dest);

  let currentTts: AudioBufferSourceNode | null = null;
  let playbackSeq = 0;

  const stopTts = () => {
    playbackSeq++; // Invalidate any pending in-flight fetch / decode
    if (currentTts) {
      try {
        currentTts.stop();
        currentTts.disconnect();
      } catch {
        // already stopped or disconnected
      }
      currentTts = null;
    }
  };

  const playTts = async (text: string, opts?: PlayTtsOptions) => {
    const seq = ++playbackSeq;
    const model = TTS_VOICES[opts?.language ?? 'es'] ?? TTS_VOICES.es;

    if (opts?.signal?.aborted) return;

    const res = await fetch('/voice/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, encoding: 'mp3', model }),
      signal: opts?.signal,
    });
    if (!res.ok) {
      // 501 => no API key configured; caller may fall back to Web Speech API.
      throw new Error(`TTS failed: ${res.status}`);
    }

    if (playbackSeq !== seq || opts?.signal?.aborted) return;

    const buf = await res.arrayBuffer();
    if (playbackSeq !== seq || opts?.signal?.aborted) return;

    const audioBuf = await ctx.decodeAudioData(buf);
    if (playbackSeq !== seq || opts?.signal?.aborted) return;

    if (currentTts) {
      try {
        currentTts.stop();
      } catch {
        // ignore
      }
      currentTts = null;
    }

    const src = ctx.createBufferSource();
    src.buffer = audioBuf;
    src.connect(dest); // into the call
    if (opts?.localMonitor !== false) src.connect(ctx.destination); // local speakers
    currentTts = src;

    await ctx.resume();
    src.start();

    await new Promise<void>((resolve) => {
      const handleEnded = () => {
        if (currentTts === src) {
          currentTts = null;
        }
        resolve();
      };
      src.onended = handleEnded;
      opts?.signal?.addEventListener(
        'abort',
        () => {
          try {
            src.stop();
          } catch {
            // ignore
          }
          handleEnded();
        },
        { once: true },
      );
    });
  };

  return {
    outgoingStream: dest.stream,
    playTts,
    stopTts,
    close: () => {
      stopTts();
      void ctx.close();
    },
  };
}

/**
 * Detect whether incoming transcribed speech is likely acoustic echo of the AI's
 * current utterance (e.g. from laptop speakers bleeding into mic) rather than
 * genuine customer interruption.
 */
export function isEchoOfAi(spokenText: string, aiText: string): boolean {
  if (!aiText || !spokenText) return false;
  const clean = (s: string) =>
    s
      .toLowerCase()
      .replace(/[.,/#!$%^&*;:{}=\-_`~()?"'¡¿]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();

  const cleanSpoken = clean(spokenText);
  const cleanAi = clean(aiText);
  if (!cleanSpoken) return false;

  const spokenWords = cleanSpoken.split(' ').filter(Boolean);
  if (spokenWords.length === 0) return false;

  // Common single-word barge-in keywords should NEVER be treated as echo
  const interruptKeywords = new Set([
    'no', 'espera', 'wait', 'stop', 'alto', 'oye', 'pero', 'momento', 'calla', 'parar', 'hold', 'pause'
  ]);
  if (spokenWords.length === 1 && interruptKeywords.has(spokenWords[0])) {
    return false;
  }

  // Word-boundary check: exact phrase match in AI text
  const paddedAi = ` ${cleanAi} `;
  const paddedSpoken = ` ${cleanSpoken} `;
  if (paddedAi.includes(paddedSpoken)) {
    return true;
  }

  // Word overlap check for partial acoustic bleeding
  const longSpokenWords = spokenWords.filter((w) => w.length > 2);
  if (longSpokenWords.length >= 2) {
    const aiWords = new Set(cleanAi.split(' ').filter((w) => w.length > 2));
    const matchCount = longSpokenWords.filter((w) => aiWords.has(w)).length;
    if (matchCount / longSpokenWords.length >= 0.75) {
      return true;
    }
  }

  return false;
}

/** Browser-native fallback when the backend TTS is not configured. */
export function speakWithWebSpeech(text: string): Promise<void> {
  return new Promise((resolve) => {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.onend = () => resolve();
    utterance.onerror = () => resolve();
    speechSynthesis.speak(utterance);
  });
}

/** Open the STT/emotion WebSocket for a room.
 * Set opts.persist=false when another flow (e.g. /voice/agent-reply) already
 * persists transcripts, to avoid duplicate Message rows. */
export function openVoiceSocket(
  roomId: string,
  speaker: string,
  onEvent: (ev: VoiceSocketEvent) => void,
  opts?: { persist?: boolean },
): WebSocket {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const persist = opts?.persist ?? true;
  const ws = new WebSocket(
    `${protocol}//${window.location.host}/ws/stt/${encodeURIComponent(roomId)}?speaker=${encodeURIComponent(speaker)}&persist=${persist}`,
  );
  ws.binaryType = 'arraybuffer';
  ws.onmessage = (e) => {
    try {
      onEvent(JSON.parse(e.data) as VoiceSocketEvent);
    } catch {
      // ignore malformed frames
    }
  };
  return ws;
}
