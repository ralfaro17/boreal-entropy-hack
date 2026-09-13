import { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router';
import { useTranslation } from 'react-i18next';
import { useCustomer } from '@/hooks/useCustomers';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Card } from '@/components/ui/card';
import {
  Send,
  Bot,
  User,
  ShieldCheck,
  AlertCircle,
  RefreshCw,
  Sparkles,
  ArrowLeft,
  Lock,
  MessageSquare,
} from 'lucide-react';

interface ChatMessage {
  id?: string;
  room_id?: string;
  sender_name: string;
  text: string;
  type?: string;
  timestamp?: string;
  was_flagged?: boolean;
}

export function CustomerChat() {
  const { customerId } = useParams<{ customerId: string }>();
  const navigate = useNavigate();
  const { i18n } = useTranslation();

  const isSpanish = i18n.language.startsWith('es');

  // Customer data lookup
  const { data: customer, isLoading: loadingCustomer } = useCustomer(customerId || '');

  const customerName = customer?.full_name || 'Customer';
  const customerNameRef = useRef(customerName);
  customerNameRef.current = customerName;

  // WebSocket and messages state
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(true);
  const [hasEscalated, setHasEscalated] = useState(false);
  const [isWaitingForAssistant, setIsWaitingForAssistant] = useState(false);

  const socketRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isWaitingForAssistant]);

  // Connect WebSocket
  useEffect(() => {
    if (!customerId) return;

    let isMounted = true;
    setIsConnecting(true);

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/chat/${customerId}?sender_name=Customer`;

    const ws = new WebSocket(wsUrl);
    socketRef.current = ws;

    ws.onopen = () => {
      if (!isMounted) return;
      setIsConnected(true);
      setIsConnecting(false);
    };

    ws.onmessage = (event) => {
      if (!isMounted) return;
      try {
        const data = JSON.parse(event.data);

        if (data.type === 'history' && Array.isArray(data.messages)) {
          setMessages(data.messages);
          // Check if any message indicates escalation
          const containsEscalation = data.messages.some(
            (m: ChatMessage) =>
              m.text.includes('especialista') || m.text.includes('specialist')
          );
          if (containsEscalation) {
            setHasEscalated(true);
          }
        } else if (data.type === 'message') {
          const isCustomer =
            data.sender_name?.toLowerCase() === 'you' ||
            data.sender_name?.toLowerCase() === 'customer' ||
            data.sender_name === customerNameRef.current;

          setMessages((prev) => {
            // Avoid duplicate appends if message already exists with same real server ID
            if (data.id && prev.some((m) => m.id === data.id)) {
              return prev;
            }

            // If this is the server confirmation of the user's optimistic message,
            // reconcile by replacing the temporary message with the confirmed server message
            if (isCustomer) {
              const tempIndex = prev.findIndex(
                (m) => m.id?.startsWith('temp-') && m.text.trim() === data.text.trim()
              );
              if (tempIndex !== -1) {
                const updated = [...prev];
                updated[tempIndex] = data;
                return updated;
              }
            }

            return [...prev, data];
          });

          // If the message is from the assistant, hide the thinking indicator
          if (!isCustomer) {
            setIsWaitingForAssistant(false);
          } else {
            // User message confirmed; assistant is currently generating response
            setIsWaitingForAssistant(true);
          }

          if (
            data.text.includes('especialista') ||
            data.text.includes('specialist')
          ) {
            setHasEscalated(true);
          }
        }
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
      }
    };

    ws.onclose = () => {
      if (!isMounted) return;
      setIsConnected(false);
      setIsConnecting(false);
    };

    ws.onerror = () => {
      if (!isMounted) return;
      setIsConnected(false);
      setIsConnecting(false);
    };

    return () => {
      isMounted = false;
      if (ws.readyState === WebSocket.OPEN) {
        ws.close(1000, 'Component unmounted');
      } else if (ws.readyState === WebSocket.CONNECTING) {
        ws.onopen = () => {
          ws.close(1000, 'Component unmounted');
        };
      }
    };
  }, [customerId]);

  const handleSendMessage = (textToSend?: string) => {
    const text = (textToSend || inputMessage).trim();
    if (!text || !socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      return;
    }

    const currentSender = customerNameRef.current || 'Customer';
    const tempId = `temp-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;

    const optimisticMessage: ChatMessage = {
      id: tempId,
      room_id: customerId,
      sender_name: currentSender,
      text,
      type: 'message',
      timestamp: new Date().toISOString(),
    };

    // 1. Inmediately display user message for immediate visual feedback
    setMessages((prev) => [...prev, optimisticMessage]);

    // 2. Clear the input immediately
    setInputMessage('');

    // 3. Inmediately show the LLM thinking/writing indicator
    setIsWaitingForAssistant(true);

    // 4. Transmit payload over WebSocket
    const payload = {
      text,
      sender_name: currentSender,
    };
    socketRef.current.send(JSON.stringify(payload));
  };


  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const reconnect = () => {
    if (socketRef.current) {
      socketRef.current.close();
    }
    setIsConnecting(true);
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/chat/${customerId}?sender_name=${encodeURIComponent(
      customerName
    )}`;
    const ws = new WebSocket(wsUrl);
    socketRef.current = ws;
  };

  // Quick suggestions for rapid user response testing
  const suggestions = isSpanish
    ? [
        'Hola, ¿puedo acordar un plan de pagos flexibles?',
        'Ya realicé mi abono por transferencia hoy.',
        'Lamentablemente perdí mi empleo este mes y no puedo pagar.',
        'Tuve una emergencia médica y gastos imprevistos.',
      ]
    : [
        'Hi, could we arrange a flexible payment schedule?',
        'I already sent my installment payment today via transfer.',
        'Unfortunately I lost my job this month and cannot afford this.',
        'I had an unexpected medical emergency this week.',
      ];

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return '';
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  };

  if (!customerId) {
    return (
      <div className="flex h-screen items-center justify-center p-4">
        <Card className="max-w-md p-6 text-center space-y-4">
          <AlertCircle className="h-10 w-10 text-destructive mx-auto" />
          <h2 className="text-lg font-bold">Customer ID Missing</h2>
          <p className="text-sm text-muted-foreground">
            Please provide a valid customer ID in the URL to connect to the chat room.
          </p>
          <Button onClick={() => navigate('/chat')}>Go to Console</Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-slate-50 dark:bg-slate-950">
      {/* Top Banking Customer Portal Header */}
      <header className="border-b bg-card px-4 py-3 shrink-0 shadow-xs">
        <div className="max-w-4xl mx-auto flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm">
              <ShieldCheck className="h-6 w-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="font-semibold text-sm sm:text-base leading-tight">
                  Bancobranza • {isSpanish ? 'Asistencia Financiera' : 'Financial Support'}
                </h1>
                <Badge
                  variant="outline"
                  className="hidden sm:flex text-[10px] items-center gap-1 py-0 px-2 border-emerald-500/30 text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/30"
                >
                  <Lock className="h-2.5 w-2.5" />
                  {isSpanish ? 'Canal Seguro' : 'Secure Channel'}
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                {isSpanish ? 'Atención al Cliente y Prevención de Endeudamiento' : 'Customer Care & Debt Prevention'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            {/* Connection status badge */}
            {isConnecting ? (
              <Badge variant="secondary" className="text-xs gap-1 py-1">
                <RefreshCw className="h-3 w-3 animate-spin" />
                <span className="hidden sm:inline">{isSpanish ? 'Conectando...' : 'Connecting...'}</span>
              </Badge>
            ) : isConnected ? (
              <Badge
                variant="outline"
                className="text-xs gap-1.5 py-1 border-emerald-500/40 text-emerald-600 dark:text-emerald-400 bg-emerald-500/10"
              >
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                <span className="hidden sm:inline">{isSpanish ? 'En vivo' : 'Online'}</span>
              </Badge>
            ) : (
              <Button
                variant="outline"
                size="sm"
                onClick={reconnect}
                className="text-xs gap-1.5 h-7 text-destructive hover:bg-destructive/10"
              >
                <RefreshCw className="h-3 w-3" />
                {isSpanish ? 'Reconectar' : 'Reconnect'}
              </Button>
            )}

            {/* Quick link back to Internal Operator Console */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/chat')}
              className="text-xs gap-1 text-muted-foreground hover:text-foreground h-8"
              title="Return to Internal Risk Console"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              <span className="hidden md:inline">{isSpanish ? 'Consola' : 'Console'}</span>
            </Button>
          </div>
        </div>
      </header>

      {/* Customer Identity Banner */}
      <div className="bg-primary/5 border-b px-4 py-2 text-xs">
        <div className="max-w-4xl mx-auto flex items-center justify-between text-muted-foreground">
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-primary" />
            <span>
              {isSpanish ? 'Sesión de cliente verificada:' : 'Verified customer session:'}{' '}
              {loadingCustomer ? (
                <Skeleton className="inline-block h-3.5 w-24 align-middle" />
              ) : (
                <strong className="text-foreground font-semibold">{customerName}</strong>
              )}
            </span>
            {customer?.email && (
              <span className="hidden sm:inline text-muted-foreground/80">({customer.email})</span>
            )}
          </div>
          <span className="text-[11px] font-mono text-muted-foreground">ID: {customerId.slice(0, 8)}...</span>
        </div>
      </div>

      {/* Chat Messages Body */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-4xl mx-auto space-y-4">
          {/* Welcome Announcement Card */}
          <div className="text-center py-4 px-6 rounded-2xl bg-card border shadow-2xs max-w-xl mx-auto space-y-1.5">
            <div className="inline-flex p-2 rounded-xl bg-primary/10 text-primary mb-1">
              <MessageSquare className="h-5 w-5" />
            </div>
            <h3 className="font-semibold text-sm">
              {isSpanish ? 'Canal Oficial de Apoyo y Pagos Bancobranza' : 'Official Bancobranza Payment & Support Channel'}
            </h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              {isSpanish
                ? 'Este espacio confidencial te permite gestionar tus pagos, consultar fechas de vencimiento y solicitar planes de apoyo financiero sin sanciones.'
                : 'This confidential space allows you to manage payments, review due dates, and explore flexible arrangements without penalties.'}
            </p>
          </div>

          {/* Escalation Alert Banner */}
          {hasEscalated && (
            <div className="rounded-xl border border-primary/30 bg-primary/10 p-3.5 flex items-start gap-3 text-xs text-foreground max-w-2xl mx-auto animate-in fade-in">
              <Sparkles className="h-4 w-4 text-primary shrink-0 mt-0.5" />
              <div>
                <strong className="font-semibold block mb-0.5">
                  {isSpanish ? 'Atención especializada asignada' : 'Specialist Assistance Assigned'}
                </strong>
                <p className="text-muted-foreground leading-relaxed">
                  {isSpanish
                    ? 'Hemos tomado nota de tu situación. Un asesor de nuestro equipo de apoyo financiero revisará alternativas flexibles para ti.'
                    : 'We have noted your situation. A specialist from our financial support team will follow up with flexible alternatives.'}
                </p>
              </div>
            </div>
          )}

          {/* Message List */}
          {messages.length === 0 ? (
            <div className="text-center py-12 text-sm text-muted-foreground">
              {isSpanish
                ? 'Inicia la conversación escribiendo abajo...'
                : 'Start the conversation by typing below...'}
            </div>
          ) : (
            messages.map((msg, index) => {
              const isCustomer =
                msg.sender_name.toLowerCase() === 'you' ||
                msg.sender_name.toLowerCase() === 'customer' ||
                msg.sender_name === customerName;

              return (
                <div
                  key={msg.id || index}
                  className={`flex flex-col ${isCustomer ? 'items-end' : 'items-start'}`}
                >
                  <div className="flex items-center gap-1.5 mb-1 px-1 text-xs">
                    {isCustomer ? (
                      <>
                        <span className="font-medium text-foreground">{customerName}</span>
                        <div className="h-4 w-4 rounded-full bg-primary/20 flex items-center justify-center text-[9px] font-bold text-primary">
                          <User className="h-3 w-3" />
                        </div>
                      </>
                    ) : (
                      <>
                        <div className="h-4 w-4 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                          <Bot className="h-3 w-3" />
                        </div>
                        <span className="font-medium text-primary">
                          {msg.sender_name || 'Payment Assistant'}
                        </span>
                      </>
                    )}
                  </div>

                  <div
                    className={`max-w-[85%] sm:max-w-xl rounded-2xl px-4 py-3 text-sm shadow-2xs leading-relaxed ${
                      isCustomer
                        ? 'bg-primary text-primary-foreground rounded-tr-xs'
                        : 'bg-card border text-card-foreground rounded-tl-xs'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{msg.text}</p>
                    {msg.was_flagged && (
                      <div className="mt-2 pt-2 border-t border-destructive/30 flex items-center gap-1 text-[11px] text-destructive font-medium">
                        <AlertCircle className="h-3 w-3" />
                        {isSpanish
                          ? 'Identificado para revisión de especialista'
                          : 'Identified for specialist review'}
                      </div>
                    )}
                  </div>

                  {msg.timestamp && (
                    <span className="text-[10px] text-muted-foreground px-1 mt-1">
                      {formatTimestamp(msg.timestamp)}
                    </span>
                  )}
                </div>
              );
            })
          )}

          {/* Assistant Thinking / Writing Indicator */}
          {isWaitingForAssistant && (
            <div className="flex flex-col items-start animate-in fade-in slide-in-from-bottom-2 duration-200">
              <div className="flex items-center gap-1.5 mb-1 px-1 text-xs">
                <div className="h-4 w-4 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                  <Bot className="h-3 w-3" />
                </div>
                <span className="font-medium text-primary">Payment Assistant</span>
              </div>
              <div className="bg-card border text-card-foreground rounded-2xl rounded-tl-xs px-4 py-3 shadow-xs flex items-center gap-3">
                <div className="flex items-center gap-1">
                  <span className="h-2 w-2 rounded-full bg-primary animate-bounce [animation-delay:-0.3s]" />
                  <span className="h-2 w-2 rounded-full bg-primary animate-bounce [animation-delay:-0.15s]" />
                  <span className="h-2 w-2 rounded-full bg-primary animate-bounce" />
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground border-l pl-3">
                  <Sparkles className="h-3.5 w-3.5 text-primary animate-pulse shrink-0" />
                  <span>
                    {isSpanish
                      ? 'El asistente con IA está analizando tu mensaje y redactando una respuesta...'
                      : 'AI Assistant is thinking and drafting a response...'}
                  </span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Suggestion Chips & Input Footer */}
      <footer className="border-t bg-card p-3 sm:p-4 shrink-0">
        <div className="max-w-4xl mx-auto space-y-3">
          {/* Suggestion quick replies */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs no-scrollbar">
            <span className="text-muted-foreground shrink-0 text-[11px] flex items-center gap-1 mr-1">
              <Sparkles className="h-3 w-3 text-primary" />
              {isSpanish ? 'Sugerencias:' : 'Suggestions:'}
            </span>
            {suggestions.map((suggestion, idx) => (
              <Button
                key={idx}
                variant="outline"
                size="sm"
                className="h-7 text-[11px] shrink-0 rounded-full bg-background hover:bg-primary/10 hover:text-primary transition-colors"
                onClick={() => handleSendMessage(suggestion)}
                disabled={!isConnected}
              >
                {suggestion}
              </Button>
            ))}
          </div>

          {/* Input and Send button */}
          <div className="flex items-center gap-2">
            <Input
              placeholder={
                isWaitingForAssistant
                  ? isSpanish
                    ? 'El asistente está redactando una respuesta...'
                    : 'Assistant is drafting a response...'
                  : isSpanish
                  ? 'Escribe tu respuesta a la entidad bancaria...'
                  : 'Type your response to the bank assistant...'
              }
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={!isConnected}
              className="h-11 bg-background text-sm rounded-xl px-4"
            />

            <Button
              onClick={() => handleSendMessage()}
              disabled={!inputMessage.trim() || !isConnected}
              className="h-11 px-5 rounded-xl gap-2 font-medium"
            >
              <Send className="h-4 w-4" />
              <span className="hidden sm:inline">{isSpanish ? 'Enviar' : 'Send'}</span>
            </Button>
          </div>
          <p className="text-[11px] text-center text-muted-foreground">
            {isSpanish
              ? 'Tus respuestas son procesadas de forma segura y confidencial bajo la política de protección al usuario financiero.'
              : 'Your responses are handled securely and confidentially under fair banking and customer protection policies.'}
          </p>
        </div>
      </footer>
    </div>
  );
}
