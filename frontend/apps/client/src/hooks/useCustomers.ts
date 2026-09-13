import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  customersApi,
  accountsApi,
  accountActivityApi,
  riskFeaturesApi,
  type CustomerCreate,
  type CustomerUpdate,
  type AccountCreate,
  type AccountActivityCreate,
  type RiskFeatureCreate,
} from '@/lib/api';

export function useCustomers(params?: { skip?: number; limit?: number; email?: string; region?: string; employment_status?: string }) {
  return useQuery({
    queryKey: ['customers', params],
    queryFn: () => customersApi.list(params),
  });
}

export function useCustomer(id: string) {
  return useQuery({
    queryKey: ['customers', id],
    queryFn: () => customersApi.get(id),
    enabled: !!id,
  });
}

export function useCreateCustomer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CustomerCreate) => customersApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
    },
  });
}

export function useUpdateCustomer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: CustomerUpdate }) =>
      customersApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
      queryClient.invalidateQueries({ queryKey: ['customers', id] });
    },
  });
}

export function useDeleteCustomer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => customersApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
    },
  });
}

export function useCustomerAccounts(customerId: string) {
  return useQuery({
    queryKey: ['customers', customerId, 'accounts'],
    queryFn: () => customersApi.getAccounts(customerId),
    enabled: !!customerId,
  });
}

export function useCustomerActivities(customerId: string) {
  return useQuery({
    queryKey: ['customers', customerId, 'activities'],
    queryFn: () => customersApi.getActivities(customerId),
    enabled: !!customerId,
  });
}

export function useCustomerRiskFeatures(customerId: string) {
  return useQuery({
    queryKey: ['customers', customerId, 'risk-features'],
    queryFn: () => customersApi.getRiskFeatures(customerId),
    enabled: !!customerId,
  });
}

export function useCustomerEarlyWarning(customerId: string) {
  return useQuery({
    queryKey: ['customers', customerId, 'early-warning'],
    queryFn: () => customersApi.getEarlyWarning(customerId),
    enabled: !!customerId,
  });
}

export function useCreateAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: AccountCreate) => accountsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
    },
  });
}

export function useCreateActivity() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: AccountActivityCreate) => accountActivityApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
      queryClient.invalidateQueries({ queryKey: ['activities'] });
    },
  });
}

export function useCreateRiskFeature() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: RiskFeatureCreate) => riskFeaturesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
      queryClient.invalidateQueries({ queryKey: ['risk-features'] });
    },
  });
}
