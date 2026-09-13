import { useState } from 'react';
import { NavLink } from 'react-router';
import { LayoutDashboard, Users, CreditCard, MessageSquare, Moon, Sun, Menu, Globe } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/utils';
import { useIsMobile } from '@/hooks/use-mobile';
import { Button } from '@/components/ui/button';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const { t } = useTranslation();

  const navItems = [
    { to: '/', icon: LayoutDashboard, label: t('nav.dashboard') },
    { to: '/customers', icon: Users, label: t('nav.customers') },
    { to: '/payments', icon: CreditCard, label: t('nav.payments') },
    { to: '/chat', icon: MessageSquare, label: t('nav.chat') },
  ];

  return (
    <nav className="space-y-1 p-4">
      {navItems.map(({ to, icon: Icon, label }) => (
        <NavLink
          key={to}
          to={to}
          end={to === '/'}
          onClick={onNavigate}
          className={({ isActive }) =>
            cn(
              'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
              isActive
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:bg-muted hover:text-foreground'
            )
          }
        >
          <Icon className="h-4 w-4" />
          {label}
        </NavLink>
      ))}
    </nav>
  );
}

function ThemeToggle() {
  const [dark, setDark] = useState(
    () => document.documentElement.classList.contains('dark')
  );

  const toggle = () => {
    setDark(!dark);
    document.documentElement.classList.toggle('dark', !dark);
  };

  return (
    <Button variant="ghost" size="icon" onClick={toggle}>
      {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
    </Button>
  );
}

function LanguageSwitcher() {
  const { i18n } = useTranslation();

  return (
    <Select
      value={i18n.language}
      onValueChange={(val) => i18n.changeLanguage(val ?? undefined)}
    >
      <SelectTrigger className="w-[100px] h-8 text-xs">
        <Globe className="h-3 w-3 mr-1" />
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="es">ES</SelectItem>
        <SelectItem value="en">EN</SelectItem>
      </SelectContent>
    </Select>
  );
}

export function Sidebar() {
  const isMobile = useIsMobile();

  if (isMobile) {
    return (
      <div className="flex items-center justify-between border-b px-4 h-14">
        <Sheet>
          <SheetTrigger render={<Button variant="ghost" size="icon" />}>
            <Menu className="h-5 w-5" />
          </SheetTrigger>
          <SheetContent side="left" className="w-64 p-0">
            <SheetHeader className="border-b px-6 py-4">
              <SheetTitle className="text-xl font-bold">Boreal Entropy</SheetTitle>
            </SheetHeader>
            <NavLinks />
          </SheetContent>
        </Sheet>
        <span className="text-lg font-bold">Boreal Entropy</span>
        <div className="flex items-center gap-1">
          <LanguageSwitcher />
          <ThemeToggle />
        </div>
      </div>
    );
  }

  return (
    <aside className="w-64 border-r bg-muted/40 flex flex-col">
      <div className="flex h-16 items-center justify-between border-b px-6">
        <span className="text-xl font-bold">Boreal Entropy</span>
        <div className="flex items-center gap-1">
          <LanguageSwitcher />
          <ThemeToggle />
        </div>
      </div>
      <NavLinks />
    </aside>
  );
}
