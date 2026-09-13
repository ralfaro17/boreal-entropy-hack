import { useState } from 'react';
import { useCustomers, useDeleteCustomer, useCreateCustomer } from '@/hooks/useCustomers';
import { useNavigate } from 'react-router';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { PageHeader } from '@/components/page-header';
import { CustomerForm } from '@/components/customer-form';
import { ConfirmDialog } from '@/components/confirm-dialog';
import { Skeleton } from '@/components/ui/skeleton';
import { Plus, Search, Trash2, Eye, Users } from 'lucide-react';
import { showSuccessToast, showErrorToast } from '@/lib/toast-utils';
import type { Customer } from '@/lib/api';

export function Customers() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [createOpen, setCreateOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Customer | null>(null);
  const { data: customers, isLoading } = useCustomers({ limit: 100 });
  const deleteCustomer = useDeleteCustomer();
  const createCustomer = useCreateCustomer();

  const filteredCustomers = customers?.filter(
    (c) =>
      c.full_name.toLowerCase().includes(search.toLowerCase()) ||
      c.email.toLowerCase().includes(search.toLowerCase())
  );

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteCustomer.mutateAsync(deleteTarget.id);
      showSuccessToast(t('customers.deleteSuccess'));
      setDeleteTarget(null);
    } catch {
      showErrorToast(t('customers.deleteError'));
    }
  };

  const handleCreate = async (data: Parameters<typeof createCustomer.mutateAsync>[0]) => {
    try {
      await createCustomer.mutateAsync(data);
      showSuccessToast(t('customers.createSuccess'));
      setCreateOpen(false);
    } catch {
      showErrorToast(t('customers.createError'));
    }
  };

  const getEmploymentBadge = (status: Customer['employment_status']) => {
    if (!status) return <Badge variant="outline">N/A</Badge>;
    const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
      employed: 'default',
      self_employed: 'secondary',
      unemployed: 'destructive',
      retired: 'outline',
      student: 'outline',
    };
    return <Badge variant={variants[status] ?? 'outline'}>{t(`employment.${status}`)}</Badge>;
  };

  const getInitials = (name: string) =>
    name
      .split(' ')
      .map((n) => n[0])
      .slice(0, 2)
      .join('')
      .toUpperCase();

  const getCreditScoreColor = (score: number | null | undefined) => {
    if (score == null) return 'text-muted-foreground';
    if (score >= 740) return 'text-emerald-600 dark:text-emerald-400';
    if (score >= 620) return 'text-amber-600 dark:text-amber-400';
    return 'text-destructive';
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title={t('customers.title')}
        description={t('customers.description')}
        action={
          <Button onClick={() => setCreateOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            {t('customers.addCustomer')}
          </Button>
        }
      />

      <Card className="overflow-hidden">
        <CardHeader className="border-b bg-muted/30">
          <div className="relative max-w-sm">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder={t('customers.search')}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 bg-background"
            />
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/40 hover:bg-muted/40">
                <TableHead className="pl-6">{t('customers.name')}</TableHead>
                <TableHead>{t('customers.email')}</TableHead>
                <TableHead>{t('customers.region')}</TableHead>
                <TableHead>{t('customers.employmentStatus')}</TableHead>
                <TableHead>{t('customers.creditScore')}</TableHead>
                <TableHead className="text-right pr-6">{t('common.actions')}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={i}>
                    {Array.from({ length: 6 }).map((_, j) => (
                      <TableCell key={j}>
                        <Skeleton className="h-4 w-full" />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : filteredCustomers?.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="h-40 text-center">
                    <div className="flex flex-col items-center gap-2 text-muted-foreground">
                      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
                        <Users className="h-6 w-6" />
                      </div>
                      <p className="text-sm">{t('customers.noResults')}</p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                filteredCustomers?.map((customer) => (
                  <TableRow
                    key={customer.id}
                    className="cursor-pointer group"
                    onClick={() => navigate(`/customers/${customer.id}`)}
                  >
                    <TableCell className="pl-6">
                      <div className="flex items-center gap-3">
                        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary text-xs font-semibold">
                          {getInitials(customer.full_name)}
                        </div>
                        <span className="font-medium">{customer.full_name}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-muted-foreground">{customer.email}</TableCell>
                    <TableCell>{customer.region ?? <span className="text-muted-foreground">N/A</span>}</TableCell>
                    <TableCell>{getEmploymentBadge(customer.employment_status)}</TableCell>
                    <TableCell>
                      <span className={`font-semibold tabular-nums ${getCreditScoreColor(customer.credit_score)}`}>
                        {customer.credit_score ?? 'N/A'}
                      </span>
                    </TableCell>
                    <TableCell className="text-right pr-6">
                      <div className="flex justify-end gap-1 opacity-60 group-hover:opacity-100 transition-opacity">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/customers/${customer.id}`);
                          }}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="hover:text-destructive"
                          onClick={(e) => {
                            e.stopPropagation();
                            setDeleteTarget(customer);
                          }}
                          disabled={deleteCustomer.isPending}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Create Dialog */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="sm:max-w-md max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{t('customers.addCustomer')}</DialogTitle>
            <DialogDescription>{t('customers.addDescription')}</DialogDescription>
          </DialogHeader>
          <CustomerForm
            onSubmit={handleCreate}
            isPending={createCustomer.isPending}
          />
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title={t('common.delete')}
        description={`${t('common.confirmDelete')} ${deleteTarget?.full_name}?`}
        confirmLabel={t('common.delete')}
        onConfirm={handleDelete}
        isPending={deleteCustomer.isPending}
      />
    </div>
  );
}