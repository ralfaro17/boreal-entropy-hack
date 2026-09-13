import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { accountsApi, type AccountCreate, type AccountUpdate } from '@/lib/api';

export function useAccounts(params?: { skip?: number; limit?: number; customer_id?: string; product_type?: string; is_active?: boolean }) {
  return useQuery({
    queryKey: ['accounts', params],
    queryFn: () => accountsApi.list(params),
  });
}

export function useAccount(id: string) {
  return useQuery({
    queryKey: ['accounts', id],
    queryFn: () => accountsApi.get(id),
    enabled: !!id,
  });
}

export function useCreateAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: AccountCreate) => accountsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
    },
  });
}

export function useUpdateAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: AccountUpdate }) =>
      accountsApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      queryClient.invalidateQueries({ queryKey: ['accounts', id] });
    },
  });
}

export function useDeleteAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => accountsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
    },
  });
}

export function useAccountPayments(accountId: string) {
  return useQuery({
    queryKey: ['accounts', accountId, 'payments'],
    queryFn: () => accountsApi.getPayments(accountId),
    enabled: !!accountId,
  });
}
