import { useCallback, useEffect, useRef, useState } from 'react';
import Peer, { type MediaConnection } from 'peerjs';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Textarea } from '@/components/ui/textarea';
import { PageHeader } from '@/components/page-header';
import { showErrorToast, showSuccessToast } from '@/lib/toast-utils';
import {
  createCallAudioGraph,
  openVoiceSocket,
  speakWithWebSpeech,
  startPcmCapture,
  type CallAudioGraph,
  type EmotionEvent,
  type PcmCapture,
} from '@/lib/voice';
import {
  Phone,
  PhoneOff,
  Mic,
  MicOff,
  Copy,
  Captions,
  Activity,
  Volume2,
  AlertTriangle,
  Radio,
  User,
} from 'lucide-react';

type CallStatus = 'idle' | 'ready' | 'calling' | 'in-call';

interface CaptionLine {
  id: number;
  speaker: string;
  text: string;
  final: boolean;
}

const EMOTION_STYLES: Record<EmotionEvent['label'], { color: string; bg: string }> = {
  silent: { color: 'text-muted-foreground', bg: 'bg-muted' },
  calm: { color: 'text-emerald-600 dark:text-emerald-400', bg: 'bg-emerald-500' },
  neutral: { color: 'text-primary', bg: 'bg-primary' },
  elevated: { color: 'text-amber-600 dark:text-amber-400', bg: 'bg-amber-500' },
  distressed: { color: 'text-destructive', bg: 'bg-destructive' },
};

let captionSeq = 0;

