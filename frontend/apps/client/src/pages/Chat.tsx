import { useState } from 'react';
import { useNavigate } from 'react-router';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { PageHeader } from '@/components/page-header';
import {
  useConversations,
  useConversationMessages,
  useConversationEvents,
  useRiskReminderCandidates,
  useSendRiskReminder,
} from '@/hooks/useConversations';
import { showSuccessToast, showErrorToast } from '@/lib/toast-utils';
import type { Conversation } from '@/lib/api';
import {
  MessageSquare,
  Search,
  Eye,
  AlertTriangle,
  ExternalLink,
  Bot,
  User,
  ShieldAlert,
  Send,
  Sparkles,
  CreditCard,
  Calendar,
  Clock,
  ShieldCheck,
  Phone,
} from 'lucide-react';
import { getChannelPreference } from '@/lib/channel-preference';

export function Chat() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);

  // Risk Reminder Dialog state
  const [reminderOpen, setReminderOpen] = useState(false);
  const [selectedCandidateId, setSelectedCandidateId] = useState('');
  const [customMessage, setCustomMessage] = useState('');

  const { data: conversations, isLoading } = useConversations();
  const { data: messages, isLoading: loadingMessages } = useConversationMessages(
    selectedConversation?.id ?? null
  );
  const { data: events, isLoading: loadingEvents } = useConversationEvents(
    selectedConversation?.id ?? null
  );


  const { data: candidates, isLoading: loadingCandidates } = useRiskReminderCandidates();
  const sendReminder = useSendRiskReminder();

  const selectedCandidate = candidates?.find((c) => c.customer_id === selectedCandidateId);

  const filteredConversations = conversations?.filter(
    (c) =>
      c.customer_name.toLowerCase().includes(search.toLowerCase()) ||
      (c.customer_email && c.customer_email.toLowerCase().includes(search.toLowerCase())) ||
      (c.last_message && c.last_message.toLowerCase().includes(search.toLowerCase()))
  );

  const formatDate = (isoString: string | null) => {
    if (!isoString) return '—';
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return isoString;
    }
  };

  const handleOpenReminder = () => {
    if (candidates && candidates.length > 0 && !selectedCandidateId) {
      setSelectedCandidateId(candidates[0].customer_id);
    }
    setReminderOpen(true);
  };

  const handleSendReminder = async () => {
    if (!selectedCandidateId) return;
    try {
      const result = await sendReminder.mutateAsync({
        customer_id: selectedCandidateId,
        language: i18n.language.startsWith('es') ? 'es' : 'en',
        custom_message: customMessage.trim() || undefined,
      });
      showSuccessToast(t('chat.reminderSentSuccess'));
      setReminderOpen(false);
      setCustomMessage('');

      // If conversation is available, highlight it
      if (result.conversation_id && conversations) {
        const matching = conversations.find((c) => c.id === result.conversation_id);
        if (matching) {
          setSelectedConversation(matching);
        }
      }
    } catch (err: any) {
      showErrorToast(err?.message || t('chat.reminderSentError'));
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title={t('chat.title')}
        description={t('chat.description')}
        action={
          <Button onClick={handleOpenReminder} className="gap-2">
            <ShieldAlert className="h-4 w-4" />
            {t('chat.sendRiskReminder')}
          </Button>
        }
      />

      <Card className="w-full overflow-hidden">
        <CardHeader className="pb-3 border-b bg-muted/30">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <MessageSquare className="h-4 w-4" />
              </div>
              <CardTitle className="text-base font-semibold">
                {t('chat.conversations')}
              </CardTitle>
              {conversations && (
                <Badge variant="secondary" className="text-xs">
                  {conversations.length}
                </Badge>
              )}
            </div>
            <div className="relative w-full sm:max-w-sm">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder={t('chat.search')}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9 h-9 bg-background"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/40 hover:bg-muted/40">
                <TableHead className="pl-6">{t('chat.customer')}</TableHead>
                <TableHead>{t('chat.channel')}</TableHead>
                <TableHead>{t('chat.status')}</TableHead>
                <TableHead>{t('chat.lastMessage')}</TableHead>
                <TableHead>{t('chat.messages')}</TableHead>
                <TableHead>{t('chat.auditTimelineTab')}</TableHead>
                <TableHead>{t('chat.lastActive')}</TableHead>
                <TableHead className="text-right pr-6">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                Array.from({ length: 4 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-16" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-20" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-48" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-8" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-16" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-24" /></TableCell>
                    <TableCell><Skeleton className="h-8 w-16 ml-auto" /></TableCell>
                  </TableRow>
                ))
              ) : !filteredConversations || filteredConversations.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="h-32 text-center text-muted-foreground">
                    {t('chat.noConversations')}
                  </TableCell>
                </TableRow>
              ) : (
                filteredConversations.map((convo) => (
                  <TableRow
                    key={convo.id}
                    className="cursor-pointer hover:bg-muted/50 transition-colors"
                    onClick={() => setSelectedConversation(convo)}
                  >
                    <TableCell className="pl-6">
                      <div className="flex items-center gap-2.5">
                        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary text-xs font-semibold">
                          {convo.customer_name
                            .split(' ')
                            .map((n) => n[0])
                            .slice(0, 2)
                            .join('')
                            .toUpperCase()}
                        </div>
                        <div>
                          <p className="font-medium text-sm leading-none">
                            {convo.customer_name}
                          </p>
                          {convo.customer_email && (
                            <p className="text-xs text-muted-foreground mt-0.5">
                              {convo.customer_email}
                            </p>
                          )}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-xs capitalize">
                        {convo.channel || 'app'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {convo.is_escalated ? (
                        <div className="space-y-0.5">
                          <Badge variant="destructive" className="text-xs">
                            {t('chat.escalated')}
                          </Badge>
                          {convo.escalation_reason && (
                            <p className="text-[10px] text-muted-foreground truncate max-w-36" title={convo.escalation_reason}>
                              {convo.escalation_reason}
                            </p>
                          )}
                        </div>
                      ) : (
                        <Badge variant="secondary" className="text-xs">
                          {t('chat.normal')}
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell className="max-w-70">
                      <p className="text-xs text-muted-foreground truncate">
                        {convo.last_message || 'No messages yet'}
                      </p>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary" className="text-xs font-mono">
                        {convo.message_count}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {convo.event_count && convo.event_count > 0 ? (
                        <Badge variant="outline" className="text-xs font-mono border-primary/40 text-primary">
                          {convo.event_count}
                        </Badge>
                      ) : (
                        <span className="text-xs text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
                      {formatDate(convo.last_message_at)}
                    </TableCell>
                    <TableCell className="text-right pr-6 space-x-2">

                      <Button
                        variant="outline"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          window.open(`/chat/${convo.customer_id}`, '_blank');
                        }}
                        title={t('chat.openCustomerChat')}
                        className="text-xs text-primary border-primary/30 hover:bg-primary/10"
                      >
                        <ExternalLink className="h-3.5 w-3.5 mr-1" />
                        {t('chat.openCustomerChat')}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedConversation(convo);
                        }}
                        className="text-xs"
                      >
                        <Eye className="h-3.5 w-3.5 mr-1" />
                        {t('chat.viewConversation')}
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Send Risk Reminder Dialog */}
      <Dialog open={reminderOpen} onOpenChange={setReminderOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-destructive/10 text-destructive">
                <ShieldAlert className="h-5 w-5" />
              </div>
              <div>
                <DialogTitle>{t('chat.riskReminderDialogTitle')}</DialogTitle>
                <DialogDescription className="text-xs mt-1">
                  {t('chat.riskReminderDialogDesc')}
                </DialogDescription>
              </div>
            </div>
          </DialogHeader>

          <div className="space-y-4 py-2">
            {/* Candidate Selector */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground">
                {t('chat.selectCustomer')}
              </label>
              {loadingCandidates ? (
                <Skeleton className="h-10 w-full" />
              ) : !candidates || candidates.length === 0 ? (
                <p className="text-xs text-muted-foreground p-3 border rounded-md">
                  {t('chat.noCandidates')}
                </p>
              ) : (
                <Select
                  value={selectedCandidateId}
                  onValueChange={(val) => {
                    if (val) setSelectedCandidateId(val);
                  }}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder={t('chat.selectCustomer')} />
                  </SelectTrigger>
                  <SelectContent>
                    {candidates.map((cand) => {
                      const pref = getChannelPreference(
                        {
                          id: cand.customer_id,
                          full_name: cand.customer_name,
                          email: cand.customer_email,
                        },
                        i18n.language
                      );
                      const isChat = pref.channel === 'chat';
                      return (
                        <SelectItem key={cand.customer_id} value={cand.customer_id}>
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{cand.customer_name}</span>
                            <span className="text-xs text-muted-foreground">
                              (${cand.amount_due.toFixed(2)})
                            </span>
                            <span
                              className={`inline-flex items-center gap-1 text-[10px] font-medium px-1.5 py-0.5 rounded border shrink-0 ${
                                isChat
                                  ? 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/50 dark:text-blue-300 dark:border-blue-800'
                                  : 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/50 dark:text-emerald-300 dark:border-emerald-800'
                              }`}
                            >
                              {isChat ? <MessageSquare className="h-2.5 w-2.5" /> : <Phone className="h-2.5 w-2.5" />}
                              {pref.tag}
                            </span>
                            {cand.is_overdue && (
                              <Badge variant="destructive" className="text-[10px] py-0 px-1.5">
                                Overdue
                              </Badge>
                            )}
                            {cand.hardship_flag && (
                              <Badge variant="outline" className="text-[10px] py-0 px-1.5 border-destructive text-destructive">
                                Hardship
                              </Badge>
                            )}
                          </div>
                        </SelectItem>
                      );
                    })}
                  </SelectContent>
                </Select>
              )}
            </div>

            {/* Selected Candidate Details Card */}
            {selectedCandidate && (() => {
              const pref = getChannelPreference(
                {
                  id: selectedCandidate.customer_id,
                  full_name: selectedCandidate.customer_name,
                  email: selectedCandidate.customer_email,
                },
                i18n.language
              );
              const isChat = pref.channel === 'chat';
              return (
                <div className="rounded-lg border bg-muted/40 p-3.5 space-y-2.5 text-xs">
                  <div className="flex items-center justify-between font-medium">
                    <div className="flex items-center gap-2">
                      <span>{selectedCandidate.customer_name}</span>
                      <span
                        className={`inline-flex items-center gap-1 text-[10px] font-medium px-1.5 py-0.5 rounded border ${
                          isChat
                            ? 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/50 dark:text-blue-300 dark:border-blue-800'
                            : 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/50 dark:text-emerald-300 dark:border-emerald-800'
                        }`}
                      >
                        {isChat ? <MessageSquare className="h-2.5 w-2.5" /> : <Phone className="h-2.5 w-2.5" />}
                        {pref.label}
                      </span>
                    </div>
                    <span className="text-muted-foreground">{selectedCandidate.customer_email}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 pt-1 border-t border-border/60">
                    <div className="flex items-center gap-1.5 text-muted-foreground">
                      <CreditCard className="h-3.5 w-3.5" />
                      <span>{t('chat.nextInstallment')}:</span>
                      <strong className="text-foreground font-semibold">
                        ${selectedCandidate.amount_due.toFixed(2)}
                      </strong>
                    </div>
                    <div className="flex items-center gap-1.5 text-muted-foreground">
                      <Calendar className="h-3.5 w-3.5" />
                      <span>{t('chat.dueDate')}:</span>
                      <strong className={`font-semibold ${selectedCandidate.is_overdue ? 'text-destructive' : 'text-foreground'}`}>
                        {selectedCandidate.due_date} ({selectedCandidate.days_until_due < 0 ? `${Math.abs(selectedCandidate.days_until_due)}d late` : `${selectedCandidate.days_until_due}d left`})
                      </strong>
                    </div>
                    <div className="flex items-center gap-1.5 text-muted-foreground">
                      <Clock className="h-3.5 w-3.5" />
                      <span>{t('chat.streak')}:</span>
                      <strong className="text-foreground font-semibold">
                        {selectedCandidate.missed_payment_streak} missed
                      </strong>
                    </div>
                    <div className="flex items-center gap-1.5 text-muted-foreground">
                      <AlertTriangle className="h-3.5 w-3.5" />
                      <span>{t('chat.hardship')}:</span>
                      <strong className={selectedCandidate.hardship_flag ? 'text-destructive font-semibold' : 'text-foreground'}>
                        {selectedCandidate.hardship_flag ? 'Yes' : 'No'}
                      </strong>
                    </div>
                  </div>
                  <div
                    className={`rounded border p-2 text-xs flex items-start gap-2 ${
                      isChat
                        ? 'bg-blue-500/10 border-blue-500/20 text-blue-950 dark:text-blue-300'
                        : 'bg-amber-500/10 border-amber-500/20 text-amber-950 dark:text-amber-300'
                    }`}
                  >
                    {isChat ? (
                      <MessageSquare className="h-3.5 w-3.5 mt-0.5 shrink-0 text-blue-600 dark:text-blue-400" />
                    ) : (
                      <Phone className="h-3.5 w-3.5 mt-0.5 shrink-0 text-amber-600 dark:text-amber-400" />
                    )}
                    <div className="space-y-0.5">
                      <div className="font-medium flex items-center gap-1">
                        <span>{t('channels.preference')}:</span>
                        <span>{pref.reason}</span>
                      </div>
                      {!isChat && (
                        <p className="text-[11px] text-amber-700 dark:text-amber-300/80 font-medium">
                          {t('channels.advisoryChat')}
                        </p>
                      )}
                    </div>
                  </div>
                  {selectedCandidate.last_reminder_at && (
                    <p className="text-[11px] text-muted-foreground pt-1 border-t border-border/60">
                      Last reminder: {formatDate(selectedCandidate.last_reminder_at)}
                    </p>
                  )}
                </div>
              );
            })()}

            {/* Custom Message Field */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-foreground flex items-center gap-1.5">
                <Sparkles className="h-3.5 w-3.5 text-primary" />
                <span>Message text</span>
              </label>
              <Textarea
                placeholder={t('chat.customMessagePlaceholder')}
                value={customMessage}
                onChange={(e) => setCustomMessage(e.target.value)}
                className="text-xs min-h-20"
              />
              <p className="text-[11px] text-muted-foreground">
                Leave empty to automatically generate a compliant, non-judgmental debt-prevention reminder using AI.
              </p>
            </div>
          </div>

          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setReminderOpen(false);
                setCustomMessage('');
              }}
              disabled={sendReminder.isPending}
            >
              Cancel
            </Button>
            <Button
              size="sm"
              onClick={handleSendReminder}
              disabled={!selectedCandidateId || sendReminder.isPending}
              className="gap-1.5"
            >
              <Send className="h-3.5 w-3.5" />
              {sendReminder.isPending ? t('chat.sending') : t('chat.sendAction')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Conversation Detail Modal */}
      <Dialog
        open={!!selectedConversation}
        onOpenChange={(open) => !open && setSelectedConversation(null)}
      >
        <DialogContent className="sm:max-w-3xl max-h-[88vh] flex flex-col p-0 gap-0 overflow-hidden">
          <DialogHeader className="p-5 pb-3 border-b">
            <div className="flex items-center justify-between pr-6">
              <div>
                <DialogTitle className="text-base flex items-center gap-2">
                  <MessageSquare className="h-5 w-5 text-primary" />
                  {selectedConversation?.customer_name}
                </DialogTitle>
                <DialogDescription className="text-xs text-muted-foreground mt-1">
                  Channel: <span className="capitalize font-medium">{selectedConversation?.channel || 'App'}</span>
                  {selectedConversation?.started_at && ` • Started ${formatDate(selectedConversation.started_at)}`}
                  {selectedConversation?.escalated_at && ` • Escalated ${formatDate(selectedConversation.escalated_at)}`}
                </DialogDescription>
              </div>
              {selectedConversation?.is_escalated && (
                <div className="flex flex-col items-end gap-1">
                  <Badge variant="destructive" className="flex items-center gap-1">
                    <AlertTriangle className="h-3 w-3" />
                    {t('chat.escalated')}
                  </Badge>
                  {selectedConversation?.escalation_reason && (
                    <span className="text-[10px] text-muted-foreground max-w-64 truncate" title={selectedConversation.escalation_reason}>
                      {selectedConversation.escalation_reason}
                    </span>
                  )}
                </div>
              )}
            </div>
          </DialogHeader>

          {/* Navigation Tabs */}
          <Tabs defaultValue="messages" className="flex-1 flex flex-col min-h-0">
            <div className="px-5 pt-3 pb-1 border-b bg-muted/20">
              <TabsList>
                <TabsTrigger value="messages" className="gap-2 text-xs">
                  <MessageSquare className="h-3.5 w-3.5" />
                  <span>{t('chat.messagesTab')}</span>
                  {messages && (
                    <Badge variant="secondary" className="text-[10px] py-0 px-1.5 ml-1">
                      {messages.length}
                    </Badge>
                  )}
                </TabsTrigger>
                <TabsTrigger value="events" className="gap-2 text-xs">
                  <ShieldCheck className="h-3.5 w-3.5 text-primary" />
                  <span>{t('chat.auditTimelineTab')}</span>
                  {events && (
                    <Badge variant="outline" className="text-[10px] py-0 px-1.5 ml-1 border-primary/40 text-primary">
                      {events.length}
                    </Badge>
                  )}
                </TabsTrigger>
              </TabsList>
            </div>

            {/* Messages Tab: Dialogue Only */}
            <TabsContent value="messages" className="flex-1 overflow-y-auto p-5 space-y-4 m-0 min-h-75 max-h-[55vh]">
              {loadingMessages ? (
                <div className="space-y-3">
                  <Skeleton className="h-16 w-3/4" />
                  <Skeleton className="h-16 w-3/4 ml-auto" />
                  <Skeleton className="h-16 w-2/3" />
                </div>
              ) : !messages || messages.length === 0 ? (
                <div className="text-center text-muted-foreground py-12 text-sm">
                  No messages found for this conversation.
                </div>
              ) : (
                messages.map((msg) => {
                  const isUser = msg.role === 'user';
                  return (
                    <div
                      key={msg.id}
                      className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}
                    >
                      <div className="flex items-center gap-1.5 mb-1 px-1">
                        {isUser ? (
                          <>
                            <span className="text-xs font-medium text-muted-foreground">
                              {selectedConversation?.customer_name || 'Customer'}
                            </span>
                            <User className="h-3.5 w-3.5 text-muted-foreground" />
                          </>
                        ) : (
                          <>
                            <Bot className="h-3.5 w-3.5 text-primary" />
                            <span className="text-xs font-medium text-primary">
                              Payment Assistant
                            </span>
                          </>
                        )}
                      </div>
                      <div
                        className={`max-w-[80%] rounded-xl px-4 py-2.5 text-sm ${
                          isUser
                            ? 'bg-primary text-primary-foreground rounded-tr-none'
                            : 'bg-muted text-foreground rounded-tl-none'
                        }`}
                      >
                        <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                        {msg.flagged && (
                          <div className="mt-2 pt-2 border-t border-destructive/30 flex items-center gap-1 text-xs text-destructive font-medium">
                            <AlertTriangle className="h-3.5 w-3.5" />
                            Flagged for human review
                          </div>
                        )}
                      </div>
                      <span className="text-[10px] text-muted-foreground px-1 mt-1">
                        {formatDate(msg.created_at)}
                      </span>
                    </div>
                  );
                })
              )}
            </TabsContent>

            {/* Audit & Compliance Timeline Tab */}
            <TabsContent value="events" className="flex-1 overflow-y-auto p-5 space-y-3 m-0 min-h-75 max-h-[55vh]">
              <div className="rounded-md bg-muted/40 border border-border/60 p-3 text-xs text-muted-foreground flex items-start gap-2.5 mb-2">
                <ShieldCheck className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                <p>
                  {t('chat.auditTimelineDesc')}
                </p>
              </div>

              {loadingEvents ? (
                <div className="space-y-3">
                  <Skeleton className="h-14 w-full" />
                  <Skeleton className="h-14 w-full" />
                  <Skeleton className="h-14 w-full" />
                </div>
              ) : !events || events.length === 0 ? (
                <div className="text-center text-muted-foreground py-12 text-sm">
                  {t('chat.noAuditEvents')}
                </div>
              ) : (
                <div className="relative border-l-2 border-border/80 ml-4 pl-4 space-y-4 py-1">
                  {events.map((evt) => {
                    const isEscalation = evt.event_type.includes('escalated') || evt.event_type.includes('distress');
                    const isHandoff = evt.event_type.includes('handoff');
                    const isFlagged = evt.event_type.includes('guardrail') || evt.event_type.includes('blocked');
                    const isReminder = evt.event_type.includes('reminder');

                    return (
                      <div key={evt.id} className="relative group">
                        {/* Timeline dot */}
                        <div
                          className={`absolute -left-[23px] top-1 h-3.5 w-3.5 rounded-full border-2 border-background ${
                            isEscalation || isFlagged
                              ? 'bg-destructive'
                              : isHandoff
                              ? 'bg-primary'
                              : isReminder
                              ? 'bg-amber-500'
                              : 'bg-muted-foreground'
                          }`}
                        />
                        <div className="rounded-lg border bg-card p-3.5 shadow-sm space-y-1.5">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-semibold text-foreground">
                                {evt.title}
                              </span>
                              <Badge
                                variant={
                                  isEscalation || isFlagged
                                    ? 'destructive'
                                    : isHandoff
                                    ? 'default'
                                    : 'secondary'
                                }
                                className="text-[10px] py-0 px-1.5 uppercase font-mono"
                              >
                                {evt.event_type.replace(/_/g, ' ')}
                              </Badge>
                            </div>
                            <span className="text-[11px] text-muted-foreground font-mono">
                              {formatDate(evt.created_at)}
                            </span>
                          </div>

                          {evt.description && (
                            <p className="text-xs text-muted-foreground leading-relaxed">
                              {evt.description}
                            </p>
                          )}

                          {evt.metadata && Object.keys(evt.metadata).length > 0 && (
                            <div className="mt-2 pt-2 border-t border-border/50 text-[11px] font-mono bg-muted/30 p-2 rounded">
                              <span className="text-muted-foreground block mb-1 font-sans font-medium text-[10px] uppercase">
                                {t('chat.auditMetadata')}:
                              </span>
                              <pre className="text-[10px] overflow-x-auto text-muted-foreground leading-tight">
                                {JSON.stringify(evt.metadata, null, 2)}
                              </pre>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </TabsContent>
          </Tabs>

          <div className="border-t p-3 bg-muted/10 flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              {selectedConversation?.customer_id && (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      window.open(`/chat/${selectedConversation.customer_id}`, '_blank');
                    }}
                    className="gap-1.5 text-primary border-primary/30 hover:bg-primary/10 text-xs"
                  >
                    <ExternalLink className="h-3.5 w-3.5" />
                    {t('chat.respondAsCustomer')}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      const customerId = selectedConversation.customer_id;
                      setSelectedConversation(null);
                      navigate(`/customers/${customerId}`);
                    }}
                    className="text-xs"
                  >
                    <User className="h-3.5 w-3.5 mr-1" />
                    Profile
                  </Button>
                </>
              )}
            </div>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setSelectedConversation(null)}
              className="text-xs ml-auto"
            >
              Close
            </Button>
          </div>
        </DialogContent>
      </Dialog>

    </div>
  );
}
