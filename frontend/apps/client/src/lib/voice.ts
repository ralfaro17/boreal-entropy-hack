/**
 * Voice pipeline helpers: mic capture -> 16 kHz PCM chunks (AudioWorklet),
 * TTS playback that is mixed into the outgoing call stream, and shared types.
 */

/** Deterministic PeerJS id for a customer's call portal (so the AI agent can dial them). */
export function customerPeerId(customerId: string): string {
  return `boreal-cust-${customerId}`;
}

/** Deterministic-prefix PeerJS id for the AI agent side (random suffix avoids collisions). */
export function agentPeerId(): string {
  return `boreal-agent-${Math.random().toString(36).slice(2, 8)}`;
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

export interface CallAudioGraph {
  /** Stream to hand to peer.call(): mic + TTS mixed together. */
  outgoingStream: MediaStream;
  /** Play AI TTS audio into the call (both parties hear it). */
  playTts: (text: string, opts?: { localMonitor?: boolean }) => Promise<void>;
  /** Stop any TTS currently playing. */
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

  const playTts = async (text: string, opts?: { localMonitor?: boolean }) => {
    const res = await fetch('/voice/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, encoding: 'mp3' }),
    });
    if (!res.ok) {
      // 501 => no API key configured; caller may fall back to Web Speech API.
      throw new Error(`TTS failed: ${res.status}`);
    }
    const buf = await res.arrayBuffer();
    const audioBuf = await ctx.decodeAudioData(buf);
    currentTts?.stop();
    const src = ctx.createBufferSource();
    src.buffer = audioBuf;
    src.connect(dest); // into the call
    if (opts?.localMonitor !== false) src.connect(ctx.destination); // local speakers
    currentTts = src;
    await ctx.resume();
    src.start();
    await new Promise<void>((resolve) => {
      src.onended = () => resolve();
    });
  };

  return {
    outgoingStream: dest.stream,
    playTts,
    stopTts: () => currentTts?.stop(),
    close: () => void ctx.close(),
  };
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

/** Open the STT/emotion WebSocket for a room. */
export function openVoiceSocket(
  roomId: string,
  speaker: string,
  onEvent: (ev: VoiceSocketEvent) => void,
): WebSocket {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const ws = new WebSocket(
    `${protocol}//${window.location.host}/ws/stt/${encodeURIComponent(roomId)}?speaker=${encodeURIComponent(speaker)}`,
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
