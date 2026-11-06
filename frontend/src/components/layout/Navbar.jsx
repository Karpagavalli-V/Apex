import React from 'react';
import { Menu, ArrowDownLeft, ArrowUpRight, Sparkles, ShieldCheck } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import Button from '../common/Button';
import { Link } from 'react-router-dom';

export const Navbar = ({ setMobileOpen, onOpenDeposit, onOpenTransfer }) => {
  const { user } = useAuth();
  const firstName = user?.full_name?.trim().split(/\s+/)[0] || user?.username || 'there';

  return (
    <header className="sticky top-0 z-30 h-[72px] bg-white/90 backdrop-blur-xl border-b border-slate-200/70 px-4 sm:px-6 lg:px-8 flex items-center justify-between">
      {/* Left: Mobile Toggle & Page Greeting */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={() => setMobileOpen(true)}
          aria-label="Open navigation menu"
          className="p-2 rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-800 lg:hidden focus:outline-none"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="hidden sm:block">
          <h1 className="text-sm font-semibold text-slate-900 leading-tight">
            Welcome back, <span className="text-brand-700">{firstName}</span>
          </h1>
          <p className="text-[11px] text-slate-500 flex items-center gap-1.5 mt-1">
            <ShieldCheck className="w-3 h-3 text-emerald-600" />
            Your accounts are protected
          </p>
        </div>
      </div>

      {/* Right: Quick Action Hub */}
      <div className="flex items-center gap-2">
        {onOpenDeposit && (
          <Button
            size="sm"
            variant="outline"
            icon={ArrowDownLeft}
            onClick={onOpenDeposit}
            aria-label="Make a deposit"
            className="text-xs"
          >
            Deposit
          </Button>
        )}

        {onOpenTransfer && (
          <Button
            size="sm"
            variant="primary"
            icon={ArrowUpRight}
            onClick={onOpenTransfer}
            aria-label="Make a transfer"
            className="text-xs"
          >
            Transfer
          </Button>
        )}

        <Link
          to="/ai-assistant"
          className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-2 rounded-xl bg-gradient-to-r from-violet-600 to-brand-600 text-white shadow-sm shadow-brand-900/15 hover:shadow-md hover:brightness-105 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2"
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>Ask AI</span>
        </Link>
      </div>
    </header>
  );
};

export default Navbar;
