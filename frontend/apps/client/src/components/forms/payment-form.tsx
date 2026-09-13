import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { paymentCreateSchema } from '@/schemas/payment';

interface PaymentFormProps {
  accountId: string;
  onSubmit: (data: any) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

const paymentStatuses = ['on_time', 'late', 'partial', 'missed', 'reversed', 'grace_period'] as const;
const paymentMethods = ['auto_debit', 'transfer', 'cash', 'card', 'third_party'] as const;
const channels = ['app', 'branch', 'atm', 'call_center', 'web'] as const;

export function PaymentForm({ accountId, onSubmit, onCancel, isLoading }: PaymentFormProps) {
  const { t } = useTranslation();

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(paymentCreateSchema),
    defaultValues: {
      account_id: accountId,
      amount_due: 0,
      due_date: new Date().toISOString().split('T')[0],
      status: 'on_time' as const,
      days_late: 0,
      is_partial_payment: false,
      currency: 'USD',
    },
  });

  const status = watch('status');
  const paymentMethod = watch('payment_method');
  const channel = watch('channel');

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="grid gap-4 py-4">
      <div className="grid gap-2">
        <Label>{t('detail.amountDue')} *</Label>
        <Input
          type="number"
          step="0.01"
          {...register('amount_due', { valueAsNumber: true })}
        />
        {errors.amount_due && (
          <p className="text-xs text-destructive">{errors.amount_due.message}</p>
        )}
      </div>

      <div className="grid gap-2">
        <Label>{t('detail.dueDate')} *</Label>
        <Input type="date" {...register('due_date')} />
        {errors.due_date && (
          <p className="text-xs text-destructive">{errors.due_date.message}</p>
        )}
      </div>

      <div className="grid gap-2">
        <Label>{t('detail.amountPaid')}</Label>
        <Input
          type="number"
          step="0.01"
          {...register('amount_paid', { valueAsNumber: true })}
        />
      </div>

      <div className="grid gap-2">
        <Label>{t('detail.status')}</Label>
        <Select
          value={status ?? 'on_time'}
          onValueChange={(v) => setValue('status', v as any, { shouldValidate: true })}
        >
          <SelectTrigger className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {paymentStatuses.map((s) => (
              <SelectItem key={s} value={s}>
                {t(`paymentStatus.${s}`)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="grid gap-2">
        <Label>{t('detail.paymentMethod')}</Label>
        <Select
          value={paymentMethod ?? ''}
          onValueChange={(v) => setValue('payment_method', (v || null) as any, { shouldValidate: true })}
        >
          <SelectTrigger className="w-full">
            <SelectValue placeholder={t('detail.paymentMethod')} />
          </SelectTrigger>
          <SelectContent>
            {paymentMethods.map((m) => (
              <SelectItem key={m} value={m}>
                {t(`paymentMethod.${m}`)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="grid gap-2">
        <Label>{t('detail.channel')}</Label>
        <Select
          value={channel ?? ''}
          onValueChange={(v) => setValue('channel', (v || null) as any, { shouldValidate: true })}
        >
          <SelectTrigger className="w-full">
            <SelectValue placeholder={t('detail.channel')} />
          </SelectTrigger>
          <SelectContent>
            {channels.map((c) => (
              <SelectItem key={c} value={c}>
                {t(`channel.${c}`)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="grid gap-2">
        <Label>{t('detail.daysLate')}</Label>
        <Input
          type="number"
          min="0"
          {...register('days_late', { valueAsNumber: true })}
        />
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