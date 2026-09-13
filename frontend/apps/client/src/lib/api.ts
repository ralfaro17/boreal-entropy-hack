const API_BASE = '';

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>;
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { params, ...fetchOptions } = options;

  let url = endpoint;
  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value));
      }
    });
    const queryString = searchParams.toString();
    if (queryString) {
      url += `?${queryString}`;
    }
  }

  const response = await fetch(`${API_BASE}${url}`, {
    ...fetchOptions,
    headers: {
      'Content-Type': 'application/json',
      ...fetchOptions.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

// Customers
export const customersApi = {
  list: (params?: { skip?: number; limit?: number; email?: string; region?: string; employment_status?: string }) =>
    request<Customer[]>('/customers', { params }),

  get: (id: string) =>
    request<Customer>(`/customers/${id}`),

  create: (data: CustomerCreate) =>
    request<Customer>('/customers', { method: 'POST', body: JSON.stringify(data) }),

  update: (id: string, data: CustomerUpdate) =>
    request<Customer>(`/customers/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  delete: (id: string) =>
    request<void>(`/customers/${id}`, { method: 'DELETE' }),

  getAccounts: (customerId: string) =>
    request<Account[]>(`/customers/${customerId}/accounts`),

  getActivities: (customerId: string) =>
    request<AccountActivity[]>(`/customers/${customerId}/account-activity`),

  getRiskFeatures: (customerId: string) =>
    request<RiskFeature[]>(`/customers/${customerId}/risk-features`),

  getEarlyWarning: (customerId: string) =>
    request<EarlyWarning>(`/customers/${customerId}/early-warning`),
};

// Accounts
export const accountsApi = {
  list: (params?: { skip?: number; limit?: number; customer_id?: string; product_type?: string; is_active?: boolean }) =>
    request<Account[]>('/accounts', { params }),

  get: (id: string) =>
    request<Account>(`/accounts/${id}`),

  create: (data: AccountCreate) =>
    request<Account>('/accounts', { method: 'POST', body: JSON.stringify(data) }),

  update: (id: string, data: AccountUpdate) =>
    request<Account>(`/accounts/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  delete: (id: string) =>
    request<void>(`/accounts/${id}`, { method: 'DELETE' }),

  getPayments: (accountId: string) =>
    request<Payment[]>(`/accounts/${accountId}/payments`),
};

// Payments
export const paymentsApi = {
  list: (params?: { skip?: number; limit?: number; account_id?: string; status?: string }) =>
    request<Payment[]>('/payments', { params }),

  get: (id: string) =>
    request<Payment>(`/payments/${id}`),

  create: (data: PaymentCreate) =>
    request<Payment>('/payments', { method: 'POST', body: JSON.stringify(data) }),

  update: (id: string, data: PaymentUpdate) =>
    request<Payment>(`/payments/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  delete: (id: string) =>
    request<void>(`/payments/${id}`, { method: 'DELETE' }),
};

// Account Activity
export const accountActivityApi = {
  list: (params?: { skip?: number; limit?: number; customer_id?: string; hardship_flag?: boolean; large_withdrawal_flag?: boolean }) =>
    request<AccountActivity[]>('/account-activity', { params }),

  get: (id: string) =>
    request<AccountActivity>(`/account-activity/${id}`),

  create: (data: AccountActivityCreate) =>
    request<AccountActivity>('/account-activity', { method: 'POST', body: JSON.stringify(data) }),

  update: (id: string, data: AccountActivityUpdate) =>
    request<AccountActivity>(`/account-activity/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  delete: (id: string) =>
    request<void>(`/account-activity/${id}`, { method: 'DELETE' }),
};

// Risk Features
export const riskFeaturesApi = {
  list: (params?: { skip?: number; limit?: number; customer_id?: string; early_warning_flag?: boolean; defaulted?: boolean }) =>
    request<RiskFeature[]>('/risk-features', { params }),

  get: (id: string) =>
    request<RiskFeature>(`/risk-features/${id}`),

  create: (data: RiskFeatureCreate) =>
    request<RiskFeature>('/risk-features', { method: 'POST', body: JSON.stringify(data) }),

  update: (id: string, data: RiskFeatureUpdate) =>
    request<RiskFeature>(`/risk-features/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  delete: (id: string) =>
    request<void>(`/risk-features/${id}`, { method: 'DELETE' }),
};

// Types
export type EmploymentStatus = 'employed' | 'self_employed' | 'unemployed' | 'retired' | 'student';
export type ProductType = 'mortgage' | 'personal_loan' | 'credit_card' | 'auto_loan';
export type PaymentStatus = 'on_time' | 'late' | 'partial' | 'missed' | 'reversed' | 'grace_period';
export type PaymentMethod = 'auto_debit' | 'transfer' | 'cash' | 'card' | 'third_party';
export type Channel = 'app' | 'branch' | 'atm' | 'call_center' | 'web';

export interface Customer {
  id: string;
  full_name: string;
  email: string;
  age: number | null;
  region: string | null;
  employment_status: EmploymentStatus | null;
  income_bracket: string | null;
  tenure_months: number | null;
  credit_score: number | null;
  created_at: string;
}

export interface CustomerCreate {
  full_name: string;
  email: string;
  age?: number | null;
  region?: string | null;
  employment_status?: EmploymentStatus | null;
  income_bracket?: string | null;
  tenure_months?: number | null;
  credit_score?: number | null;
}

export interface CustomerUpdate {
  full_name?: string | null;
  email?: string | null;
  age?: number | null;
  region?: string | null;
  employment_status?: EmploymentStatus | null;
  income_bracket?: string | null;
  tenure_months?: number | null;
  credit_score?: number | null;
}

export interface Account {
  id: string;
  customer_id: string;
  product_type: ProductType;
  principal_amount: number;
  interest_rate: number;
  total_installments: number | null;
  opened_at: string;
  is_active: boolean;
}

export interface AccountCreate {
  customer_id: string;
  product_type: ProductType;
  principal_amount: number;
  interest_rate: number;
  total_installments?: number | null;
}

export interface AccountUpdate {
  product_type?: ProductType | null;
  principal_amount?: number | null;
  interest_rate?: number | null;
  total_installments?: number | null;
  is_active?: boolean | null;
}

export interface Payment {
  id: string;
  account_id: string;
  amount_due: number;
  amount_paid: number | null;
  currency: string;
  minimum_payment_due: number | null;
  due_date: string;
  payment_date: string | null;
  posted_date: string | null;
  billing_cycle_start: string | null;
  billing_cycle_end: string | null;
  status: PaymentStatus;
  days_late: number;
  payment_method: PaymentMethod | null;
  channel: Channel | null;
  is_partial_payment: boolean;
  installment_number: number | null;
  outstanding_balance_after: number | null;
  late_fee_charged: number | null;
  interest_accrued: number | null;
  retry_count: number;
}

export interface PaymentCreate {
  account_id: string;
  amount_due: number;
  amount_paid?: number | null;
  currency?: string;
  minimum_payment_due?: number | null;
  due_date: string;
  payment_date?: string | null;
  posted_date?: string | null;
  billing_cycle_start?: string | null;
  billing_cycle_end?: string | null;
  status?: PaymentStatus;
  days_late?: number;
  payment_method?: PaymentMethod | null;
  channel?: Channel | null;
  is_partial_payment?: boolean;
  installment_number?: number | null;
}

export interface PaymentUpdate {
  amount_due?: number | null;
  amount_paid?: number | null;
  currency?: string | null;
  minimum_payment_due?: number | null;
  outstanding_balance_after?: number | null;
  late_fee_charged?: number | null;
  interest_accrued?: number | null;
  due_date?: string | null;
  payment_date?: string | null;
  posted_date?: string | null;
  billing_cycle_start?: string | null;
  billing_cycle_end?: string | null;
  status?: PaymentStatus | null;
  days_late?: number | null;
  payment_method?: PaymentMethod | null;
  channel?: Channel | null;
  is_partial_payment?: boolean | null;
  retry_count?: number | null;
  installment_number?: number | null;
}

export interface AccountActivity {
  id: string;
  customer_id: string;
  snapshot_date: string;
  checking_balance: number | null;
  savings_balance: number | null;
  overdraft_count_30d: number;
  large_withdrawal_flag: boolean;
  salary_deposit_detected: boolean;
  app_logins_30d: number;
  support_contacts_30d: number;
  hardship_flag: boolean;
}

export interface AccountActivityCreate {
  customer_id: string;
  snapshot_date: string;
  checking_balance?: number | null;
  savings_balance?: number | null;
  overdraft_count_30d?: number;
  large_withdrawal_flag?: boolean;
  salary_deposit_detected?: boolean;
  app_logins_30d?: number;
  support_contacts_30d?: number;
  hardship_flag?: boolean;
}

export interface AccountActivityUpdate {
  snapshot_date?: string | null;
  checking_balance?: number | null;
  savings_balance?: number | null;
  overdraft_count_30d?: number | null;
  large_withdrawal_flag?: boolean | null;
  salary_deposit_detected?: boolean | null;
  app_logins_30d?: number | null;
  support_contacts_30d?: number | null;
  hardship_flag?: boolean | null;
}

export interface RiskFeature {
  id: string;
  customer_id: string;
  as_of_date: string;
  consecutive_partial_payments: number;
  missed_payment_streak: number;
  avg_days_late_90d: number;
  debt_to_income_ratio: number | null;
  credit_utilization_pct: number | null;
  balance_trend_30d: number | null;
  early_warning_flag: boolean;
  defaulted: boolean;
  days_to_default: number | null;
}

export interface RiskFeatureCreate {
  customer_id: string;
  as_of_date: string;
  consecutive_partial_payments?: number;
  missed_payment_streak?: number;
  avg_days_late_90d?: number;
  debt_to_income_ratio?: number | null;
  credit_utilization_pct?: number | null;
  balance_trend_30d?: number | null;
  early_warning_flag?: boolean;
  defaulted?: boolean;
  days_to_default?: number | null;
}

export interface RiskFeatureUpdate {
  as_of_date?: string | null;
  consecutive_partial_payments?: number | null;
  missed_payment_streak?: number | null;
  avg_days_late_90d?: number | null;
  debt_to_income_ratio?: number | null;
  credit_utilization_pct?: number | null;
  balance_trend_30d?: number | null;
  early_warning_flag?: boolean | null;
  defaulted?: boolean | null;
  days_to_default?: number | null;
}

export interface EarlyWarning {
  customer_id: string;
  as_of_date: string;
  early_warning_flag: boolean;
  missed_payment_streak: number;
  consecutive_partial_payments: number;
  debt_to_income_ratio: number | null;
  credit_utilization_pct: number | null;
  balance_trend_30d: number | null;
}
