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
import { accountCreateSchema } from '@/schemas/account';

interface AccountFormProps {
  customerId: string;
  onSubmit: (data: any) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

const productTypes = ['mortgage', 'personal_loan', 'credit_card', 'auto_loan'] as const;

export function AccountForm({ customerId, onSubmit, onCancel, isLoading }: AccountFormProps) {
  const { t } = useTranslation();

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(accountCreateSchema),
    defaultValues: {
      customer_id: customerId,
      product_type: undefined as any,
      principal_amount: 0,
      interest_rate: 0,
      total_installments: null as number | null,
    },
  });

  const productType = watch('product_type');

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="grid gap-4 py-4">
      <div className="grid gap-2">
        <Label>{t('detail.productType')} *</Label>
        <Select
          value={productType ?? ''}
          onValueChange={(v) => { if (v) setValue('product_type', v as any, { shouldValidate: true }); }}
        >
          <SelectTrigger className="w-full">
            <SelectValue placeholder={t('detail.productType')} />
          </SelectTrigger>
          <SelectContent>
            {productTypes.map((pt) => (
              <SelectItem key={pt} value={pt}>
                {t(`product.${pt}`)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {errors.product_type && (
          <p className="text-xs text-destructive">{errors.product_type.message}</p>
        )}
      </div>

      <div className="grid gap-2">
        <Label>{t('detail.principalAmount')} *</Label>
        <Input
          type="number"
          step="0.01"
          {...register('principal_amount', { valueAsNumber: true })}
        />
        {errors.principal_amount && (
          <p className="text-xs text-destructive">{errors.principal_amount.message}</p>
        )}
      </div>

      <div className="grid gap-2">
        <Label>{t('detail.interestRate')} (0-1) *</Label>
        <Input
          type="number"
          step="0.01"
          min="0"
          max="1"
          {...register('interest_rate', { valueAsNumber: true })}
        />
        {errors.interest_rate && (
          <p className="text-xs text-destructive">{errors.interest_rate.message}</p>
        )}
      </div>

      <div className="grid gap-2">
        <Label>{t('detail.totalInstallments')}</Label>
        <Input
          type="number"
          {...register('total_installments', { valueAsNumber: true })}
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