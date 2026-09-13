import { useState } from 'react';
import { useParams, useNavigate } from 'react-router';
import { useTranslation } from 'react-i18next';
import {
  useCustomer,
  useCustomerAccounts,
  useCustomerRiskFeatures,
  useCustomerActivities,
  useUpdateCustomer,
  useCreateAccount,
  useCreateActivity,
  useCreateRiskFeature,
} from '@/hooks/useCustomers';
import { usePayments, useCreatePayment } from '@/hooks/usePayments';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { ArrowLeft, Pencil, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { PageHeader } from '@/components/page-header';
import { CustomerForm } from '@/components/customer-form';
import { AccountForm } from '@/components/forms/account-form';
import { PaymentForm } from '@/components/forms/payment-form';
import { ActivityForm } from '@/components/forms/activity-form';
import { RiskFeatureForm } from '@/components/forms/risk-feature-form';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { showSuccessToast, showErrorToast } from '@/lib/toast-utils';
import type { CustomerCreateInput } from '@/schemas/customer';
import type { AccountCreateInput } from '@/schemas/account';
import type { PaymentCreateInput } from '@/schemas/payment';

export function CustomerDetail() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [editOpen, setEditOpen] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);
  const [paymentOpen, setPaymentOpen] = useState(false);
  const [activityOpen, setActivityOpen] = useState(false);
  const [riskOpen, setRiskOpen] = useState(false);

  const { data: customer, isLoading: loadingCustomer } = useCustomer(id!);
  const { data: accounts, isLoading: loadingAccounts } = useCustomerAccounts(id!);
  const { data: riskFeatures, isLoading: loadingRisk } = useCustomerRiskFeatures(id!);
  const { data: activities, isLoading: loadingActivities } = useCustomerActivities(id!);
  const { data: allPayments, isLoading: loadingPayments } = usePayments({ limit: 500 });

  const updateCustomer = useUpdateCustomer();
  const createAccount = useCreateAccount();
  const createPayment = useCreatePayment();
  const createActivity = useCreateActivity();
  const createRiskFeature = useCreateRiskFeature();

  const accountIds = new Set(accounts?.map(a => a.id) ?? []);
  const customerPayments = allPayments?.filter(p => accountIds.has(p.account_id)) ?? [];

  const handleEdit = async (data: CustomerCreateInput) => {
    if (!id) return;
    try {
      await updateCustomer.mutateAsync({
        id,
        data: {
          ...data,
          age: data.age ?? null,
          region: data.region || null,
          employment_status: data.employment_status ?? null,
          income_bracket: data.income_bracket || null,
          tenure_months: data.tenure_months ?? null,
          credit_score: data.credit_score ?? null,
        },
      });
      showSuccessToast(t('customers.updateSuccess'));
      setEditOpen(false);
    } catch {
      showErrorToast(t('customers.updateError'));
    }
  };

  const handleCreateAccount = async (data: AccountCreateInput) => {
    try {
      await createAccount.mutateAsync(data);
      showSuccessToast(t('detail.accountCreateSuccess'));
      setAccountOpen(false);
    } catch {
      showErrorToast(t('detail.accountCreateError'));
    }
  };

  const handleCreatePayment = async (data: PaymentCreateInput) => {
    try {
      await createPayment.mutateAsync(data);
      showSuccessToast(t('detail.paymentCreateSuccess'));
      setPaymentOpen(false);
    } catch {
      showErrorToast(t('detail.paymentCreateError'));
    }
  };

  const handleCreateActivity = async (data: any) => {
    try {
      await createActivity.mutateAsync(data);
      showSuccessToast(t('detail.activityCreateSuccess'));
      setActivityOpen(false);
    } catch {
      showErrorToast(t('detail.activityCreateError'));
    }
  };

  const handleCreateRisk = async (data: any) => {
    try {
      await createRiskFeature.mutateAsync(data);
      showSuccessToast(t('detail.riskCreateSuccess'));
      setRiskOpen(false);
    } catch {
      showErrorToast(t('detail.riskCreateError'));
    }
  };

  if (loadingCustomer) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}>
              <CardHeader className="pb-2">
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-16" />
              </CardContent>
            </Card>
          ))}
        </div>
        <Skeleton className="h-10 w-64" />
        <Card>
          <CardContent className="pt-6">
            <Skeleton className="h-48 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!customer) {
    return <div className="text-center py-8">{t('common.noData')}</div>;
  }

  const latestRisk = riskFeatures?.[0];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/customers')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <PageHeader
            title={customer.full_name}
            description={customer.email}
            action={
              <Button variant="outline" onClick={() => setEditOpen(true)}>
                <Pencil className="mr-2 h-4 w-4" />
                {t('common.edit')}
              </Button>
            }
          />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">{t('customers.creditScore')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{customer.credit_score ?? 'N/A'}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">{t('customers.region')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{customer.region ?? 'N/A'}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">{t('customers.employmentStatus')}</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant="outline">
              {customer.employment_status ? t(`employment.${customer.employment_status}`) : 'N/A'}
            </Badge>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">{t('detail.earlyWarning')}</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant={latestRisk?.early_warning_flag ? 'destructive' : 'default'}>
              {latestRisk?.early_warning_flag ? t('detail.earlyWarning') : t('detail.earlyWarning')}
            </Badge>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="accounts">
        <TabsList>
          <TabsTrigger value="accounts">{t('detail.accounts')}</TabsTrigger>
          <TabsTrigger value="payments">{t('detail.payments')}</TabsTrigger>
          <TabsTrigger value="activity">{t('detail.activity')}</TabsTrigger>
          <TabsTrigger value="risk">{t('detail.riskFeatures')}</TabsTrigger>
        </TabsList>

        <TabsContent value="accounts" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>{t('detail.accounts')}</CardTitle>
              <Button size="sm" onClick={() => setAccountOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                {t('detail.addAccount')}
              </Button>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{t('detail.productType')}</TableHead>
                    <TableHead>{t('detail.principalAmount')}</TableHead>
                    <TableHead>{t('detail.interestRate')}</TableHead>
                    <TableHead>{t('detail.status')}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loadingAccounts ? (
                    Array.from({ length: 3 }).map((_, i) => (
                      <TableRow key={i}>
                        {Array.from({ length: 4 }).map((_, j) => (
                          <TableCell key={j}><Skeleton className="h-4 w-full" /></TableCell>
                        ))}
                      </TableRow>
                    ))
                  ) : accounts?.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={4} className="text-center text-muted-foreground">{t('common.noData')}</TableCell>
                    </TableRow>
                  ) : (
                    accounts?.map((account) => (
                      <TableRow key={account.id}>
                        <TableCell>{t(`product.${account.product_type}`)}</TableCell>
                        <TableCell>${account.principal_amount.toLocaleString()}</TableCell>
                        <TableCell>{(account.interest_rate * 100).toFixed(2)}%</TableCell>
                        <TableCell>
                          <Badge variant={account.is_active ? 'default' : 'secondary'}>
                            {account.is_active ? 'Active' : 'Inactive'}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="payments" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>{t('detail.payments')}</CardTitle>
              <Button size="sm" onClick={() => setPaymentOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                {t('detail.addPayment')}
              </Button>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{t('detail.dueDate')}</TableHead>
                    <TableHead>{t('detail.amountDue')}</TableHead>
                    <TableHead>{t('detail.amountPaid')}</TableHead>
                    <TableHead>{t('detail.status')}</TableHead>
                    <TableHead>{t('detail.daysLate')}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loadingPayments || loadingAccounts ? (
                    Array.from({ length: 3 }).map((_, i) => (
                      <TableRow key={i}>
                        {Array.from({ length: 5 }).map((_, j) => (
                          <TableCell key={j}><Skeleton className="h-4 w-full" /></TableCell>
                        ))}
                      </TableRow>
                    ))
                  ) : customerPayments.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center text-muted-foreground">{t('common.noData')}</TableCell>
                    </TableRow>
                  ) : (
                    customerPayments.map((payment) => (
                      <TableRow key={payment.id}>
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
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="activity" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>{t('detail.activity')}</CardTitle>
              <Button size="sm" onClick={() => setActivityOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                {t('detail.addActivity')}
              </Button>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{t('detail.snapshotDate')}</TableHead>
                    <TableHead>{t('detail.checkingBalance')}</TableHead>
                    <TableHead>{t('detail.savingsBalance')}</TableHead>
                    <TableHead>{t('detail.overdraftCount')}</TableHead>
                    <TableHead>{t('detail.appLogins')}</TableHead>
                    <TableHead>{t('detail.status')}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loadingActivities ? (
                    Array.from({ length: 3 }).map((_, i) => (
                      <TableRow key={i}>
                        {Array.from({ length: 6 }).map((_, j) => (
                          <TableCell key={j}><Skeleton className="h-4 w-full" /></TableCell>
                        ))}
                      </TableRow>
                    ))
                  ) : activities?.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center text-muted-foreground">{t('common.noData')}</TableCell>
                    </TableRow>
                  ) : (
                    activities?.map((act) => (
                      <TableRow key={act.id}>
                        <TableCell>{new Date(act.snapshot_date).toLocaleDateString()}</TableCell>
                        <TableCell>{act.checking_balance != null ? `$${act.checking_balance.toLocaleString()}` : '-'}</TableCell>
                        <TableCell>{act.savings_balance != null ? `$${act.savings_balance.toLocaleString()}` : '-'}</TableCell>
                        <TableCell>{act.overdraft_count_30d}</TableCell>
                        <TableCell>{act.app_logins_30d}</TableCell>
                        <TableCell>
                          <div className="flex gap-1">
                            {act.hardship_flag && <Badge variant="destructive">{t('detail.hardshipFlag')}</Badge>}
                            {act.large_withdrawal_flag && <Badge variant="secondary">{t('detail.largeWithdrawal')}</Badge>}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="risk" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>{t('detail.riskFeatures')}</CardTitle>
              <Button size="sm" onClick={() => setRiskOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                {t('detail.addRiskFeature')}
              </Button>
            </CardHeader>
            <CardContent>
              {loadingRisk ? (
                <div className="grid gap-4 md:grid-cols-2">
                  {Array.from({ length: 8 }).map((_, i) => (
                    <div key={i} className="space-y-2">
                      <Skeleton className="h-4 w-32" />
                      <Skeleton className="h-8 w-16" />
                    </div>
                  ))}
                </div>
              ) : !latestRisk ? (
                <div className="text-center py-4 text-muted-foreground">{t('common.noData')}</div>
              ) : (
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <p className="text-sm text-muted-foreground">{t('detail.missedStreak')}</p>
                    <p className="text-2xl font-bold">{latestRisk.missed_payment_streak}</p>
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm text-muted-foreground">{t('detail.consecutivePartial')}</p>
                    <p className="text-2xl font-bold">{latestRisk.consecutive_partial_payments}</p>
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm text-muted-foreground">{t('detail.avgDaysLate')}</p>
                    <p className="text-2xl font-bold">{latestRisk.avg_days_late_90d.toFixed(1)}</p>
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm text-muted-foreground">{t('detail.debtToIncome')}</p>
                    <p className="text-2xl font-bold">
                      {latestRisk.debt_to_income_ratio
                        ? `${(latestRisk.debt_to_income_ratio * 100).toFixed(1)}%`
                        : 'N/A'}
                    </p>
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm text-muted-foreground">{t('detail.creditUtilization')}</p>
                    <p className="text-2xl font-bold">
                      {latestRisk.credit_utilization_pct
                        ? `${latestRisk.credit_utilization_pct.toFixed(1)}%`
                        : 'N/A'}
                    </p>
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm text-muted-foreground">{t('detail.balanceTrend')}</p>
                    <p className="text-2xl font-bold">
                      {latestRisk.balance_trend_30d != null
                        ? `${latestRisk.balance_trend_30d > 0 ? '+' : ''}${latestRisk.balance_trend_30d.toFixed(1)}%`
                        : 'N/A'}
                    </p>
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm text-muted-foreground">{t('detail.defaulted')}</p>
                    <Badge variant={latestRisk.defaulted ? 'destructive' : 'default'}>
                      {latestRisk.defaulted ? 'Yes' : 'No'}
                    </Badge>
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm text-muted-foreground">{t('detail.daysToDefault')}</p>
                    <p className="text-2xl font-bold">{latestRisk.days_to_default ?? 'N/A'}</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Edit Dialog */}
      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent className="sm:max-w-md max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{t('customers.editCustomer')}</DialogTitle>
            <DialogDescription>{t('customers.editDescription')}</DialogDescription>
          </DialogHeader>
          <CustomerForm
            initialData={customer}
            onSubmit={handleEdit}
            isPending={updateCustomer.isPending}
          />
        </DialogContent>
      </Dialog>

      {/* Account Dialog */}
      <Dialog open={accountOpen} onOpenChange={setAccountOpen}>
        <DialogContent className="sm:max-w-md max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{t('detail.addAccount')}</DialogTitle>
            <DialogDescription>{t('detail.addAccount')}</DialogDescription>
          </DialogHeader>
          <AccountForm
            customerId={id!}
            onSubmit={handleCreateAccount}
            onCancel={() => setAccountOpen(false)}
            isLoading={createAccount.isPending}
          />
        </DialogContent>
      </Dialog>

      {/* Payment Dialog */}
      <Dialog open={paymentOpen} onOpenChange={setPaymentOpen}>
        <DialogContent className="sm:max-w-md max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{t('detail.addPayment')}</DialogTitle>
            <DialogDescription>{t('detail.addPayment')}</DialogDescription>
          </DialogHeader>
          <PaymentForm
            accountId={accounts?.[0]?.id ?? ''}
            onSubmit={handleCreatePayment}
            onCancel={() => setPaymentOpen(false)}
            isLoading={createPayment.isPending}
          />
        </DialogContent>
      </Dialog>

      {/* Activity Dialog */}
      <Dialog open={activityOpen} onOpenChange={setActivityOpen}>
        <DialogContent className="sm:max-w-md max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{t('detail.addActivity')}</DialogTitle>
            <DialogDescription>{t('detail.addActivity')}</DialogDescription>
          </DialogHeader>
          <ActivityForm
            customerId={id!}
            onSubmit={handleCreateActivity}
            onCancel={() => setActivityOpen(false)}
            isLoading={createActivity.isPending}
          />
        </DialogContent>
      </Dialog>

      {/* Risk Feature Dialog */}
      <Dialog open={riskOpen} onOpenChange={setRiskOpen}>
        <DialogContent className="sm:max-w-md max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{t('detail.addRiskFeature')}</DialogTitle>
            <DialogDescription>{t('detail.addRiskFeature')}</DialogDescription>
          </DialogHeader>
          <RiskFeatureForm
            customerId={id!}
            onSubmit={handleCreateRisk}
            onCancel={() => setRiskOpen(false)}
            isLoading={createRiskFeature.isPending}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}