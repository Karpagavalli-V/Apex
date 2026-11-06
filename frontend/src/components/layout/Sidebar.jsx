import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  CreditCard,
  ArrowLeftRight,
  ReceiptText,
  ShieldAlert,
  Sparkles,
  LogOut,
  Building2,
  User,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import Badge from '../common/Badge';

export const Sidebar = ({ mobileOpen, setMobileOpen }) => {
  const { user, logout } = useAuth();

  const navItems = [
    { name: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
    { name: 'Accounts', to: '/accounts', icon: CreditCard },
    { name: 'Banking Operations', to: '/operations', icon: ArrowLeftRight },
    { name: 'Transactions', to: '/transactions', icon: ReceiptText },
    { name: 'Fraud Monitoring', to: '/fraud-monitoring', icon: ShieldAlert },
    { name: 'AI Financial Assistant', to: '/ai-assistant', icon: Sparkles, badge: 'AI' },
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/50 backdrop-blur-sm lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-64 bg-gradient-to-b from-slate-950 via-slate-900 to-[#101d35] text-white flex flex-col justify-between transition-transform duration-200 ease-in-out border-r border-white/5 shadow-2xl shadow-slate-950/10 lg:translate-x-0 ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand Header */}
        <div>
          <div className="h-20 flex items-center gap-3 px-6 border-b border-white/[0.07]">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-brand-400 to-brand-700 flex items-center justify-center text-white font-bold shadow-lg shadow-brand-500/30 ring-1 ring-white/15">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <div className="font-bold tracking-tight text-white flex items-center gap-2">
                Apex Bank
                <span className="text-[9px] font-bold tracking-wide bg-white/[0.08] text-slate-300 border border-white/10 px-1.5 py-0.5 rounded-md">
                  PLUS
                </span>
              </div>
              <div className="text-[11px] text-slate-400 font-medium">Private banking</div>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-4 space-y-1">
            <div className="px-3 pt-2 pb-3 text-[10px] font-bold tracking-[0.16em] text-slate-500 uppercase">
              Workspace
            </div>

            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={() => setMobileOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                      isActive
                        ? 'bg-white/[0.1] text-white shadow-sm ring-1 ring-white/[0.08] before:absolute before:left-0 before:h-7 before:w-[3px] before:rounded-r-full before:bg-brand-400'
                        : 'text-slate-400 hover:text-white hover:bg-white/[0.05]'
                    }`
                  }
                  style={{ position: 'relative' }}
                >
                  <div className="flex items-center gap-3">
                    <Icon className="w-[17px] h-[17px] shrink-0" />
                    <span>{item.name}</span>
                  </div>
                  {item.badge && (
                    <span className="text-[10px] font-bold bg-amber-400/20 text-amber-300 border border-amber-400/30 px-1.5 py-0.5 rounded-full">
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* User Profile & Logout Bottom Card */}
        <div className="p-4 border-t border-white/[0.07]">
          <div className="flex items-center justify-between p-2.5 rounded-2xl bg-white/[0.045] border border-white/[0.08]">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-9 h-9 rounded-xl bg-brand-500/15 border border-brand-400/20 flex items-center justify-center text-brand-300 font-semibold text-xs shrink-0">
                {user?.username?.charAt(0).toUpperCase() || <User className="w-4 h-4" />}
              </div>
              <div className="min-w-0">
                <p className="text-xs font-semibold text-white truncate leading-tight">
                  {user?.full_name || user?.username}
                </p>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <Badge variant={user?.role} size="sm">
                    {user?.role}
                  </Badge>
                </div>
              </div>
            </div>

            <button
              onClick={logout}
              title="Sign Out"
              aria-label="Sign out"
              className="p-2 rounded-xl text-slate-500 hover:text-rose-300 hover:bg-white/[0.06] transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
