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
import { PageHeader } from '@/components/page-header';
import {
  useConversations,
  useConversationMessages,
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
} from 'lucide-react';

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
                    <TableCell><Skeleton className="h-4 w-24" /></TableCell>
                    <TableCell><Skeleton className="h-8 w-16 ml-auto" /></TableCell>
                  </TableRow>
                ))
              ) : !filteredConversations || filteredConversations.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="h-32 text-center text-muted-foreground">
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
                        <Badge variant="destructive" className="text-xs">
                          {t('chat.escalated')}
                        </Badge>
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
                    <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
                      {formatDate(convo.last_message_at)}
                    </TableCell>
                    <TableCell className="text-right pr-6">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedConversation(convo);
                        }}
                      >
                        <Eye className="h-4 w-4 mr-1" />
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
                    {candidates.map((cand) => (
                      <SelectItem key={cand.customer_id} value={cand.customer_id}>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{cand.customer_name}</span>
                          <span className="text-xs text-muted-foreground">
                            (${cand.amount_due.toFixed(2)})
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
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>

            {/* Selected Candidate Details Card */}
            {selectedCandidate && (
              <div className="rounded-lg border bg-muted/40 p-3.5 space-y-2.5 text-xs">
                <div className="flex items-center justify-between font-medium">
                  <span>{selectedCandidate.customer_name}</span>
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
                {selectedCandidate.last_reminder_at && (
                  <p className="text-[11px] text-muted-foreground pt-1 border-t border-border/60">
                    Last reminder: {formatDate(selectedCandidate.last_reminder_at)}
                  </p>
                )}
              </div>
            )}

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
        <DialogContent className="sm:max-w-2xl max-h-[85vh] flex flex-col">
          <DialogHeader className="pb-3 border-b">
            <div className="flex items-center justify-between pr-6">
              <div>
                <DialogTitle className="text-base flex items-center gap-2">
                  <MessageSquare className="h-5 w-5 text-primary" />
                  {selectedConversation?.customer_name}
                </DialogTitle>
                <DialogDescription className="text-xs text-muted-foreground mt-1">
                  Channel: <span className="capitalize font-medium">{selectedConversation?.channel || 'App'}</span>
                  {selectedConversation?.started_at && ` • Started ${formatDate(selectedConversation.started_at)}`}
                </DialogDescription>
              </div>
              {selectedConversation?.is_escalated && (
                <Badge variant="destructive" className="flex items-center gap-1">
                  <AlertTriangle className="h-3 w-3" />
                  {t('chat.escalated')}
                </Badge>
              )}
            </div>
          </DialogHeader>

          {/* Message History */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-75 max-h-[55vh]">
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
          </div>

          <div className="border-t pt-3 flex items-center justify-between">
            {selectedConversation?.customer_id ? (
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  const customerId = selectedConversation.customer_id;
                  setSelectedConversation(null);
                  navigate(`/customers/${customerId}`);
                }}
              >
                <ExternalLink className="h-4 w-4 mr-1.5" />
                View Customer Profile
              </Button>
            ) : (
              <div />
            )}
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setSelectedConversation(null)}
            >
              Close
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
