import { useEffect, useState } from 'react';
import {
  LayoutDashboard,
  Wallet,
  TrendingUp,
  Users,
  FileText,
  Lightbulb,
  Loader2,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import StatCard from '../components/StatCard';
import { getDashboardSummary, getDepartmentSummary, getRecentActivity } from '../lib/api';
import { formatCurrency, cn, MONTH_LABELS } from '../lib/utils';

interface DashSummary {
  total_budget: number;
  total_actual_ytd: number;
  total_variance_ytd: number;
  total_clients: number;
  total_invoices: number;
  total_proposals: number;
  monthly_expected: number[];
  monthly_actual: number[];
}

interface DeptRow {
  department: string;
  budget: number;
  actual: number;
  variance: number;
}

interface ActivityItem {
  type: string;
  date: string | null;
  reference: string | null;
  customer: string | null;
  amount: number | null;
  status: string | null;
}

export default function Dashboard() {
  const [summary, setSummary] = useState<DashSummary | null>(null);
  const [departments, setDepartments] = useState<DeptRow[]>([]);
  const [activity, setActivity] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [sumRes, deptRes, actRes] = await Promise.all([
          getDashboardSummary(),
          getDepartmentSummary(),
          getRecentActivity(),
        ]);
        setSummary(sumRes.data);
        setDepartments(deptRes.data);
        setActivity(actRes.data);
      } catch {
        /* graceful failure – data will show as empty */
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  const chartData = MONTH_LABELS.map((label, i) => ({
    month: label,
    expected: summary?.monthly_expected?.[i] ?? 0,
    actual: summary?.monthly_actual?.[i] ?? 0,
  }));

  const varianceDir = (summary?.total_variance_ytd ?? 0) <= 0 ? 'up' as const : 'down' as const;

  return (
    <div className="space-y-6">
      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <StatCard title="Total Budget" value={formatCurrency(summary?.total_budget)} icon={<Wallet className="w-5 h-5" />} color="blue" />
        <StatCard title="YTD Actual" value={formatCurrency(summary?.total_actual_ytd)} icon={<TrendingUp className="w-5 h-5" />} color="green" />
        <StatCard title="YTD Variance" value={formatCurrency(summary?.total_variance_ytd)} trend={varianceDir} icon={<LayoutDashboard className="w-5 h-5" />} color={varianceDir === 'up' ? 'green' : 'red'} />
        <StatCard title="Total Clients" value={String(summary?.total_clients ?? 0)} icon={<Users className="w-5 h-5" />} color="purple" />
        <StatCard title="Invoices" value={String(summary?.total_invoices ?? 0)} icon={<FileText className="w-5 h-5" />} color="orange" />
        <StatCard title="Proposals" value={String(summary?.total_proposals ?? 0)} icon={<Lightbulb className="w-5 h-5" />} color="slate" />
      </div>

      {/* Chart */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-4">Monthly Expected vs Actual</h2>
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="month" tick={{ fontSize: 12 }} stroke="#94a3b8" />
            <YAxis tick={{ fontSize: 12 }} stroke="#94a3b8" tickFormatter={(v: number) => `₹${(v / 100000).toFixed(0)}L`} />
            <Tooltip formatter={(value) => formatCurrency(Number(value))} contentStyle={{ borderRadius: 8, border: '1px solid #e2e8f0' }} />
            <Legend />
            <Line type="monotone" dataKey="expected" stroke="#2563eb" strokeWidth={2.5} dot={{ r: 4 }} name="Expected" />
            <Line type="monotone" dataKey="actual" stroke="#16a34a" strokeWidth={2.5} dot={{ r: 4 }} name="Actual" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Bottom row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Dept summary */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100">
            <h2 className="text-lg font-semibold text-slate-900">Department Summary</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200">
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Department</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase">Budget</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase">Actual</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase">Variance</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase">% Ach.</th>
                </tr>
              </thead>
              <tbody>
                {departments.length === 0 ? (
                  <tr><td colSpan={5} className="px-4 py-12 text-center text-slate-400">No data — click "Import Data" in Settings</td></tr>
                ) : (
                  departments.map((d, i) => {
                    const pct = d.budget > 0 ? ((d.actual / d.budget) * 100) : 0;
                    return (
                      <tr key={d.department} className={cn('border-b border-slate-100', i % 2 === 1 && 'bg-slate-50/50')}>
                        <td className="px-4 py-3 font-medium text-slate-800">{d.department}</td>
                        <td className="px-4 py-3 text-right text-slate-700">{formatCurrency(d.budget)}</td>
                        <td className="px-4 py-3 text-right text-slate-700">{formatCurrency(d.actual)}</td>
                        <td className={cn('px-4 py-3 text-right font-medium', d.variance >= 0 ? 'text-red-600' : 'text-green-600')}>
                          {formatCurrency(d.variance)}
                        </td>
                        <td className="px-4 py-3 text-right text-slate-700">{pct.toFixed(1)}%</td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Recent activity */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-100">
          <div className="px-6 py-4 border-b border-slate-100">
            <h2 className="text-lg font-semibold text-slate-900">Recent Activity</h2>
          </div>
          <div className="divide-y divide-slate-100 max-h-80 overflow-y-auto">
            {activity.length === 0 ? (
              <div className="px-6 py-12 text-center text-slate-400">No recent activity</div>
            ) : (
              activity.map((a, i) => (
                <div key={`${a.reference}-${i}`} className="px-6 py-3 hover:bg-slate-50 transition-colors">
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-slate-700 truncate">
                      <span className={cn('inline-block w-2 h-2 rounded-full mr-2', a.type === 'invoice' ? 'bg-blue-500' : 'bg-amber-500')} />
                      {a.customer ?? 'N/A'}
                    </p>
                    <span className="text-sm font-medium text-slate-900">{a.amount ? formatCurrency(a.amount) : '—'}</span>
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">{a.reference} · {a.date ?? ''}</p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
