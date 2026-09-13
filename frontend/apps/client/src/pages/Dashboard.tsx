import type { ComponentType, ReactNode } from 'react';
import { useCustomers } from '@/hooks/useCustomers';
import { useAccounts } from '@/hooks/useAccounts';
import { usePayments } from '@/hooks/usePayments';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { PageHeader } from '@/components/page-header';
import { Users, CreditCard, DollarSign, AlertTriangle, TrendingUp } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/utils';

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

interface StatCardProps {
  title: string;
  icon: ComponentType<{ className?: string }>;
  loading: boolean;
  value: ReactNode;
  sub?: ReactNode;
  tone?: 'primary' | 'violet' | 'emerald' | 'destructive';
}

const tones = {
  primary: {
    iconWrap: 'bg-primary/10 text-primary',
    bar: 'from-primary/60 to-primary',
  },
  violet: {
    iconWrap: 'bg-chart-2/15 text-chart-2',
    bar: 'from-chart-2/60 to-chart-2',
  },
  emerald: {
    iconWrap: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
    bar: 'from-emerald-500/60 to-emerald-500',
  },
  destructive: {
    iconWrap: 'bg-destructive/10 text-destructive',
    bar: 'from-destructive/60 to-destructive',
  },
} as const;

function StatCard({ title, icon: Icon, loading, value, sub, tone = 'primary' }: StatCardProps) {
  const t = tones[tone];
  return (
    <Card className="relative overflow-hidden transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5">
      <div className={cn('absolute inset-x-0 top-0 h-1 bg-linear-to-r', t.bar)} />
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <div className={cn('flex h-9 w-9 items-center justify-center rounded-lg', t.iconWrap)}>
          <Icon className="h-4.5 w-4.5" />
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-8 w-14" />
        ) : (
          <>
            <div className="text-3xl font-bold tracking-tight">{value}</div>
            {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
          </>
        )}
      </CardContent>
    </Card>
  );
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
        <StatCard
          title={t('dashboard.totalCustomers')}
          icon={Users}
          loading={loadingCustomers}
          value={totalCustomers}
          tone="primary"
        />
        <StatCard
          title={t('dashboard.activeAccounts')}
          icon={CreditCard}
          loading={loadingAccounts}
          value={activeAccounts}
          sub={`of ${totalAccounts} total`}
          tone="violet"
        />
        <StatCard
          title={t('dashboard.totalPayments')}
          icon={DollarSign}
          loading={loadingPayments}
          value={totalPayments}
          tone="emerald"
        />
        <StatCard
          title={t('dashboard.missedPayments')}
          icon={AlertTriangle}
          loading={loadingPayments}
          value={<span className="text-destructive">{missedPayments}</span>}
          sub={
            totalPayments > 0
              ? `${((missedPayments / totalPayments) * 100).toFixed(1)}% of payments`
              : undefined
          }
          tone="destructive"
        />
      </div>

      <Card className="overflow-hidden">
        <CardHeader className="border-b bg-muted/30">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <TrendingUp className="h-4 w-4" />
            </div>
            <div>
              <CardTitle className="text-base">{t('dashboard.chartTitle')}</CardTitle>
              <CardDescription className="text-xs">Total vs missed payment volume by month</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-6">
          {loadingPayments ? (
            <Skeleton className="h-87.5 w-full" />
          ) : chartData.length === 0 ? (
            <div className="flex items-center justify-center h-87.5 text-muted-foreground">
              {t('common.noData')}
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={350}>
              <AreaChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="fillTotal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--chart-1)" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="var(--chart-1)" stopOpacity={0.02} />
                  </linearGradient>
                  <linearGradient id="fillMissed" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--destructive)" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="var(--destructive)" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 12, fill: 'var(--muted-foreground)' }}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  tick={{ fontSize: 12, fill: 'var(--muted-foreground)' }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(v) => `$${Number(v).toLocaleString()}`}
                  width={80}
                />
                <Tooltip
                  formatter={(value) => [`$${Number(value).toLocaleString()}`, '']}
                  contentStyle={{
                    background: 'var(--popover)',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--radius)',
                    color: 'var(--popover-foreground)',
                    fontSize: 13,
                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="total"
                  stroke="var(--chart-1)"
                  strokeWidth={2}
                  fill="url(#fillTotal)"
                  name="Total"
                />
                <Area
                  type="monotone"
                  dataKey="missed"
                  stroke="var(--destructive)"
                  strokeWidth={2}
                  fill="url(#fillMissed)"
                  name="Missed"
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>
    </div>
  );
}