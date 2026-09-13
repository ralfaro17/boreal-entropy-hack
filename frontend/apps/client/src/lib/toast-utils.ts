import { toast } from '@/components/ui/toast';

export function showSuccessToast(message: string) {
  toast.add({
    title: message,
    type: 'success',
  });
}

export function showErrorToast(message: string) {
  toast.add({
    title: message,
    type: 'error',
  });
}
