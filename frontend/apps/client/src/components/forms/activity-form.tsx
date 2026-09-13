import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useTranslation } from 'react-i18next';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface ActivityFormProps {
  customerId: string;
  onSubmit: (data: any) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

const schema = z.object({
  customer_id: z.string().uuid(),
  snapshot_date: z.string().min(1),
  checking_balance: z.number().nullable().optional(),
  savings_balance: z.number().nullable().optional(),
  overdraft_count_30d: z.number().int().min(0).default(0),
  large_withdrawal_flag: z.boolean().default(false),
  salary_deposit_detected: z.boolean().default(true),
  app_logins_30d: z.number().int().min(0).default(0),
  support_contacts_30d: z.number().int().min(0).default(0),
  hardship_flag: z.boolean().default(false),
});

export function ActivityForm({ customerId, onSubmit, onCancel, isLoading }: ActivityFormProps) {
  const { t } = useTranslation();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      customer_id: customerId,
      snapshot_date: new Date().toISOString().split('T')[0],
      overdraft_count_30d: 0,
      large_withdrawal_flag: false,
      salary_deposit_detected: true,
      app_logins_30d: 0,
      support_contacts_30d: 0,
      hardship_flag: false,
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="grid gap-4 py-4">
      <div className="grid gap-2">
        <Label>{t('detail.snapshotDate')} *</Label>
        <Input type="date" {...register('snapshot_date')} />
        {errors.snapshot_date && (
          <p className="text-xs text-destructive">{errors.snapshot_date.message}</p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="grid gap-2">
          <Label>{t('detail.checkingBalance')}</Label>
          <Input type="number" step="0.01" {...register('checking_balance', { valueAsNumber: true })} />
        </div>
        <div className="grid gap-2">
          <Label>{t('detail.savingsBalance')}</Label>
          <Input type="number" step="0.01" {...register('savings_balance', { valueAsNumber: true })} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="grid gap-2">
          <Label>{t('detail.overdraftCount')}</Label>
          <Input type="number" min="0" {...register('overdraft_count_30d', { valueAsNumber: true })} />
        </div>
        <div className="grid gap-2">
          <Label>{t('detail.appLogins')}</Label>
          <Input type="number" min="0" {...register('app_logins_30d', { valueAsNumber: true })} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="grid gap-2">
          <Label>{t('detail.supportContacts')}</Label>
          <Input type="number" min="0" {...register('support_contacts_30d', { valueAsNumber: true })} />
        </div>
        <div className="flex items-center gap-2 pt-6">
          <input type="checkbox" {...register('hardship_flag')} />
          <Label>{t('detail.hardshipFlag')}</Label>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="flex items-center gap-2">
          <input type="checkbox" {...register('large_withdrawal_flag')} />
          <Label>{t('detail.largeWithdrawal')}</Label>
        </div>
        <div className="flex items-center gap-2">
          <input type="checkbox" {...register('salary_deposit_detected')} />
          <Label>{t('detail.salaryDeposit')}</Label>
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