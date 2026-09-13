/**
 * Procedural telephone ringback & incoming ringing tone generator using Web Audio API.
 * Synthesizes realistic dual-frequency supervisory tones (440 Hz + 480 Hz)
 * without requiring external MP3/WAV assets.
 */

export interface RingtoneController {
  stop: () => void;
}

export interface RingtoneOptions {
  /**
   * 'ringback': Tone heard by the caller (AI agent) while waiting for the customer to answer.
   * 'incoming': Tone heard on the customer's portal when a call arrives.
   */
  mode?: 'ringback' | 'incoming';
  /** Gain volume (0.0 to 1.0). Defaults: 0.15 for ringback, 0.22 for incoming. */
  volume?: number;
}

export function startRingtone(options?: RingtoneOptions): RingtoneController {
  const mode = options?.mode ?? 'ringback';
  const targetVolume = options?.volume ?? (mode === 'incoming' ? 0.22 : 0.15);

  let ctx: AudioContext | null = null;
  let isStopped = false;
  let timerId: ReturnType<typeof setTimeout> | null = null;

  try {
    const AudioCtx =
      window.AudioContext ||
      (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    ctx = new AudioCtx();
  } catch (e) {
    console.warn('Web Audio API not supported for ringtone:', e);
    return { stop: () => {} };
  }

  // Dual tone frequencies (standard Bell / ITU-T supervisory tones: 440 Hz + 480 Hz)
  const freq1 = 440;
  const freq2 = 480;

  const masterGain = ctx.createGain();
  masterGain.gain.setValueAtTime(0.0001, ctx.currentTime);
  masterGain.connect(ctx.destination);

  const osc1 = ctx.createOscillator();
  const osc2 = ctx.createOscillator();
  osc1.type = 'sine';
  osc2.type = 'sine';
  osc1.frequency.setValueAtTime(freq1, ctx.currentTime);
  osc2.frequency.setValueAtTime(freq2, ctx.currentTime);

  osc1.connect(masterGain);
  osc2.connect(masterGain);

  try {
    osc1.start();
    osc2.start();
  } catch {
    // ignore if already started or closed
  }

  const scheduleCycle = () => {
    if (isStopped || !ctx || ctx.state === 'closed') return;

    if (ctx.state === 'suspended') {
      void ctx.resume();
    }

    const now = ctx.currentTime;
    const ramp = 0.025; // 25ms smooth attack/release to eliminate audio pops

    if (mode === 'incoming') {
      // Incoming phone ring pattern: Burst 1 (0.8s) + Pause (0.4s) + Burst 2 (0.8s) + Long pause (2.5s)
      // Total cycle: 4.5s
      try {
        // Burst 1: 0.0s -> 0.8s
        masterGain.gain.setValueAtTime(0.0001, now);
        masterGain.gain.exponentialRampToValueAtTime(targetVolume, now + ramp);
        masterGain.gain.setValueAtTime(targetVolume, now + 0.8 - ramp);
        masterGain.gain.exponentialRampToValueAtTime(0.0001, now + 0.8);

        // Burst 2: 1.2s -> 2.0s
        masterGain.gain.setValueAtTime(0.0001, now + 1.2);
        masterGain.gain.exponentialRampToValueAtTime(targetVolume, now + 1.2 + ramp);
        masterGain.gain.setValueAtTime(targetVolume, now + 2.0 - ramp);
        masterGain.gain.exponentialRampToValueAtTime(0.0001, now + 2.0);
      } catch {
        // audio timing error
      }

      timerId = setTimeout(scheduleCycle, 4500);
    } else {
      // Outbound ringback pattern: 1.6s tone ON + 2.4s pause OFF
      // Total cycle: 4.0s
      try {
        masterGain.gain.setValueAtTime(0.0001, now);
        masterGain.gain.exponentialRampToValueAtTime(targetVolume, now + ramp);
        masterGain.gain.setValueAtTime(targetVolume, now + 1.6 - ramp);
        masterGain.gain.exponentialRampToValueAtTime(0.0001, now + 1.6);
      } catch {
        // audio timing error
      }

      timerId = setTimeout(scheduleCycle, 4000);
    }
  };

  scheduleCycle();

  const stop = () => {
    if (isStopped) return;
    isStopped = true;

    if (timerId) {
      clearTimeout(timerId);
      timerId = null;
    }

    if (ctx && ctx.state !== 'closed') {
      try {
        const now = ctx.currentTime;
        masterGain.gain.cancelScheduledValues(now);
        masterGain.gain.setValueAtTime(Math.max(masterGain.gain.value, 0.0001), now);
        masterGain.gain.exponentialRampToValueAtTime(0.0001, now + 0.03);

        setTimeout(() => {
          try {
            osc1.stop();
            osc2.stop();
            osc1.disconnect();
            osc2.disconnect();
            masterGain.disconnect();
            void ctx?.close();
          } catch {
            // ignore
          }
        }, 40);
      } catch {
        void ctx.close();
      }
    }
  };

  return { stop };
}

