import { useState } from 'react';
import { NavLink } from 'react-router';
import { LayoutDashboard, Users, CreditCard, MessageSquare, Phone, Moon, Sun, Menu, Globe, Snowflake } from 'lucide-react';
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
    { to: '/call', icon: Phone, label: t('nav.call') },
  ];

  return (
    <nav className="space-y-1 p-4">
      <p className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground/70">
        Menu
      </p>
      {navItems.map(({ to, icon: Icon, label }) => (
        <NavLink
          key={to}
          to={to}
          end={to === '/'}
          onClick={onNavigate}
          className={({ isActive }) =>
            cn(
              'group relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200',
              isActive
                ? 'bg-primary/10 text-primary shadow-none before:absolute before:left-0 before:top-1/2 before:-translate-y-1/2 before:h-5 before:w-1 before:rounded-full before:bg-primary'
                : 'text-muted-foreground hover:bg-muted hover:text-foreground hover:translate-x-0.5'
            )
          }
        >
          <Icon className="h-4 w-4 shrink-0 transition-transform duration-200 group-hover:scale-110" />
          {label}
        </NavLink>
      ))}
    </nav>
  );
}

function Brand({ compact = false }: { compact?: boolean }) {
  return (
    <div className="flex items-center gap-2.5">
      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-linear-to-br from-primary to-chart-2 text-primary-foreground shadow-md shadow-primary/25">
        <Snowflake className="h-4.5 w-4.5" />
      </div>
      <div className="leading-tight">
        <span className={cn('font-bold tracking-tight', compact ? 'text-base' : 'text-[15px]')}>
          Boreal <span className="text-primary">Entropy</span>
        </span>
        {!compact && (
          <p className="text-[10px] font-medium uppercase tracking-widest text-muted-foreground">
            Risk Console
          </p>
        )}
      </div>
    </div>
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
      <SelectTrigger className="w-25 h-8 text-xs">
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
      <div className="flex items-center justify-between border-b bg-sidebar/80 backdrop-blur-md px-4 h-14 sticky top-0 z-40">
        <Sheet>
          <SheetTrigger render={<Button variant="ghost" size="icon" />}>
            <Menu className="h-5 w-5" />
          </SheetTrigger>
          <SheetContent side="left" className="w-64 p-0">
            <SheetHeader className="border-b px-4 py-4">
              <SheetTitle>
                <Brand compact />
              </SheetTitle>
            </SheetHeader>
            <NavLinks />
          </SheetContent>
        </Sheet>
        <Brand compact />
        <div className="flex items-center gap-1">
          <LanguageSwitcher />
          <ThemeToggle />
        </div>
      </div>
    );
  }

  return (
    <aside className="w-64 border-r bg-sidebar flex flex-col">
      <div className="flex h-16 items-center border-b px-4">
        <Brand />
      </div>
      <div className="flex-1">
        <NavLinks />
      </div>
      <div className="border-t p-4 flex items-center justify-between gap-2">
        <LanguageSwitcher />
        <ThemeToggle />
      </div>
    </aside>
  );
}
