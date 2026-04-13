export function formatCurrency(value: number | null | undefined, currency = 'INR'): string {
  if (value == null) return '₹0';
  const abs = Math.abs(value);
  const sign = value < 0 ? '-' : '';
  if (currency === 'USD') return `${sign}$${abs.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
  if (currency === 'EUR' || currency === 'Euro') return `${sign}€${abs.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
  return `${sign}₹${abs.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
}

export function formatNumber(value: number | null | undefined): string {
  if (value == null) return '0';
  return value.toLocaleString('en-IN', { maximumFractionDigits: 0 });
}

export function formatPercent(value: number | null | undefined): string {
  if (value == null) return '0%';
  return `${value.toFixed(1)}%`;
}

export const MONTHS = [
  'Apr-25', 'May-25', 'Jun-25', 'Jul-25', 'Aug-25', 'Sep-25',
  'Oct-25', 'Nov-25', 'Dec-25', 'Jan-26', 'Feb-26', 'Mar-26'
] as const;

export const MONTH_LABELS = [
  'April', 'May', 'June', 'July', 'August', 'September',
  'October', 'November', 'December', 'January', 'February', 'March'
] as const;

export function cn(...classes: (string | boolean | undefined | null)[]): string {
  return classes.filter(Boolean).join(' ');
}

export function getVarianceColor(variance: number): string {
  if (variance > 0) return 'text-red-600';
  if (variance < 0) return 'text-green-600';
  return 'text-gray-500';
}

export function getStatusColor(status: string): string {
  const s = status?.toLowerCase();
  if (s === 'accepted' || s === 'paid' || s === 'closed' || s === 'invoiced') return 'bg-green-100 text-green-800';
  if (s === 'rejected' || s === 'void' || s === 'overdue') return 'bg-red-100 text-red-800';
  if (s === 'follow up' || s === 'partially_invoiced' || s === 'draft') return 'bg-yellow-100 text-yellow-800';
  return 'bg-gray-100 text-gray-800';
}
