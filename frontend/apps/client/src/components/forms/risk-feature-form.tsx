import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useTranslation } from 'react-i18next';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface RiskFeatureFormProps {
  customerId: string;
  onSubmit: (data: any) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

const schema = z.object({
  customer_id: z.string().uuid(),
  as_of_date: z.string().min(1),
  consecutive_partial_payments: z.number().int().min(0).default(0),
  missed_payment_streak: z.number().int().min(0).default(0),
  avg_days_late_90d: z.number().min(0).default(0),
  debt_to_income_ratio: z.number().nullable().optional(),
  credit_utilization_pct: z.number().nullable().optional(),
  balance_trend_30d: z.number().nullable().optional(),
  early_warning_flag: z.boolean().default(false),
  defaulted: z.boolean().default(false),
  days_to_default: z.number().int().nullable().optional(),
});

export function RiskFeatureForm({ customerId, onSubmit, onCancel, isLoading }: RiskFeatureFormProps) {
  const { t } = useTranslation();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      customer_id: customerId,
      as_of_date: new Date().toISOString().split('T')[0],
      consecutive_partial_payments: 0,
      missed_payment_streak: 0,
      avg_days_late_90d: 0,
      early_warning_flag: false,
      defaulted: false,
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="grid gap-4 py-4">
      <div className="grid gap-2">
        <Label>{t('detail.asOfDate')} *</Label>
        <Input type="date" {...register('as_of_date')} />
        {errors.as_of_date && (
          <p className="text-xs text-destructive">{errors.as_of_date.message}</p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="grid gap-2">
          <Label>{t('detail.debtToIncome')}</Label>
          <Input type="number" step="0.01" {...register('debt_to_income_ratio', { valueAsNumber: true })} />
        </div>
        <div className="grid gap-2">
          <Label>{t('detail.creditUtilization')}</Label>
          <Input type="number" step="0.01" {...register('credit_utilization_pct', { valueAsNumber: true })} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="grid gap-2">
          <Label>{t('detail.balanceTrend')}</Label>
          <Input type="number" step="0.01" {...register('balance_trend_30d', { valueAsNumber: true })} />
        </div>
        <div className="grid gap-2">
          <Label>{t('detail.avgDaysLate')}</Label>
          <Input type="number" step="0.01" min="0" {...register('avg_days_late_90d', { valueAsNumber: true })} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="grid gap-2">
          <Label>{t('detail.consecutivePartial')}</Label>
          <Input type="number" min="0" {...register('consecutive_partial_payments', { valueAsNumber: true })} />
        </div>
        <div className="grid gap-2">
          <Label>{t('detail.missedStreak')}</Label>
          <Input type="number" min="0" {...register('missed_payment_streak', { valueAsNumber: true })} />
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="flex items-center gap-2">
          <input type="checkbox" {...register('early_warning_flag')} />
          <Label>{t('detail.earlyWarning')}</Label>
        </div>
        <div className="flex items-center gap-2">
          <input type="checkbox" {...register('defaulted')} />
          <Label>{t('detail.defaulted')}</Label>
        </div>
        <div className="grid gap-2">
          <Label>{t('detail.daysToDefault')}</Label>
          <Input type="number" min="0" {...register('days_to_default', { valueAsNumber: true })} />
        </div>
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isLoading}>
          {t('common.cancel')}
        </Button>
        <Button type="submit" disabled={isLoading}>
          {isLoading ? t('common.loading') : t('common.save')}
        </Button>
      </div>
    </form>
  );
}