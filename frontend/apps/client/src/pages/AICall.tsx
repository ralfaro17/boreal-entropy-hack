import { useCallback, useEffect, useRef, useState } from 'react';
import Peer, { type MediaConnection } from 'peerjs';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { PageHeader } from '@/components/page-header';
import { useCustomers } from '@/hooks/useCustomers';
import { showErrorToast } from '@/lib/toast-utils';
import {
  agentPeerId,
  createCallAudioGraph,
  customerPeerId,
  openVoiceSocket,
  startPcmCapture,
  type CallAudioGraph,
  type EmotionEvent,
  type PcmCapture,
} from '@/lib/voice';
import {
  Bot,
  Phone,
  PhoneOff,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Activity,
  AlertTriangle,
  Radio,
  User,
  Captions,
  ExternalLink,
} from 'lucide-react';
import { useNavigate, useSearchParams } from 'react-router';

type AgentStatus = 'idle' | 'dialing' | 'in-call' | 'escalated' | 'ended';

interface TurnLine {
  id: number;
  who: 'customer' | 'ai';
  text: string;
  final: boolean;
}

const EMOTION_COLORS: Record<EmotionEvent['label'], string> = {
  silent: 'text-muted-foreground',
  calm: 'text-emerald-600 dark:text-emerald-400',
  neutral: 'text-primary',
  elevated: 'text-amber-600 dark:text-amber-400',
  distressed: 'text-destructive',
};

let turnSeq = 0;

/**
 * AI outbound call console. Select a customer, click "Start AI Call":
 *   1. Dials the customer's portal (deterministic peer id boreal-cust-{id}).
 *   2. On answer, speaks a compliant reminder greeting (backend-generated).
 *   3. Captures the customer's remote audio -> /ws/stt -> on each final
 *      transcript, POST /voice/agent-reply -> TTS reply into the call.
 *   4. On distress (text or sustained vocal), the loop stops and hands off.
 */
