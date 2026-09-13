import { z } from 'zod';

export const productTypeSchema = z.enum([
  'mortgage',
  'personal_loan',
  'credit_card',
  'auto_loan',
]);

export const accountCreateSchema = z.object({
  customer_id: z.string().uuid(),
  product_type: productTypeSchema,
  principal_amount: z.number().positive(),
  interest_rate: z.number().min(0).max(1),
  total_installments: z.number().int().positive().nullable().optional(),
});

export const accountUpdateSchema = z.object({
  product_type: productTypeSchema.nullable().optional(),
  principal_amount: z.number().positive().nullable().optional(),
  interest_rate: z.number().min(0).max(1).nullable().optional(),
  total_installments: z.number().int().positive().nullable().optional(),
  is_active: z.boolean().nullable().optional(),
});

export type AccountCreateInput = z.infer<typeof accountCreateSchema>;
export type AccountUpdateInput = z.infer<typeof accountUpdateSchema>;