export function Call() {
  const { t } = useTranslation();
  const [status, setStatus] = useState<CallStatus>('idle');
  const [myPeerId, setMyPeerId] = useState('');
  const [remotePeerId, setRemotePeerId] = useState('');
  const [roomId, setRoomId] = useState('');
  const [muted, setMuted] = useState(false);
  const [sttEnabled, setSttEnabled] = useState<boolean | null>(null);
  const [captions, setCaptions] = useState<CaptionLine[]>([]);
  const [emotion, setEmotion] = useState<EmotionEvent | null>(null);
  const [distressAlert, setDistressAlert] = useState(false);
  const [ttsText, setTtsText] = useState('');
  const [ttsBusy, setTtsBusy] = useState(false);

  const peerRef = useRef<Peer | null>(null);
  const callRef = useRef<MediaConnection | null>(null);
  const micStreamRef = useRef<MediaStream | null>(null);
  const graphRef = useRef<CallAudioGraph | null>(null);
  const captureRef = useRef<PcmCapture | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const remoteAudioRef = useRef<HTMLAudioElement | null>(null);
  const captionsEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    captionsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [captions]);

  const cleanup = useCallback(() => {
    captureRef.current?.stop();
    captureRef.current = null;
    socketRef.current?.close();
    socketRef.current = null;
    callRef.current?.close();
    callRef.current = null;
    graphRef.current?.close();
    graphRef.current = null;
    micStreamRef.current?.getTracks().forEach((t) => t.stop());
    micStreamRef.current = null;
    peerRef.current?.destroy();
    peerRef.current = null;
    if (remoteAudioRef.current) remoteAudioRef.current.srcObject = null;
    setEmotion(null);
    setStatus('idle');
    setMyPeerId('');
  }, []);

  useEffect(() => cleanup, [cleanup]);

  /** Start STT + emotion streaming over the local mic. */
  const startVoicePipeline = useCallback(async (micStream: MediaStream, room: string) => {
    const ws = openVoiceSocket(room || 'lobby', 'customer', (ev) => {
      if (ev.type === 'ready') {
        setSttEnabled(ev.stt);
        return;
      }
      if (ev.type === 'emotion') {
        setEmotion(ev);
        if (ev.sustained_distress) setDistressAlert(true);
        return;
      }
      // transcript
      setCaptions((prev) => {
        const next = [...prev];
        const last = next[next.length - 1];
        if (last && !last.final && last.speaker === ev.speaker) {
          next[next.length - 1] = { ...last, text: ev.text, final: ev.type === 'final' };
        } else {
          next.push({ id: ++captionSeq, speaker: ev.speaker, text: ev.text, final: ev.type === 'final' });
        }
        return next.slice(-50);
      });
    });
    socketRef.current = ws;

    await new Promise<void>((resolve, reject) => {
      ws.onopen = () => resolve();
      ws.onerror = () => reject(new Error('voice socket failed'));
    });

    captureRef.current = await startPcmCapture(micStream, (chunk) => {
      if (ws.readyState === WebSocket.OPEN) ws.send(chunk);
    });
  }, []);

  /** Acquire mic, build mixer graph, register with PeerJS broker. */
  const initialize = useCallback(async () => {
    try {
      const micStream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      });
      micStreamRef.current = micStream;
      graphRef.current = createCallAudioGraph(micStream);

      const suffix = Math.random().toString(36).slice(2, 8);
      const peer = new Peer(`bancobranza-${suffix}`, { debug: 1 });
      peerRef.current = peer;

      peer.on('open', (id) => {
        setMyPeerId(id);
        setStatus('ready');
      });
      peer.on('call', (incoming) => {
        // Auto-answer with our mixed outgoing stream
        incoming.answer(graphRef.current!.outgoingStream);
        wireCall(incoming);
      });
      peer.on('error', (err) => {
        showErrorToast(`Peer error: ${err.type}`);
        if (err.type === 'peer-unavailable') setStatus('ready');
      });

      await startVoicePipeline(micStream, roomId.trim());
    } catch (e) {
      showErrorToast(e instanceof Error ? e.message : 'Could not access microphone');
      cleanup();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [roomId, startVoicePipeline, cleanup]);

  const wireCall = (call: MediaConnection) => {
    callRef.current = call;
    setStatus('in-call');
    call.on('stream', (remote) => {
      if (remoteAudioRef.current) {
        remoteAudioRef.current.srcObject = remote;
        void remoteAudioRef.current.play().catch(() => undefined);
      }
    });
    call.on('close', () => {
      setStatus('ready');
      callRef.current = null;
    });
    call.on('error', () => {
      setStatus('ready');
      callRef.current = null;
    });
  };

  const placeCall = () => {
    const peer = peerRef.current;
    const graph = graphRef.current;
    const target = remotePeerId.trim();
    if (!peer || !graph || !target) return;
    setStatus('calling');
    const call = peer.call(target, graph.outgoingStream);
    wireCall(call);
  };

  const hangUp = () => {
    callRef.current?.close();
    callRef.current = null;
    setStatus('ready');
  };

  const toggleMute = () => {
    const stream = micStreamRef.current;
    if (!stream) return;
    const next = !muted;
    stream.getAudioTracks().forEach((tr) => (tr.enabled = !next));
    setMuted(next);
  };

  const copyPeerId = async () => {
    await navigator.clipboard.writeText(myPeerId);
    showSuccessToast(t('call.idCopied'));
  };

  const speak = async () => {
    const text = ttsText.trim();
    if (!text || ttsBusy) return;
    setTtsBusy(true);
    try {
      if (graphRef.current) {
        await graphRef.current.playTts(text);
      } else {
        await speakWithWebSpeech(text);
      }
      setTtsText('');
    } catch {
      // Backend TTS unavailable -> browser fallback (local only)
      await speakWithWebSpeech(text);
      setTtsText('');
      showErrorToast(t('call.ttsFallback'));
    } finally {
      setTtsBusy(false);
    }
  };

  const emotionStyle = EMOTION_STYLES[emotion?.label ?? 'silent'];

  return (
    <div className="space-y-6">
      <PageHeader title={t('call.title')} description={t('call.description')} />

      {distressAlert && (
        <div className="flex items-center gap-3 rounded-lg border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          <span className="font-medium">{t('call.distressAlert')}</span>
          <Button
            variant="ghost"
            size="sm"
            className="ml-auto h-7 text-destructive"
            onClick={() => setDistressAlert(false)}
          >
            {t('common.confirm')}
          </Button>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-5">
        {/* ---- Left column: call controls ---- */}
        <Card className="lg:col-span-2 overflow-hidden">
          <CardHeader className="border-b bg-muted/30">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Phone className="h-4 w-4" />
              </div>
              <div>
                <CardTitle className="text-base">{t('call.controls')}</CardTitle>
                <CardDescription className="text-xs">
                  {status === 'idle' && t('call.statusIdle')}
                  {status === 'ready' && t('call.statusReady')}
                  {status === 'calling' && t('call.statusCalling')}
                  {status === 'in-call' && t('call.statusInCall')}
                </CardDescription>
              </div>
              <Badge
                variant={status === 'in-call' ? 'default' : 'secondary'}
                className="ml-auto capitalize"
              >
                {status === 'in-call' && <Radio className="h-3 w-3 mr-1 animate-pulse" />}
                {status}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4 pt-6">
            {status === 'idle' ? (
              <>
                <div className="space-y-2">
                  <label className="text-sm font-medium">{t('call.roomLabel')}</label>
                  <Input
                    placeholder={t('call.roomPlaceholder')}
                    value={roomId}
                    onChange={(e) => setRoomId(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">{t('call.roomHint')}</p>
                </div>
                <Button className="w-full" onClick={initialize}>
                  <Mic className="mr-2 h-4 w-4" />
                  {t('call.start')}
                </Button>
              </>
            ) : (
              <>
                <div className="space-y-2">
                  <label className="text-sm font-medium">{t('call.yourId')}</label>
                  <div className="flex gap-2">
                    <Input readOnly value={myPeerId} className="font-mono text-xs" />
                    <Button variant="outline" size="icon" onClick={copyPeerId}>
                      <Copy className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">{t('call.remoteId')}</label>
                  <Input
                    placeholder="bancobranza-xxxxxx"
                    value={remotePeerId}
                    onChange={(e) => setRemotePeerId(e.target.value)}
                    className="font-mono text-xs"
                    disabled={status === 'in-call'}
                  />
                </div>

                <div className="flex gap-2">
                  {status !== 'in-call' ? (
                    <Button
                      className="flex-1"
                      onClick={placeCall}
                      disabled={!remotePeerId.trim() || status === 'calling'}
                    >
                      <Phone className="mr-2 h-4 w-4" />
                      {t('call.call')}
                    </Button>
                  ) : (
                    <Button variant="destructive" className="flex-1" onClick={hangUp}>
                      <PhoneOff className="mr-2 h-4 w-4" />
                      {t('call.hangUp')}
                    </Button>
                  )}
                  <Button variant={muted ? 'destructive' : 'outline'} size="icon" onClick={toggleMute}>
                    {muted ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
                  </Button>
                </div>

                <Button variant="ghost" className="w-full text-muted-foreground" onClick={cleanup}>
                  {t('call.stopSession')}
                </Button>
              </>
            )}

            {sttEnabled === false && status !== 'idle' && (
              <p className="text-xs text-amber-600 dark:text-amber-400">
                {t('call.sttUnavailable')}
              </p>
            )}

            {/* ---- Emotion strip ---- */}
            {status !== 'idle' && (
              <div className="rounded-lg border p-4 space-y-3">
                <div className="flex items-center gap-2">
                  <Activity className={`h-4 w-4 ${emotionStyle.color}`} />
                  <span className="text-sm font-medium">{t('call.emotionTitle')}</span>
                  <Badge variant="outline" className={`ml-auto capitalize ${emotionStyle.color}`}>
                    {emotion?.label ?? 'silent'}
                  </Badge>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>{t('call.arousal')}</span>
                    <span className="tabular-nums">{((emotion?.arousal ?? 0) * 100).toFixed(0)}%</span>
                  </div>
                  <Progress value={(emotion?.arousal ?? 0) * 100} />
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>{t('call.valence')}</span>
                    <span className="tabular-nums">{((emotion?.valence ?? 0.5) * 100).toFixed(0)}%</span>
                  </div>
                  <Progress value={(emotion?.valence ?? 0.5) * 100} />
                </div>
                <p className="text-[10px] text-muted-foreground leading-snug">
                  {t('call.emotionDisclaimer')}
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* ---- Right column: captions + TTS ---- */}
        <div className="lg:col-span-3 space-y-6">
          <Card className="overflow-hidden">
            <CardHeader className="border-b bg-muted/30">
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-chart-2/15 text-chart-2">
                  <Captions className="h-4 w-4" />
                </div>
                <div>
                  <CardTitle className="text-base">{t('call.captionsTitle')}</CardTitle>
                  <CardDescription className="text-xs">{t('call.captionsDescription')}</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-4">
              <div className="h-72 overflow-y-auto space-y-2 pr-1">
                {captions.length === 0 ? (
                  <div className="flex h-full flex-col items-center justify-center gap-2 text-muted-foreground">
                    <Captions className="h-8 w-8 opacity-40" />
                    <p className="text-sm">{t('call.noCaptions')}</p>
                  </div>
                ) : (
                  captions.map((line) => (
                    <div key={line.id} className="flex items-start gap-2">
                      <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                        <User className="h-3 w-3" />
                      </div>
                      <p
                        className={
                          line.final
                            ? 'text-sm leading-relaxed'
                            : 'text-sm leading-relaxed italic text-muted-foreground'
                        }
                      >
                        {line.text}
                        {line.final && line.speaker && (
                          <span className="sr-only">({line.speaker})</span>
                        )}
                      </p>
                    </div>
                  ))
                )}
                <div ref={captionsEndRef} />
              </div>
            </CardContent>
          </Card>

          <Card className="overflow-hidden">
            <CardHeader className="border-b bg-muted/30">
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                  <Volume2 className="h-4 w-4" />
                </div>
                <div>
                  <CardTitle className="text-base">{t('call.ttsTitle')}</CardTitle>
                  <CardDescription className="text-xs">{t('call.ttsDescription')}</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="pt-4 space-y-3">
              <Textarea
                placeholder={t('call.ttsPlaceholder')}
                value={ttsText}
                onChange={(e) => setTtsText(e.target.value)}
                rows={3}
              />
              <Button onClick={speak} disabled={!ttsText.trim() || ttsBusy}>
                <Volume2 className="mr-2 h-4 w-4" />
                {ttsBusy ? t('call.speaking') : t('call.speak')}
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Hidden element that renders the remote peer's audio */}
      <audio ref={remoteAudioRef} autoPlay className="hidden" />
    </div>
  );
}
