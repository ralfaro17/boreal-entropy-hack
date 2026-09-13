import { useQuery } from '@tanstack/react-query';
import { conversationsApi } from '@/lib/api';

export function useConversations(params?: { customer_id?: string }) {
  return useQuery({
    queryKey: ['conversations', params],
    queryFn: () => conversationsApi.list(params),
  });
}

export function useConversationMessages(conversationId: string | null) {
  return useQuery({
    queryKey: ['conversation-messages', conversationId],
    queryFn: () => (conversationId ? conversationsApi.getMessages(conversationId) : Promise.resolve([])),
    enabled: !!conversationId,
  });
}

