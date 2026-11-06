import React from 'react';

export const StatCard = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  trendLabel,
  colorScheme = 'brand',
  accentColor,
  loading = false,
  className = '',
}) => {
  const iconColors = {
    brand: 'bg-brand-50 text-brand-600 border-brand-100',
    indigo: 'bg-indigo-50 text-indigo-600 border-indigo-100',
    emerald: 'bg-emerald-50 text-emerald-600 border-emerald-100',
    rose: 'bg-rose-50 text-rose-600 border-rose-100',
    amber: 'bg-amber-50 text-amber-600 border-amber-100',
    slate: 'bg-slate-100 text-slate-700 border-slate-200',
    purple: 'bg-purple-50 text-purple-600 border-purple-100',
  };

  const selectedIconStyle = iconColors[accentColor || colorScheme] || iconColors.brand;

  return (
    <div
      className={`group relative overflow-hidden bg-white rounded-2xl border border-slate-200/80 p-5 shadow-card hover:-translate-y-0.5 hover:shadow-hover transition-all duration-200 flex flex-col justify-between ${className}`}
    >
      <div className="flex items-center justify-between gap-4">
        <span className="text-sm font-medium text-slate-500 line-clamp-1">{title}</span>
        {Icon && (
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center border transition-transform duration-200 group-hover:scale-105 ${selectedIconStyle}`}>
            <Icon className="w-[18px] h-[18px]" />
          </div>
        )}
      </div>

      <div className="mt-3">
        {loading ? (
          <div className="space-y-2.5" role="status" aria-label={`Loading ${title}`}>
            <div className="h-7 w-3/4 rounded-md bg-slate-100 animate-pulse" />
            <div className="h-3 w-1/2 rounded bg-slate-100 animate-pulse" />
          </div>
        ) : (
          <>
            <div className="text-2xl font-bold tracking-tight text-slate-900 tabular-nums">{value}</div>
            {(subtitle || trend) && (
              <div className="mt-1.5 flex items-center gap-2 text-xs">
                {trend !== undefined && trend !== null && (
                  <span
                    className={`font-semibold inline-flex items-center px-1.5 py-0.5 rounded-md ${
                      trend >= 0 ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'
                    }`}
                  >
                    {trend >= 0 ? `+${trend}%` : `${trend}%`}
                  </span>
                )}
                <span className="text-slate-500">{trendLabel || subtitle}</span>
              </div>
            )}
          </>
        )}
      </div>
      <div className="absolute inset-x-0 bottom-0 h-0.5 bg-gradient-to-r from-transparent via-slate-200 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
    </div>
  );
};

export default StatCard;
