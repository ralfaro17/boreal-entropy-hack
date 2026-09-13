import { useCallback, useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router';
import Peer, { type MediaConnection } from 'peerjs';
import { useTranslation } from 'react-i18next';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { customerPeerId } from '@/lib/voice';
import { customersApi, type Customer } from '@/lib/api';
import { Phone, PhoneOff, PhoneIncoming, Mic, MicOff, Radio, Snowflake } from 'lucide-react';
import { startRingtone, type RingtoneController } from '@/lib/ringtone';

type PortalStatus = 'connecting' | 'waiting' | 'ringing' | 'in-call' | 'ended' | 'error';

/**
 * Customer-facing call portal. Registers this browser under a deterministic
 * peer id (bancobranza-cust-{customerId}) so the bank's AI agent can dial it.
 * Shows an incoming-call screen with explicit Answer / Decline.
 */
export function CustomerCallPortal() {
  const { customerId } = useParams<{ customerId: string }>();
  const { t } = useTranslation();
  const [status, setStatus] = useState<PortalStatus>('connecting');
  const [customer, setCustomer] = useState<Customer | null>(null);
  const [muted, setMuted] = useState(false);
  const [error, setError] = useState('');

  const peerRef = useRef<Peer | null>(null);
  const callRef = useRef<MediaConnection | null>(null);
  const pendingCallRef = useRef<MediaConnection | null>(null);
  const micStreamRef = useRef<MediaStream | null>(null);
  const remoteAudioRef = useRef<HTMLAudioElement | null>(null);
  const ringtoneRef = useRef<RingtoneController | null>(null);

  useEffect(() => {
    if (!customerId) return;
    customersApi.get(customerId).then(setCustomer).catch(() => setCustomer(null));
  }, [customerId]);

  useEffect(() => {
    if (!customerId) return;
    const peer = new Peer(customerPeerId(customerId), { debug: 1 });
    peerRef.current = peer;

    peer.on('open', () => setStatus('waiting'));
    peer.on('call', (incoming) => {
      pendingCallRef.current = incoming;
      setStatus('ringing');
      ringtoneRef.current?.stop();
      ringtoneRef.current = startRingtone({ mode: 'incoming', volume: 0.22 });

      incoming.on('close', () => {
        if (pendingCallRef.current === incoming) {
          ringtoneRef.current?.stop();
          ringtoneRef.current = null;
          pendingCallRef.current = null;
          setStatus('waiting');
        }
      });
    });
    peer.on('error', (err) => {
      ringtoneRef.current?.stop();
      ringtoneRef.current = null;
      if (err.type === 'unavailable-id') {
        setError(t('portalCall.idTaken'));
      } else {
        setError(`${err.type}`);
      }
      setStatus('error');
    });

    return () => {
      ringtoneRef.current?.stop();
      ringtoneRef.current = null;
      callRef.current?.close();
      micStreamRef.current?.getTracks().forEach((tr) => tr.stop());
      peer.destroy();
    };
  }, [customerId, t]);

  const answer = useCallback(async () => {
    ringtoneRef.current?.stop();
    ringtoneRef.current = null;
    const incoming = pendingCallRef.current;
    if (!incoming) return;
    try {
      const mic = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      });
      micStreamRef.current = mic;
      incoming.answer(mic);
      callRef.current = incoming;
      pendingCallRef.current = null;
      setStatus('in-call');

      incoming.on('stream', (remote) => {
        if (remoteAudioRef.current) {
          remoteAudioRef.current.srcObject = remote;
          void remoteAudioRef.current.play().catch(() => undefined);
        }
      });
      incoming.on('close', () => endCall());
      incoming.on('error', () => endCall());
    } catch {
      setError(t('portalCall.micDenied'));
      setStatus('error');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [t]);

  const decline = () => {
    ringtoneRef.current?.stop();
    ringtoneRef.current = null;
    pendingCallRef.current?.close();
    pendingCallRef.current = null;
    setStatus('waiting');
  };

  const endCall = () => {
    ringtoneRef.current?.stop();
    ringtoneRef.current = null;
    callRef.current?.close();
    callRef.current = null;
    micStreamRef.current?.getTracks().forEach((tr) => tr.stop());
    micStreamRef.current = null;
    if (remoteAudioRef.current) remoteAudioRef.current.srcObject = null;
    setStatus('ended');
  };

  const toggleMute = () => {
    const stream = micStreamRef.current;
    if (!stream) return;
    const next = !muted;
    stream.getAudioTracks().forEach((tr) => (tr.enabled = !next));
    setMuted(next);
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <Card className="w-full max-w-md overflow-hidden">
        <div className="bg-linear-to-br from-primary to-chart-2 px-6 py-8 text-center text-primary-foreground">
          <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-white/15 backdrop-blur">
            <Snowflake className="h-7 w-7" />
          </div>
          <h1 className="text-xl font-bold tracking-tight">Bancobranza</h1>
          <p className="text-sm opacity-90">{t('portalCall.subtitle')}</p>
        </div>

        <CardContent className="p-6 space-y-6 text-center">
          {customer && (
            <p className="text-sm text-muted-foreground">
              {t('portalCall.loggedInAs')} <span className="font-medium text-foreground">{customer.full_name}</span>
            </p>
          )}

          {status === 'connecting' && (
            <p className="text-muted-foreground animate-pulse">{t('portalCall.connecting')}</p>
          )}

          {status === 'waiting' && (
            <div className="space-y-2 py-6">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-muted">
                <Phone className="h-7 w-7 text-muted-foreground" />
              </div>
              <p className="font-medium">{t('portalCall.waiting')}</p>
              <p className="text-xs text-muted-foreground">{t('portalCall.waitingHint')}</p>
            </div>
          )}

          {status === 'ringing' && (
            <div className="space-y-5 py-4">
              <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-primary/10 text-primary animate-pulse">
                <PhoneIncoming className="h-9 w-9" />
              </div>
              <div>
                <p className="text-lg font-semibold">{t('portalCall.incoming')}</p>
                <p className="text-sm text-muted-foreground">{t('portalCall.incomingFrom')}</p>
              </div>
              <div className="flex justify-center gap-3">
                <Button size="lg" className="bg-emerald-600 hover:bg-emerald-700 text-white" onClick={answer}>
                  <Phone className="mr-2 h-4 w-4" />
                  {t('portalCall.answer')}
                </Button>
                <Button size="lg" variant="destructive" onClick={decline}>
                  <PhoneOff className="mr-2 h-4 w-4" />
                  {t('portalCall.decline')}
                </Button>
              </div>
            </div>
          )}

          {status === 'in-call' && (
            <div className="space-y-5 py-4">
              <Badge className="gap-1.5">
                <Radio className="h-3 w-3 animate-pulse" />
                {t('portalCall.inCall')}
              </Badge>
              <p className="text-sm text-muted-foreground">{t('portalCall.inCallHint')}</p>
              <div className="flex justify-center gap-3">
                <Button variant={muted ? 'destructive' : 'outline'} size="icon" onClick={toggleMute}>
                  {muted ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
                </Button>
                <Button variant="destructive" onClick={endCall}>
                  <PhoneOff className="mr-2 h-4 w-4" />
                  {t('portalCall.hangUp')}
                </Button>
              </div>
            </div>
          )}

          {status === 'ended' && (
            <div className="space-y-4 py-6">
              <p className="font-medium">{t('portalCall.ended')}</p>
              <Button variant="outline" onClick={() => setStatus('waiting')}>
                {t('portalCall.waitAgain')}
              </Button>
            </div>
          )}

          {status === 'error' && (
            <div className="space-y-2 py-6">
              <p className="text-destructive font-medium">{error}</p>
            </div>
          )}
        </CardContent>
      </Card>
      <audio ref={remoteAudioRef} autoPlay className="hidden" />
    </div>
  );
}
