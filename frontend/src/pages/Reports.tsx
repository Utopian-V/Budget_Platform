import { Fragment, useEffect, useState } from 'react';
import { Loader2, Download } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { getDeptVarianceReport, getMtdYtdReport, getClientSummary, exportReport } from '../lib/api';
import { formatCurrency, cn, MONTHS } from '../lib/utils';

interface DeptVariance {
  department: string;
  total_expected: number;
  total_actual: number;
  total_variance: number;
  lines: {
    client_name: string;
    service_category: string;
    manager: string;
    expected: number;
    actual: number;
    variance: number;
    reason: string | null;
    remark: string | null;
  }[];
}

interface MtdYtdRow {
  department: string;
  months: { month: string; month_index: number; expected: number; actual: number; mtd_variance: number }[];
  ytd_expected: number;
  ytd_actual: number;
  ytd_variance: number;
}

interface ClientRow {
  client_name: string;
  department: string;
  total_expected: number;
  total_actual: number;
  variance: number;
}

const TABS = ['Department Variance', 'MTD/YTD Summary', 'Client Summary'] as const;
type Tab = (typeof TABS)[number];

export default function Reports() {
  const [activeTab, setActiveTab] = useState<Tab>('Department Variance');
  const [month, setMonth] = useState<string>(MONTHS[0]);
  const [loading, setLoading] = useState(true);

  const [deptVariance, setDeptVariance] = useState<DeptVariance[]>([]);
  const [mtdYtd, setMtdYtd] = useState<MtdYtdRow[]>([]);
  const [clients, setClients] = useState<ClientRow[]>([]);
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    setExporting(true);
    try {
      const reportType = activeTab === 'Department Variance' ? 'department-variance' : activeTab === 'MTD/YTD Summary' ? 'mtd-ytd' : 'client-summary';
      const needsMonth = activeTab === 'Department Variance';
      const res = await exportReport(reportType, needsMonth ? month : undefined);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `${reportType}_${month}.xlsx`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      // handle error
    } finally {
      setExporting(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    const fetchTab = async () => {
      try {
        if (activeTab === 'Department Variance') {
          const res = await getDeptVarianceReport(month);
          setDeptVariance(res.data?.departments ?? []);
        } else if (activeTab === 'MTD/YTD Summary') {
          const res = await getMtdYtdReport();
          setMtdYtd(Array.isArray(res.data) ? res.data : []);
        } else {
          const res = await getClientSummary();
          setClients(Array.isArray(res.data) ? res.data : []);
        }
      } catch {
        // handle error
      } finally {
        setLoading(false);
      }
    };
    fetchTab();
  }, [activeTab, month]);

  return (
    <div className="space-y-6">
      {/* Tab bar + Export */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-1.5 inline-flex gap-1">
          {TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={cn(
                'px-4 py-2 text-sm font-medium rounded-lg transition-colors',
                activeTab === tab
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-600 hover:bg-slate-100'
              )}
            >
              {tab}
            </button>
          ))}
        </div>
        <button
          onClick={handleExport}
          disabled={exporting}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-60 transition-colors"
        >
          {exporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
          Export Excel
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      ) : (
        <>
          {/* Department Variance */}
          {activeTab === 'Department Variance' && (
            <div className="space-y-6">
              <div className="flex items-center gap-3">
                <select
                  value={month}
                  onChange={(e) => setMonth(e.target.value)}
                  className="text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {MONTHS.map((m) => <option key={m} value={m}>{m}</option>)}
                </select>
              </div>

              {/* Table */}
              <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-slate-50 border-b border-slate-200">
                        <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Department</th>
                        <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase">Expected</th>
                        <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase">Actual</th>
                        <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase">Variance</th>
                      </tr>
                    </thead>
                    <tbody>
                      {deptVariance.length === 0 ? (
                        <tr><td colSpan={4} className="px-4 py-12 text-center text-slate-400">No data</td></tr>
                      ) : (
                        deptVariance.map((d, i) => (
                          <tr key={d.department} className={cn('border-b border-slate-100', i % 2 === 1 && 'bg-slate-50/50')}>
                            <td className="px-4 py-3 font-medium text-slate-800">{d.department}</td>
                            <td className="px-4 py-3 text-right text-slate-700">{formatCurrency(d.total_expected)}</td>
                            <td className="px-4 py-3 text-right text-slate-700">{formatCurrency(d.total_actual)}</td>
                            <td className={cn('px-4 py-3 text-right font-medium', d.total_variance >= 0 ? 'text-green-600' : 'text-red-600')}>
                              {formatCurrency(d.total_variance)}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Bar chart */}
              {deptVariance.length > 0 && (
                <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
                  <h3 className="text-lg font-semibold text-slate-900 mb-4">Department Comparison</h3>
                  <ResponsiveContainer width="100%" height={350}>
                    <BarChart data={deptVariance}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="department" tick={{ fontSize: 11 }} stroke="#94a3b8" angle={-20} textAnchor="end" height={60} />
                      <YAxis tick={{ fontSize: 12 }} stroke="#94a3b8" tickFormatter={(v: number) => `₹${(v / 100000).toFixed(0)}L`} />
                      <Tooltip formatter={(value) => formatCurrency(Number(value))} contentStyle={{ borderRadius: 8, border: '1px solid #e2e8f0' }} />
                      <Legend />
                      <Bar dataKey="total_expected" fill="#2563eb" radius={[4, 4, 0, 0]} name="Expected" />
                      <Bar dataKey="total_actual" fill="#16a34a" radius={[4, 4, 0, 0]} name="Actual" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          )}

          {/* MTD/YTD Summary */}
          {activeTab === 'MTD/YTD Summary' && (
            <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200">
                      <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase sticky left-0 bg-slate-50 z-10">
                        Department
                      </th>
                      {MONTHS.map((m) => (
                        <th key={m} colSpan={2} className="px-2 py-3 text-center text-xs font-semibold text-slate-600 uppercase border-l border-slate-200">
                          {m}
                        </th>
                      ))}
                      <th className="px-3 py-3 text-right text-xs font-semibold text-slate-600 uppercase border-l border-slate-200">YTD Var</th>
                    </tr>
                    <tr className="bg-slate-50 border-b border-slate-200">
                      <th className="sticky left-0 bg-slate-50 z-10" />
                      {MONTHS.map((m) => (
                        <Fragment key={m}>
                          <th className="px-2 py-2 text-center text-[10px] font-medium text-blue-600 border-l border-slate-200">Exp</th>
                          <th className="px-2 py-2 text-center text-[10px] font-medium text-green-600">Act</th>
                        </Fragment>
                      ))}
                      <th className="border-l border-slate-200" />
                    </tr>
                  </thead>
                  <tbody>
                    {mtdYtd.length === 0 ? (
                      <tr><td colSpan={2 + MONTHS.length * 2} className="px-4 py-12 text-center text-slate-400">No data</td></tr>
                    ) : (
                      mtdYtd.map((row, i) => (
                        <tr key={row.department} className={cn('border-b border-slate-100', i % 2 === 1 && 'bg-slate-50/50')}>
                          <td className="px-4 py-2.5 font-medium text-slate-800 sticky left-0 bg-inherit whitespace-nowrap z-10">
                            {row.department}
                          </td>
                          {MONTHS.map((m) => {
                            const md = row.months?.find((x) => x.month === m);
                            return (
                              <Fragment key={m}>
                                <td className="px-2 py-2.5 text-right text-xs text-slate-600 border-l border-slate-100">
                                  {md ? formatCurrency(md.expected) : '-'}
                                </td>
                                <td className="px-2 py-2.5 text-right text-xs text-slate-600">
                                  {md ? formatCurrency(md.actual) : '-'}
                                </td>
                              </Fragment>
                            );
                          })}
                          <td className={cn('px-3 py-2.5 text-right text-xs font-medium border-l border-slate-200',
                            (row.ytd_variance ?? 0) >= 0 ? 'text-green-600' : 'text-red-600')}>
                            {formatCurrency(row.ytd_variance)}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Client Summary */}
          {activeTab === 'Client Summary' && (
            <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200">
                      <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Rank</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Client</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Department</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase">Total Expected</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase">Total Actual</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase">Variance</th>
                    </tr>
                  </thead>
                  <tbody>
                    {clients.length === 0 ? (
                      <tr><td colSpan={6} className="px-4 py-12 text-center text-slate-400">No client data</td></tr>
                    ) : (
                      clients.map((c, i) => (
                        <tr key={`${c.client_name}-${c.department}`} className={cn('border-b border-slate-100', i % 2 === 1 && 'bg-slate-50/50')}>
                          <td className="px-4 py-3 text-slate-500 font-medium">{i + 1}</td>
                          <td className="px-4 py-3 font-medium text-slate-800">{c.client_name}</td>
                          <td className="px-4 py-3 text-slate-600">{c.department}</td>
                          <td className="px-4 py-3 text-right text-slate-700">{formatCurrency(c.total_expected)}</td>
                          <td className="px-4 py-3 text-right text-slate-700">{formatCurrency(c.total_actual)}</td>
                          <td className={cn('px-4 py-3 text-right font-medium', c.variance >= 0 ? 'text-green-600' : 'text-red-600')}>
                            {formatCurrency(c.variance)}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
