import { useState } from 'react';
import { usePayments } from '@/hooks/usePayments';
import { useAccounts } from '@/hooks/useAccounts';
import { useCustomers } from '@/hooks/useCustomers';
import { useTranslation } from 'react-i18next';
import { Card, CardContent } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/page-header';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

const paymentStatuses = ['on_time', 'late', 'partial', 'missed', 'reversed', 'grace_period'] as const;

export function Payments() {
  const { t } = useTranslation();
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const { data: payments, isLoading: loadingPayments } = usePayments({ limit: 500 });
  const { data: accounts, isLoading: loadingAccounts } = useAccounts({ limit: 500 });
  const { data: customers, isLoading: loadingCustomers } = useCustomers({ limit: 500 });

  const accountToCustomer = new Map<string, string>();
  for (const account of accounts ?? []) {
    const customer = customers?.find(c => c.id === account.customer_id);
    if (customer) {
      accountToCustomer.set(account.id, customer.full_name);
    }
  }

  const filteredPayments = payments?.filter(p =>
    statusFilter === 'all' || p.status === statusFilter
  );

  const isLoading = loadingPayments || loadingAccounts || loadingCustomers;

  return (
    <div className="space-y-6">
      <PageHeader
        title={t('payments.title')}
        description={t('payments.description')}
      />

      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4 mb-4">
            <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v ?? 'all')}>
              <SelectTrigger className="w-44">
                <SelectValue placeholder={t('payments.allStatus')} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t('payments.allStatus')}</SelectItem>
                {paymentStatuses.map((s) => (
                  <SelectItem key={s} value={s}>
                    {t(`paymentStatus.${s}`)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t('payments.customer')}</TableHead>
                <TableHead>{t('detail.dueDate')}</TableHead>
                <TableHead>{t('detail.amountDue')}</TableHead>
                <TableHead>{t('detail.amountPaid')}</TableHead>
                <TableHead>{t('detail.status')}</TableHead>
                <TableHead>{t('detail.daysLate')}</TableHead>
                <TableHead>{t('detail.paymentMethod')}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                Array.from({ length: 8 }).map((_, i) => (
                  <TableRow key={i}>
                    {Array.from({ length: 7 }).map((_, j) => (
                      <TableCell key={j}><Skeleton className="h-4 w-full" /></TableCell>
                    ))}
                  </TableRow>
                ))
              ) : !filteredPayments?.length ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center text-muted-foreground">
                    {t('common.noData')}
                  </TableCell>
                </TableRow>
              ) : (
                filteredPayments.map((payment) => (
                  <TableRow key={payment.id}>
                    <TableCell className="font-medium">
                      {accountToCustomer.get(payment.account_id) ?? 'N/A'}
                    </TableCell>
                    <TableCell>{new Date(payment.due_date).toLocaleDateString()}</TableCell>
                    <TableCell>${payment.amount_due.toLocaleString()}</TableCell>
                    <TableCell>{payment.amount_paid != null ? `$${payment.amount_paid.toLocaleString()}` : '-'}</TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          payment.status === 'on_time'
                            ? 'default'
                            : payment.status === 'missed' || payment.status === 'late'
                            ? 'destructive'
                            : 'secondary'
                        }
                      >
                        {t(`paymentStatus.${payment.status}`)}
                      </Badge>
                    </TableCell>
                    <TableCell>{payment.days_late > 0 ? payment.days_late : '-'}</TableCell>
                    <TableCell>{payment.payment_method ? t(`paymentMethod.${payment.payment_method}`) : '-'}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}