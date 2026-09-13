import { useCustomers } from '@/hooks/useCustomers';
import { useAccounts } from '@/hooks/useAccounts';
import { usePayments } from '@/hooks/usePayments';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { PageHeader } from '@/components/page-header';
import { Users, CreditCard, DollarSign, AlertTriangle } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useTranslation } from 'react-i18next';

function buildChartData(payments: { due_date: string; amount_due: number; status: string }[]) {
  const byMonth: Record<string, { total: number; missed: number }> = {};

  for (const p of payments) {
    const d = new Date(p.due_date);
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
    if (!byMonth[key]) byMonth[key] = { total: 0, missed: 0 };
    byMonth[key].total += p.amount_due;
    if (p.status === 'missed') byMonth[key].missed += p.amount_due;
  }

  return Object.entries(byMonth)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([month, data]) => ({
      name: month,
      total: Math.round(data.total),
      missed: Math.round(data.missed),
    }));
}

export function Dashboard() {
  const { t } = useTranslation();
  const { data: customers, isLoading: loadingCustomers } = useCustomers({ limit: 500 });
  const { data: accounts, isLoading: loadingAccounts } = useAccounts({ limit: 500 });
  const { data: payments, isLoading: loadingPayments } = usePayments({ limit: 500 });

  const totalCustomers = customers?.length ?? 0;
  const totalAccounts = accounts?.length ?? 0;
  const activeAccounts = accounts?.filter(a => a.is_active).length ?? 0;
  const totalPayments = payments?.length ?? 0;
  const missedPayments = payments?.filter(p => p.status === 'missed').length ?? 0;
  const chartData = payments ? buildChartData(payments) : [];

  return (
    <div className="space-y-6">
      <PageHeader
        title={t('dashboard.title')}
        description={t('dashboard.description')}
      />

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('dashboard.totalCustomers')}</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {loadingCustomers ? (
              <Skeleton className="h-8 w-12" />
            ) : (
              <div className="text-2xl font-bold">{totalCustomers}</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('dashboard.activeAccounts')}</CardTitle>
            <CreditCard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {loadingAccounts ? (
              <Skeleton className="h-8 w-12" />
            ) : (
              <>
                <div className="text-2xl font-bold">{activeAccounts}</div>
                <p className="text-xs text-muted-foreground">
                  / {totalAccounts}
                </p>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('dashboard.totalPayments')}</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {loadingPayments ? (
              <Skeleton className="h-8 w-12" />
            ) : (
              <div className="text-2xl font-bold">{totalPayments}</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t('dashboard.missedPayments')}</CardTitle>
            <AlertTriangle className="h-4 w-4 text-destructive" />
          </CardHeader>
          <CardContent>
            {loadingPayments ? (
              <Skeleton className="h-8 w-12" />
            ) : (
              <div className="text-2xl font-bold text-destructive">{missedPayments}</div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t('dashboard.chartTitle')}</CardTitle>
        </CardHeader>
        <CardContent>
          {loadingPayments ? (
            <Skeleton className="h-[350px] w-full" />
          ) : chartData.length === 0 ? (
            <div className="flex items-center justify-center h-[350px] text-muted-foreground">
              {t('common.noData')}
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={350}>
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip formatter={(value) => [`$${Number(value).toLocaleString()}`, '']} />
                <Area type="monotone" dataKey="total" stackId="1" stroke="#8884d8" fill="#8884d8" name="Total" />
                <Area type="monotone" dataKey="missed" stackId="2" stroke="#ef4444" fill="#fecaca" name="Missed" />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>
    </div>
  );
}