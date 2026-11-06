import React from 'react';

export const Badge = ({ children, variant = 'default', size = 'md', className = '' }) => {
  const variantStyles = {
    // Transaction Risk Tiers
    NORMAL: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    SUSPICIOUS: 'bg-amber-50 text-amber-700 border-amber-200',
    HIGH_RISK: 'bg-rose-50 text-rose-700 border-rose-200 animate-pulse',

    // Account & Transaction Statuses
    ACTIVE: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    COMPLETED: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    FROZEN: 'bg-slate-100 text-slate-700 border-slate-300',
    CLOSED: 'bg-slate-100 text-slate-500 border-slate-200',
    FAILED: 'bg-rose-50 text-rose-700 border-rose-200',

    // Cash flow health
    EXCELLENT: 'bg-emerald-100 text-emerald-800 border-emerald-300 font-semibold',
    GOOD: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    BALANCED: 'bg-blue-50 text-blue-700 border-blue-200',
    DEFICIT: 'bg-rose-50 text-rose-700 border-rose-200',
    STRONG: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    MODERATE: 'bg-blue-50 text-blue-700 border-blue-200',
    AT_RISK: 'bg-amber-50 text-amber-700 border-amber-200',
    NEGATIVE_CASH_FLOW: 'bg-rose-50 text-rose-700 border-rose-200',

    // Roles & Defaults
    admin: 'bg-purple-50 text-purple-700 border-purple-200 font-semibold',
    customer: 'bg-slate-100 text-slate-700 border-slate-200',
    default: 'bg-slate-100 text-slate-700 border-slate-200',
    brand: 'bg-brand-50 text-brand-700 border-brand-200',
  };

  const sizeStyles = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs px-2.5 py-1',
    lg: 'text-sm px-3 py-1.5',
  };

  const dotColors = {
    NORMAL: 'bg-emerald-500',
    SUSPICIOUS: 'bg-amber-500',
    HIGH_RISK: 'bg-rose-500',
    ACTIVE: 'bg-emerald-500',
    COMPLETED: 'bg-emerald-500',
    EXCELLENT: 'bg-emerald-500',
    DEFICIT: 'bg-rose-500',
  };

  const selectedVariant = variantStyles[variant] || variantStyles.default;
  const dotColor = dotColors[variant];

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-medium rounded-full border ${selectedVariant} ${sizeStyles[size]} ${className}`}
    >
      {dotColor && <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />}
      {children || variant}
    </span>
  );
};

export default Badge;
