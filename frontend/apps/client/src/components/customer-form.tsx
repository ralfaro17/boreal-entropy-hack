import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useTranslation } from 'react-i18next';
import { customerCreateSchema, type CustomerCreateInput } from '@/schemas/customer';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { Customer } from '@/lib/api';

const incomeBrackets = ['low', 'medium', 'high', 'very_high'] as const;

interface CustomerFormProps {
  initialData?: Customer;
  onSubmit: (data: CustomerCreateInput) => Promise<void>;
  isPending?: boolean;
}

export function CustomerForm({ initialData, onSubmit, isPending }: CustomerFormProps) {
  const { t } = useTranslation();

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<CustomerCreateInput>({
    resolver: zodResolver(customerCreateSchema),
    defaultValues: {
      full_name: initialData?.full_name ?? '',
      email: initialData?.email ?? '',
      age: initialData?.age ?? null,
      region: initialData?.region ?? '',
      employment_status: initialData?.employment_status ?? null,
      income_bracket: initialData?.income_bracket ?? '',
      tenure_months: initialData?.tenure_months ?? null,
      credit_score: initialData?.credit_score ?? null,
    },
  });

  const employmentValue = watch('employment_status');
  const incomeValue = watch('income_bracket');

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="grid gap-4 py-4">
      <div className="grid gap-2">
        <Label htmlFor="full_name">{t('customers.name')} *</Label>
        <Input id="full_name" {...register('full_name')} placeholder="Juan Pérez" />
        {errors.full_name && (
          <p className="text-sm text-destructive">{errors.full_name.message}</p>
        )}
      </div>
      <div className="grid gap-2">
        <Label htmlFor="email">{t('customers.email')} *</Label>
        <Input id="email" type="email" {...register('email')} placeholder="juan@ejemplo.com" />
        {errors.email && (
          <p className="text-sm text-destructive">{errors.email.message}</p>
        )}
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="grid gap-2">
          <Label htmlFor="age">{t('customers.age')}</Label>
          <Input id="age" type="number" {...register('age', { valueAsNumber: true })} placeholder="30" />
          {errors.age && (
            <p className="text-sm text-destructive">{errors.age.message}</p>
          )}
        </div>
        <div className="grid gap-2">
          <Label htmlFor="credit_score">{t('customers.creditScore')}</Label>
          <Input id="credit_score" type="number" {...register('credit_score', { valueAsNumber: true })} placeholder="700" />
          {errors.credit_score && (
            <p className="text-sm text-destructive">{errors.credit_score.message}</p>
          )}
        </div>
      </div>
      <div className="grid gap-2">
        <Label htmlFor="region">{t('customers.region')}</Label>
        <Input id="region" {...register('region')} placeholder="San Salvador" />
      </div>
      <div className="grid gap-2">
        <Label>{t('customers.employmentStatus')}</Label>
        <Select
          value={employmentValue ?? ''}
          onValueChange={(val) => setValue('employment_status', val as CustomerCreateInput['employment_status'] || null)}
        >
          <SelectTrigger className="w-full">
            <SelectValue placeholder={t('common.search')} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="employed">{t('employment.employed')}</SelectItem>
            <SelectItem value="self_employed">{t('employment.self_employed')}</SelectItem>
            <SelectItem value="unemployed">{t('employment.unemployed')}</SelectItem>
            <SelectItem value="retired">{t('employment.retired')}</SelectItem>
            <SelectItem value="student">{t('employment.student')}</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="grid gap-2">
          <Label>{t('customers.incomeBracket')}</Label>
          <Select
            value={incomeValue ?? ''}
            onValueChange={(val) => setValue('income_bracket', val || '')}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder={t('customers.incomeBracket')} />
            </SelectTrigger>
            <SelectContent>
              {incomeBrackets.map((bracket) => (
                <SelectItem key={bracket} value={bracket}>
                  {t(`income.${bracket}`)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="grid gap-2">
          <Label htmlFor="tenure_months">{t('customers.tenureMonths')}</Label>
          <Input id="tenure_months" type="number" {...register('tenure_months', { valueAsNumber: true })} placeholder="24" />
        </div>
      </div>
      <div className="flex justify-end gap-2 pt-2">
        <Button type="submit" disabled={isPending}>
          {isPending ? t('common.loading') : initialData ? t('common.save') : t('common.add')}
        </Button>
      </div>
    </form>
  );
}
