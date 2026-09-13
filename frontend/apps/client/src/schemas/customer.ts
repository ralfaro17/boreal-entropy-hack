import { z } from 'zod';

export const employmentStatusSchema = z.enum([
  'employed',
  'self_employed',
  'unemployed',
  'retired',
  'student',
]);

export const customerCreateSchema = z.object({
  full_name: z.string().min(1, 'Name is required'),
  email: z.string().email('Invalid email address'),
  age: z.number().int().min(18).max(120).nullable().optional(),
  region: z.string().nullable().optional(),
  employment_status: employmentStatusSchema.nullable().optional(),
  income_bracket: z.string().nullable().optional(),
  tenure_months: z.number().int().min(0).nullable().optional(),
  credit_score: z.number().int().min(300).max(850).nullable().optional(),
});

export const customerUpdateSchema = z.object({
  full_name: z.string().min(1).nullable().optional(),
  email: z.string().email().nullable().optional(),
  age: z.number().int().min(18).max(120).nullable().optional(),
  region: z.string().nullable().optional(),
  employment_status: employmentStatusSchema.nullable().optional(),
  income_bracket: z.string().nullable().optional(),
  tenure_months: z.number().int().min(0).nullable().optional(),
  credit_score: z.number().int().min(300).max(850).nullable().optional(),
});

export type CustomerCreateInput = z.infer<typeof customerCreateSchema>;
export type CustomerUpdateInput = z.infer<typeof customerUpdateSchema>;
