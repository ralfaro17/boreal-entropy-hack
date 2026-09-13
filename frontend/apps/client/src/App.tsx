import { BrowserRouter, Route, Routes } from 'react-router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { Toaster } from '@/components/ui/toast';
import { Sidebar } from '@/components/layout/Sidebar';
import { Dashboard } from './pages/Dashboard';
import { Customers } from './pages/Customers';
import { CustomerDetail } from './pages/CustomerDetail';
import { Payments } from './pages/Payments';
import { Chat } from './pages/Chat';
import { CustomerChat } from './pages/CustomerChat';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function InternalLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen flex-col md:flex-row bg-background">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <div className="mx-auto max-w-7xl p-4 md:p-8">{children}</div>
      </main>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Toaster />
      <BrowserRouter>
        <Routes>
          {/* Customer Portal route: users can view & respond to AI reminders */}
          <Route path="/chat/:customerId" element={<CustomerChat />} />
          <Route path="/portal/chat/:customerId" element={<CustomerChat />} />

          {/* Internal Console routes */}
          <Route
            path="/"
            element={
              <InternalLayout>
                <Dashboard />
              </InternalLayout>
            }
          />
          <Route
            path="/customers"
            element={
              <InternalLayout>
                <Customers />
              </InternalLayout>
            }
          />
          <Route
            path="/customers/:id"
            element={
              <InternalLayout>
                <CustomerDetail />
              </InternalLayout>
            }
          />
          <Route
            path="/payments"
            element={
              <InternalLayout>
                <Payments />
              </InternalLayout>
            }
          />
          <Route
            path="/chat"
            element={
              <InternalLayout>
                <Chat />
              </InternalLayout>
            }
          />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
