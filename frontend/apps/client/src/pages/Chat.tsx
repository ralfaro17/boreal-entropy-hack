import { useState } from 'react';
import { useNavigate } from 'react-router';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
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
} from '@/components/ui/dialog';
import { PageHeader } from '@/components/page-header';
import { useConversations, useConversationMessages } from '@/hooks/useConversations';
import type { Conversation } from '@/lib/api';
import {
  MessageSquare,
  Search,
  Eye,
  AlertTriangle,
  ExternalLink,
  Bot,
  User,
} from 'lucide-react';

export function Chat() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);

  const { data: conversations, isLoading } = useConversations();
  const { data: messages, isLoading: loadingMessages } = useConversationMessages(
    selectedConversation?.id ?? null
  );

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

  return (
    <div className="space-y-6">
      <PageHeader
        title={t('chat.title')}
        description={t('chat.description')}
      />

      <Card className="w-full">
        <CardHeader className="pb-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <CardTitle className="text-base font-semibold">
                {t('chat.conversations')}
              </CardTitle>
              {conversations && (
                <Badge variant="secondary" className="text-xs">
                  {conversations.length}
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Search className="h-4 w-4 text-muted-foreground" />
              <Input
                placeholder={t('chat.search')}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="max-w-sm h-9"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t('chat.customer')}</TableHead>
                <TableHead>{t('chat.channel')}</TableHead>
                <TableHead>{t('chat.status')}</TableHead>
                <TableHead>{t('chat.lastMessage')}</TableHead>
                <TableHead>{t('chat.messages')}</TableHead>
                <TableHead>{t('chat.lastActive')}</TableHead>
                <TableHead className="text-right">Actions</TableHead>
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
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div className="p-1.5 rounded-full bg-primary/10 text-primary">
                          <MessageSquare className="h-4 w-4" />
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
                    <TableCell className="max-w-[280px]">
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
                    <TableCell className="text-right">
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
          <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-[300px] max-h-[55vh]">
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