export function AICall() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { data: customers } = useCustomers({ limit: 200 });

  const [customerId, setCustomerId] = useState(() => searchParams.get('customer') ?? '');
  const [status, setStatus] = useState<AgentStatus>('idle');
  const [turns, setTurns] = useState<TurnLine[]>([]);
  const [emotion, setEmotion] = useState<EmotionEvent | null>(null);
  const [aiSpeaking, setAiSpeaking] = useState(false);
  const [agentMicOn, setAgentMicOn] = useState(false);
  const [monitorOn, setMonitorOn] = useState(false);

  const peerRef = useRef<Peer | null>(null);
  const callRef = useRef<MediaConnection | null>(null);
  const micStreamRef = useRef<MediaStream | null>(null);
  const graphRef = useRef<CallAudioGraph | null>(null);
  const captureRef = useRef<PcmCapture | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const remoteAudioRef = useRef<HTMLAudioElement | null>(null);
  const transcriptEndRef = useRef<HTMLDivElement | null>(null);
  const busyRef = useRef(false); // half-duplex: true while AI is thinking/speaking
  const stoppedRef = useRef(false);

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [turns]);

  const cleanup = useCallback((finalStatus: AgentStatus = 'ended') => {
    stoppedRef.current = true;
    captureRef.current?.stop();
    captureRef.current = null;
    socketRef.current?.close();
    socketRef.current = null;
    callRef.current?.close();
    callRef.current = null;
    graphRef.current?.close();
    graphRef.current = null;
    micStreamRef.current?.getTracks().forEach((tr) => tr.stop());
    micStreamRef.current = null;
    peerRef.current?.destroy();
    peerRef.current = null;
    if (remoteAudioRef.current) remoteAudioRef.current.srcObject = null;
    setAiSpeaking(false);
    setStatus((prev) => (prev === 'idle' ? 'idle' : finalStatus));
  }, []);

  useEffect(() => () => cleanup(), [cleanup]);

  const addTurn = (who: TurnLine['who'], text: string, final = true) => {
    setTurns((prev) => {
      const next = [...prev];
      const last = next[next.length - 1];
      if (last && !last.final && last.who === who) {
        next[next.length - 1] = { ...last, text, final };
      } else {
        next.push({ id: ++turnSeq, who, text, final });
      }
      return next.slice(-80);
    });
  };

  /** Speak text into the call via backend TTS; disable listening while talking.
   * localMonitor=false: the AI voice reaches the agent through the portal side;
   * playing it locally too causes an echo/double-audio effect. */
  const speak = useCallback(async (text: string, language = 'es') => {
    if (!graphRef.current) return;
    setAiSpeaking(true);
    try {
      await graphRef.current.playTts(text, { language, localMonitor: false });
    } catch {
      showErrorToast(t('aiCall.ttsError'));
    } finally {
      setAiSpeaking(false);
    }
  }, [t]);

  /** One agent turn: customer's final transcript -> LLM reply -> TTS. */
  const handleCustomerUtterance = useCallback(async (text: string, custId: string) => {
    if (busyRef.current || stoppedRef.current) return;
    busyRef.current = true;
    try {
      const res = await fetch('/voice/agent-reply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ customer_id: custId, message: text }),
      });
      if (!res.ok) throw new Error(`agent-reply ${res.status}`);
      const data: { reply: string; escalated: boolean; language?: string } = await res.json();
      addTurn('ai', data.reply);
      await speak(data.reply, data.language ?? 'es');
      if (data.escalated) {
        setStatus('escalated');
        stoppedRef.current = true; // freeze the loop; human takes over
      }
    } catch {
      showErrorToast(t('aiCall.replyError'));
    } finally {
      busyRef.current = false;
    }
  }, [speak, t]);

  const startCall = useCallback(async () => {
    const custId = customerId;
    if (!custId) return;
    stoppedRef.current = false;
    setTurns([]);
    setEmotion(null);
    setStatus('dialing');

    try {
      // Mic is required by getUserMedia/WebRTC even though the agent mostly
      // listens. It starts MUTED: an open agent mic re-captures room audio and
      // causes echo/doubled voices (especially when demoing on one machine).
      // The supervisor can unmute to barge in.
      const mic = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      });
      mic.getAudioTracks().forEach((tr) => (tr.enabled = false));
      setAgentMicOn(false);
      micStreamRef.current = mic;
      graphRef.current = createCallAudioGraph(mic);

      const peer = new Peer(agentPeerId(), { debug: 1 });
      peerRef.current = peer;

      peer.on('error', (err) => {
        if (err.type === 'peer-unavailable') {
          showErrorToast(t('aiCall.customerOffline'));
          cleanup('idle');
          setStatus('idle');
        } else {
          showErrorToast(`Peer error: ${err.type}`);
        }
      });

      await new Promise<void>((resolve, reject) => {
        peer.on('open', () => resolve());
        peer.on('error', reject);
      });

      const call = peer.call(customerPeerId(custId), graphRef.current.outgoingStream);
      callRef.current = call;

      call.on('stream', (remote) => {
        void (async () => {
          setStatus('in-call');
          if (remoteAudioRef.current) {
            remoteAudioRef.current.srcObject = remote;
            remoteAudioRef.current.muted = true; // monitor off by default (echo prevention)
            void remoteAudioRef.current.play().catch(() => undefined);
          }
          setMonitorOn(false);

          // STT + emotion over the *customer's* remote audio.
          // persist=false: /voice/agent-reply persists each utterance itself.
          const ws = openVoiceSocket(custId, 'customer', (ev) => {
            if (ev.type === 'emotion') {
              setEmotion(ev);
              return;
            }
            if (ev.type === 'partial' || ev.type === 'final') {
              // Ignore the customer's echo of AI speech while the AI is talking
              if (busyRef.current || stoppedRef.current) return;
              addTurn('customer', ev.text, ev.type === 'final');
              if (ev.type === 'final') {
                void handleCustomerUtterance(ev.text, custId);
              }
            }
          }, { persist: false });
          socketRef.current = ws;
          await new Promise<void>((resolve) => {
            ws.onopen = () => resolve();
            ws.onerror = () => resolve();
          });
          captureRef.current = await startPcmCapture(remote, (chunk) => {
            if (ws.readyState === WebSocket.OPEN) ws.send(chunk);
          });

          // Opening line: compliant AI reminder greeting (Spanish-first)
          try {
            const res = await fetch(`/voice/greeting/${custId}`);
            if (res.ok) {
              const { greeting, language } = await res.json();
              addTurn('ai', greeting);
              await speak(greeting, language ?? 'es');
            }
          } catch {
            // greeting failure is non-fatal; agent will respond reactively
          }
        })();
      });

      call.on('close', () => {
        if (!stoppedRef.current) cleanup('ended');
      });
    } catch (e) {
      showErrorToast(e instanceof Error ? e.message : 'Failed to start call');
      cleanup('idle');
      setStatus('idle');
    }
  }, [customerId, cleanup, handleCustomerUtterance, speak, t]);

  const hangUp = () => cleanup('ended');

  const toggleAgentMic = () => {
    const stream = micStreamRef.current;
    if (!stream) return;
    const next = !agentMicOn;
    stream.getAudioTracks().forEach((tr) => (tr.enabled = next));
    setAgentMicOn(next);
  };

  /** Local playback of the customer's audio. OFF by default: when demoing on
   * one machine it replays the speaker's own voice (perceived as echo). STT
   * capture is unaffected — it taps the stream directly, not the audio element. */
  const toggleMonitor = () => {
    const next = !monitorOn;
    if (remoteAudioRef.current) remoteAudioRef.current.muted = !next;
    setMonitorOn(next);
  };

  const selectedCustomer = customers?.find((c) => c.id === customerId);
  const portalPath = customerId ? `/portal/call/${customerId}` : '';
  const emotionColor = EMOTION_COLORS[emotion?.label ?? 'silent'];
  const inSession = status === 'dialing' || status === 'in-call' || status === 'escalated';

  return (
    <div className="space-y-6">
      <PageHeader title={t('aiCall.title')} description={t('aiCall.description')} />

      {status === 'escalated' && (
        <div className="flex items-center gap-3 rounded-lg border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          <span className="font-medium">{t('aiCall.escalatedBanner')}</span>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-5">
        {/* ---- Control column ---- */}
        <Card className="lg:col-span-2 overflow-hidden">
          <CardHeader className="border-b bg-muted/30">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Bot className="h-4 w-4" />
              </div>
              <div>
                <CardTitle className="text-base">{t('aiCall.agentTitle')}</CardTitle>
                <CardDescription className="text-xs">
                  {status === 'idle' && t('aiCall.statusIdle')}
                  {status === 'dialing' && t('aiCall.statusDialing')}
                  {status === 'in-call' && (aiSpeaking ? t('aiCall.statusSpeaking') : t('aiCall.statusListening'))}
                  {status === 'escalated' && t('aiCall.statusEscalated')}
                  {status === 'ended' && t('aiCall.statusEnded')}
                </CardDescription>
              </div>
              <Badge
                variant={status === 'in-call' ? 'default' : status === 'escalated' ? 'destructive' : 'secondary'}
                className="ml-auto capitalize"
              >
                {status === 'in-call' && <Radio className="h-3 w-3 mr-1 animate-pulse" />}
                {status}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4 pt-6">
            <div className="space-y-2">
              <label className="text-sm font-medium">{t('aiCall.selectCustomer')}</label>
              <Select
                value={customerId || undefined}
                onValueChange={(v) => setCustomerId(v ?? '')}
              >
                <SelectTrigger className="w-full" disabled={inSession}>
                  <SelectValue placeholder={t('aiCall.selectPlaceholder')} />
                </SelectTrigger>
                <SelectContent>
                  {customers?.map((c) => (
                    <SelectItem key={c.id} value={c.id}>
                      {c.full_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {customerId && !inSession && (
              <div className="rounded-lg border bg-muted/30 p-3 space-y-1.5">
                <p className="text-xs font-medium">{t('aiCall.portalHintTitle')}</p>
                <p className="text-xs text-muted-foreground">{t('aiCall.portalHint')}</p>
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full"
                  onClick={() => window.open(portalPath, '_blank')}
                >
                  <ExternalLink className="mr-2 h-3.5 w-3.5" />
                  {t('aiCall.openPortal')}
                </Button>
              </div>
            )}

            {!inSession ? (
              <Button className="w-full" onClick={startCall} disabled={!customerId}>
                <Phone className="mr-2 h-4 w-4" />
                {t('aiCall.startCall')}
              </Button>
            ) : (
              <div className="flex gap-2">
                <Button variant="destructive" className="flex-1" onClick={hangUp}>
                  <PhoneOff className="mr-2 h-4 w-4" />
                  {t('aiCall.endCall')}
                </Button>
                <Button
                  variant={agentMicOn ? 'default' : 'outline'}
                  size="icon"
                  onClick={toggleAgentMic}
                  title={agentMicOn ? t('aiCall.micOn') : t('aiCall.micOff')}
                >
                  {agentMicOn ? <Mic className="h-4 w-4" /> : <MicOff className="h-4 w-4" />}
                </Button>
                <Button
                  variant={monitorOn ? 'default' : 'outline'}
                  size="icon"
                  onClick={toggleMonitor}
                  title={monitorOn ? t('aiCall.monitorOn') : t('aiCall.monitorOff')}
                >
                  {monitorOn ? <Volume2 className="h-4 w-4" /> : <VolumeX className="h-4 w-4" />}
                </Button>
              </div>
            )}
            {inSession && (
              <p className="text-[10px] text-muted-foreground leading-snug">
                {agentMicOn ? t('aiCall.micOnHint') : t('aiCall.micOffHint')}{' '}
                {monitorOn ? t('aiCall.monitorOnHint') : t('aiCall.monitorOffHint')}
              </p>
            )}

            {status === 'escalated' && selectedCustomer && (
              <Button
                variant="outline"
                className="w-full"
                onClick={() => navigate(`/customers/${selectedCustomer.id}`)}
              >
                <User className="mr-2 h-4 w-4" />
                {t('aiCall.viewCustomer')}
              </Button>
            )}

            {/* Emotion strip */}
            {inSession && (
              <div className="rounded-lg border p-4 space-y-3">
                <div className="flex items-center gap-2">
                  <Activity className={`h-4 w-4 ${emotionColor}`} />
                  <span className="text-sm font-medium">{t('call.emotionTitle')}</span>
                  <Badge variant="outline" className={`ml-auto capitalize ${emotionColor}`}>
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

        {/* ---- Conversation column ---- */}
        <Card className="lg:col-span-3 overflow-hidden">
          <CardHeader className="border-b bg-muted/30">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-chart-2/15 text-chart-2">
                <Captions className="h-4 w-4" />
              </div>
              <div>
                <CardTitle className="text-base">{t('aiCall.liveConversation')}</CardTitle>
                <CardDescription className="text-xs">{t('aiCall.liveConversationHint')}</CardDescription>
              </div>
              {aiSpeaking && (
                <Badge variant="secondary" className="ml-auto gap-1.5">
                  <Bot className="h-3 w-3 animate-pulse" />
                  {t('aiCall.speakingBadge')}
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent className="p-4">
            <div className="h-105 overflow-y-auto space-y-3 pr-1">
              {turns.length === 0 ? (
                <div className="flex h-full flex-col items-center justify-center gap-2 text-muted-foreground">
                  <Bot className="h-8 w-8 opacity-40" />
                  <p className="text-sm">{t('aiCall.noTurns')}</p>
                </div>
              ) : (
                turns.map((turn) => (
                  <div
                    key={turn.id}
                    className={`flex flex-col ${turn.who === 'ai' ? 'items-start' : 'items-end'}`}
                  >
                    <div className="flex items-center gap-1.5 mb-1 px-1">
                      {turn.who === 'ai' ? (
                        <>
                          <Bot className="h-3.5 w-3.5 text-primary" />
                          <span className="text-xs font-medium text-primary">Payment Assistant</span>
                        </>
                      ) : (
                        <>
                          <span className="text-xs font-medium text-muted-foreground">
                            {selectedCustomer?.full_name ?? 'Customer'}
                          </span>
                          <User className="h-3.5 w-3.5 text-muted-foreground" />
                        </>
                      )}
                    </div>
                    <div
                      className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm shadow-sm ${
                        turn.who === 'ai'
                          ? 'bg-muted text-foreground rounded-tl-sm border'
                          : turn.final
                          ? 'bg-linear-to-br from-primary to-chart-2 text-primary-foreground rounded-tr-sm'
                          : 'bg-primary/20 text-foreground rounded-tr-sm italic'
                      }`}
                    >
                      <p className="whitespace-pre-wrap leading-relaxed">{turn.text}</p>
                    </div>
                  </div>
                ))
              )}
              <div ref={transcriptEndRef} />
            </div>
          </CardContent>
        </Card>
      </div>

      <audio ref={remoteAudioRef} autoPlay className="hidden" />
    </div>
  );
}
