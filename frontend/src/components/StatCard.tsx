import { type ReactNode } from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { cn } from '../lib/utils';

interface StatCardProps {
  title: string;
  value: string;
  subtitle?: string;
  icon?: ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  color?: 'blue' | 'green' | 'red' | 'orange' | 'purple' | 'slate';
}

const colorMap: Record<string, { bg: string; icon: string }> = {
  blue: { bg: 'bg-blue-50', icon: 'text-blue-600' },
  green: { bg: 'bg-green-50', icon: 'text-green-600' },
  red: { bg: 'bg-red-50', icon: 'text-red-600' },
  orange: { bg: 'bg-orange-50', icon: 'text-orange-600' },
  purple: { bg: 'bg-purple-50', icon: 'text-purple-600' },
  slate: { bg: 'bg-slate-50', icon: 'text-slate-600' },
};

const trendIcons = {
  up: TrendingUp,
  down: TrendingDown,
  neutral: Minus,
};

export default function StatCard({
  title,
  value,
  subtitle,
  icon,
  trend,
  trendValue,
  color = 'blue',
}: StatCardProps) {
  const colors = colorMap[color] ?? colorMap.blue;
  const TrendIcon = trend ? trendIcons[trend] : null;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-slate-500 truncate">{title}</p>
          <p className="mt-1.5 text-2xl font-bold text-slate-900 break-all leading-tight">{value}</p>
          {(subtitle || trend) && (
            <div className="mt-2 flex items-center gap-1.5">
              {TrendIcon && (
                <TrendIcon
                  className={cn(
                    'w-4 h-4',
                    trend === 'up' && 'text-green-500',
                    trend === 'down' && 'text-red-500',
                    trend === 'neutral' && 'text-slate-400'
                  )}
                />
              )}
              {trendValue && (
                <span
                  className={cn(
                    'text-sm font-medium',
                    trend === 'up' && 'text-green-600',
                    trend === 'down' && 'text-red-600',
                    trend === 'neutral' && 'text-slate-500'
                  )}
                >
                  {trendValue}
                </span>
              )}
              {subtitle && (
                <span className="text-sm text-slate-500">{subtitle}</span>
              )}
            </div>
          )}
        </div>
        {icon && (
          <div className={cn('p-2.5 rounded-lg shrink-0', colors.bg)}>
            <div className={colors.icon}>{icon}</div>
          </div>
        )}
      </div>
    </div>
  );
}
