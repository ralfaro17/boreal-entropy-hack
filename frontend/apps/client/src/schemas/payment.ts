import { z } from 'zod';

export const paymentStatusSchema = z.enum([
  'on_time',
  'late',
  'partial',
  'missed',
  'reversed',
  'grace_period',
]);

export const paymentMethodSchema = z.enum([
  'auto_debit',
  'transfer',
  'cash',
  'card',
  'third_party',
]);

export const channelSchema = z.enum([
  'app',
  'branch',
  'atm',
  'call_center',
  'web',
]);

export const paymentCreateSchema = z.object({
  account_id: z.string().uuid(),
  amount_due: z.number().positive(),
  amount_paid: z.number().min(0).nullable().optional(),
  currency: z.string().length(3).default('USD'),
  minimum_payment_due: z.number().min(0).nullable().optional(),
  due_date: z.string(),
  payment_date: z.string().nullable().optional(),
  posted_date: z.string().nullable().optional(),
  billing_cycle_start: z.string().nullable().optional(),
  billing_cycle_end: z.string().nullable().optional(),
  status: paymentStatusSchema.default('on_time'),
  days_late: z.number().int().min(0).default(0),
  payment_method: paymentMethodSchema.nullable().optional(),
  channel: channelSchema.nullable().optional(),
  is_partial_payment: z.boolean().default(false),
  installment_number: z.number().int().positive().nullable().optional(),
});

export const paymentUpdateSchema = z.object({
  amount_due: z.number().positive().nullable().optional(),
  amount_paid: z.number().min(0).nullable().optional(),
  currency: z.string().length(3).nullable().optional(),
  minimum_payment_due: z.number().min(0).nullable().optional(),
  outstanding_balance_after: z.number().nullable().optional(),
  late_fee_charged: z.number().min(0).nullable().optional(),
  interest_accrued: z.number().min(0).nullable().optional(),
  due_date: z.string().nullable().optional(),
  payment_date: z.string().nullable().optional(),
  posted_date: z.string().nullable().optional(),
  billing_cycle_start: z.string().nullable().optional(),
  billing_cycle_end: z.string().nullable().optional(),
  status: paymentStatusSchema.nullable().optional(),
  days_late: z.number().int().min(0).nullable().optional(),
  payment_method: paymentMethodSchema.nullable().optional(),
  channel: channelSchema.nullable().optional(),
  is_partial_payment: z.boolean().nullable().optional(),
  retry_count: z.number().int().min(0).nullable().optional(),
  installment_number: z.number().int().positive().nullable().optional(),
});

export type PaymentCreateInput = z.infer<typeof paymentCreateSchema>;
export type PaymentUpdateInput = z.infer<typeof paymentUpdateSchema>;
