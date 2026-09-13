import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { conversationsApi, riskRemindersApi, type SendRiskReminderPayload } from '@/lib/api';

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

export function useConversationEvents(conversationId: string | null) {
  return useQuery({
    queryKey: ['conversation-events', conversationId],
    queryFn: () => (conversationId ? conversationsApi.getEvents(conversationId) : Promise.resolve([])),
    enabled: !!conversationId,
  });
}

export function useRiskReminderCandidates() {
  return useQuery({
    queryKey: ['risk-reminder-candidates'],
    queryFn: () => riskRemindersApi.getCandidates(),
  });
}

export function useSendRiskReminder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: SendRiskReminderPayload) => riskRemindersApi.sendReminder(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      queryClient.invalidateQueries({ queryKey: ['risk-reminder-candidates'] });
      queryClient.invalidateQueries({ queryKey: ['conversation-messages'] });
      queryClient.invalidateQueries({ queryKey: ['conversation-events'] });
    },
  });
}

