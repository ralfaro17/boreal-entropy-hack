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
import { Plus, Search, Trash2, Eye } from 'lucide-react';
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

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Search className="h-4 w-4 text-muted-foreground" />
            <Input
              placeholder={t('customers.search')}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="max-w-sm"
            />
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t('customers.name')}</TableHead>
                <TableHead>{t('customers.email')}</TableHead>
                <TableHead>{t('customers.region')}</TableHead>
                <TableHead>{t('customers.employmentStatus')}</TableHead>
                <TableHead>{t('customers.creditScore')}</TableHead>
                <TableHead>{t('common.actions')}</TableHead>
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
                  <TableCell colSpan={6} className="text-center text-muted-foreground">
                    {t('customers.noResults')}
                  </TableCell>
                </TableRow>
              ) : (
                filteredCustomers?.map((customer) => (
                  <TableRow key={customer.id}>
                    <TableCell className="font-medium">{customer.full_name}</TableCell>
                    <TableCell>{customer.email}</TableCell>
                    <TableCell>{customer.region ?? 'N/A'}</TableCell>
                    <TableCell>{getEmploymentBadge(customer.employment_status)}</TableCell>
                    <TableCell>{customer.credit_score ?? 'N/A'}</TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => navigate(`/customers/${customer.id}`)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => setDeleteTarget(customer)}
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