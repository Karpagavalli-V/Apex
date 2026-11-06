import React from 'react';
import { AlertCircle, CheckCircle2, AlertTriangle, Info, X } from 'lucide-react';

export const Alert = ({
  variant = 'info',
  title,
  children,
  onClose,
  className = '',
}) => {
  const styles = {
    info: {
      container: 'bg-blue-50 border-blue-200 text-blue-900',
      icon: Info,
      iconColor: 'text-blue-500',
    },
    success: {
      container: 'bg-emerald-50 border-emerald-200 text-emerald-900',
      icon: CheckCircle2,
      iconColor: 'text-emerald-500',
    },
    warning: {
      container: 'bg-amber-50 border-amber-200 text-amber-900',
      icon: AlertTriangle,
      iconColor: 'text-amber-500',
    },
    error: {
      container: 'bg-rose-50 border-rose-200 text-rose-900',
      icon: AlertCircle,
      iconColor: 'text-rose-500',
    },
  };

  const selected = styles[variant] || styles.info;
  const Icon = selected.icon;

  return (
    <div
      className={`rounded-xl border p-4 flex items-start gap-3 text-sm shadow-sm transition-all ${selected.container} ${className}`}
    >
      <Icon className={`w-5 h-5 shrink-0 mt-0.5 ${selected.iconColor}`} />
      <div className="flex-1">
        {title && <h5 className="font-semibold text-slate-900 mb-0.5">{title}</h5>}
        <div className="leading-relaxed">{children}</div>
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-slate-600 rounded p-1"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};

export default Alert;
