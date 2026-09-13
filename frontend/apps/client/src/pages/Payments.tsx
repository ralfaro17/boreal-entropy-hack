import { useState } from 'react';
import { usePayments } from '@/hooks/usePayments';
import { useAccounts } from '@/hooks/useAccounts';
import { useCustomers } from '@/hooks/useCustomers';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Filter, Inbox } from 'lucide-react';
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

      <Card className="overflow-hidden">
        <CardHeader className="border-b bg-muted/30">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v ?? 'all')}>
              <SelectTrigger className="w-44 bg-background">
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
            {filteredPayments && (
              <span className="ml-auto text-xs text-muted-foreground">
                {filteredPayments.length} {t('payments.title').toLowerCase()}
              </span>
            )}
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/40 hover:bg-muted/40">
                <TableHead className="pl-6">{t('payments.customer')}</TableHead>
                <TableHead>{t('detail.dueDate')}</TableHead>
                <TableHead>{t('detail.amountDue')}</TableHead>
                <TableHead>{t('detail.amountPaid')}</TableHead>
                <TableHead>{t('detail.status')}</TableHead>
                <TableHead>{t('detail.daysLate')}</TableHead>
                <TableHead className="pr-6">{t('detail.paymentMethod')}</TableHead>
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
                  <TableCell colSpan={7} className="h-40 text-center">
                    <div className="flex flex-col items-center gap-2 text-muted-foreground">
                      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
                        <Inbox className="h-6 w-6" />
                      </div>
                      <p className="text-sm">{t('common.noData')}</p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                filteredPayments.map((payment) => (
                  <TableRow key={payment.id}>
                    <TableCell className="pl-6 font-medium">
                      {accountToCustomer.get(payment.account_id) ?? 'N/A'}
                    </TableCell>
                    <TableCell className="text-muted-foreground whitespace-nowrap">
                      {new Date(payment.due_date).toLocaleDateString()}
                    </TableCell>
                    <TableCell className="font-semibold tabular-nums">
                      ${payment.amount_due.toLocaleString()}
                    </TableCell>
                    <TableCell className="tabular-nums text-muted-foreground">
                      {payment.amount_paid != null ? `$${payment.amount_paid.toLocaleString()}` : '—'}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          payment.status === 'on_time'
                            ? 'default'
                            : payment.status === 'missed' || payment.status === 'late'
                            ? 'destructive'
                            : 'secondary'
                        }
                        className={
                          payment.status === 'on_time'
                            ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border-transparent hover:bg-emerald-500/20'
                            : undefined
                        }
                      >
                        {t(`paymentStatus.${payment.status}`)}
                      </Badge>
                    </TableCell>
                    <TableCell className="tabular-nums">
                      {payment.days_late > 0 ? (
                        <span className="text-destructive font-medium">{payment.days_late}</span>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell className="pr-6 text-muted-foreground">
                      {payment.payment_method ? t(`paymentMethod.${payment.payment_method}`) : '—'}
                    </TableCell>
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