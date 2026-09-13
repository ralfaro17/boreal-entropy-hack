/**
 * AudioWorkletProcessor that batches mono Float32 input into ~100 ms
 * Int16 PCM chunks and posts them (as transferable ArrayBuffers) to the
 * main thread, ready to ship over a WebSocket for streaming STT/emotion.
 *
 * Expected to run inside an AudioContext created with sampleRate: 16000.
 */
class PcmWriterProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.chunkSize = 1600; // 100 ms @ 16 kHz
    this.buffer = new Int16Array(this.chunkSize);
    this.offset = 0;
  }

  process(inputs) {
    const channel = inputs[0] && inputs[0][0];
    if (!channel) return true;

    for (let i = 0; i < channel.length; i++) {
      const s = Math.max(-1, Math.min(1, channel[i]));
      this.buffer[this.offset++] = s < 0 ? s * 0x8000 : s * 0x7fff;
      if (this.offset === this.chunkSize) {
        const out = this.buffer.buffer.slice(0);
        this.port.postMessage(out, [out]);
        this.offset = 0;
      }
    }
    return true;
  }
}

registerProcessor('pcm-writer', PcmWriterProcessor);
