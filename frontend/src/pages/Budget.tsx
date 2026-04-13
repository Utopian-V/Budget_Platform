import { useEffect, useState, useMemo } from 'react';
import { type ColumnDef } from '@tanstack/react-table';
import { ChevronDown, ChevronRight, Loader2, Search } from 'lucide-react';
import DataTable from '../components/DataTable';
import { getBudgetLines, updateVariance, getMasterData } from '../lib/api';
import { formatCurrency, cn, MONTHS } from '../lib/utils';

interface MonthlyData {
  id: number;
  month: string;
  month_index: number;
  expected: number;
  actual: number;
  mtd_variance: number;
  ytd_variance: number;
  reason: string | null;
  remark: string | null;
}

interface BudgetLine {
  id: number;
  serial_no: number;
  client_name: string;
  billing_entity: string;
  department: string;
  manager: string;
  service_category: string;
  currency: string;
  level: string;
  monthly_data: MonthlyData[];
  total_expected: number;
  total_actual: number;
  variance: number;
}

function enrichBudgetLine(raw: Omit<BudgetLine, 'total_expected' | 'total_actual' | 'variance'>): BudgetLine {
  const months = raw.monthly_data ?? [];
  const total_expected = months.reduce((s, m) => s + (m.expected ?? 0), 0);
  const total_actual = months.reduce((s, m) => s + (m.actual ?? 0), 0);
  return { ...raw, total_expected, total_actual, variance: total_expected - total_actual };
}

export default function Budget() {
  const [data, setData] = useState<BudgetLine[]>([]);
  const [loading, setLoading] = useState(true);
  const [department, setDepartment] = useState('');
  const [manager, setManager] = useState('');
  const [level, setLevel] = useState('');
  const [search, setSearch] = useState('');
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [varianceReasons, setVarianceReasons] = useState<string[]>([]);

  useEffect(() => {
    getMasterData('variance-reasons')
      .then((res) => {
        const reasons = (res.data as { id: number; reason: string }[]).map((r) => r.reason);
        setVarianceReasons(['', ...reasons]);
      })
      .catch(() => setVarianceReasons(['', 'Timing Difference', 'Scope Change', 'Rate Change', 'New Addition', 'Lost Client', 'Delayed Start', 'Other']));
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = {};
      if (department) params.department = department;
      if (manager) params.manager = manager;
      if (level) params.level = level;
      if (search) params.search = search;
      const res = await getBudgetLines(params);
      const raw = res.data?.data ?? res.data ?? [];
      setData((Array.isArray(raw) ? raw : []).map(enrichBudgetLine));
    } catch {
      setData([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [department, manager, level]);

  const handleSearch = () => fetchData();

  const expandedLine = useMemo(() => data.find((d) => d.id === expandedId), [data, expandedId]);

  const toggleExpand = (row: BudgetLine) => {
    setExpandedId(expandedId === row.id ? null : row.id);
  };

  const handleVarianceUpdate = async (budgetLineId: number, month: string, field: string, value: string) => {
    const apiField = field === 'variance_reason' ? 'reason' : field === 'remarks' ? 'remark' : field;
    try {
      await updateVariance(budgetLineId, month, { [apiField]: value });
      setData((prev) =>
        prev.map((bl) => {
          if (bl.id !== budgetLineId) return bl;
          return {
            ...bl,
            monthly_data: bl.monthly_data.map((m) =>
              m.month === month ? { ...m, [apiField]: value } : m
            ),
          };
        })
      );
    } catch {
      // silently handle
    }
  };

  const departments = useMemo(() => [...new Set(data.map((d) => d.department))].sort(), [data]);
  const managers = useMemo(() => [...new Set(data.map((d) => d.manager).filter(Boolean))].sort(), [data]);

  const columns: ColumnDef<BudgetLine, unknown>[] = useMemo(
    () => [
      {
        id: 'expand',
        header: '',
        cell: ({ row }) => (
          <button className="p-1 hover:bg-slate-100 rounded transition-colors">
            {expandedId === row.original.id ? (
              <ChevronDown className="w-4 h-4 text-slate-500" />
            ) : (
              <ChevronRight className="w-4 h-4 text-slate-500" />
            )}
          </button>
        ),
        enableSorting: false,
        size: 40,
      },
      { accessorKey: 'serial_no', header: 'S.No', size: 60 },
      { accessorKey: 'client_name', header: 'Client' },
      { accessorKey: 'billing_entity', header: 'Billing Entity' },
      { accessorKey: 'department', header: 'Department' },
      { accessorKey: 'service_category', header: 'Service Category' },
      { accessorKey: 'currency', header: 'Currency', size: 70 },
      {
        accessorKey: 'total_expected',
        header: 'Total Expected',
        cell: ({ row }) => formatCurrency(row.original.total_expected, row.original.currency),
      },
      {
        accessorKey: 'total_actual',
        header: 'Total Actual',
        cell: ({ row }) => formatCurrency(row.original.total_actual, row.original.currency),
      },
      {
        accessorKey: 'variance',
        header: 'Variance',
        cell: ({ row }) => (
          <span className={cn('font-medium', row.original.variance >= 0 ? 'text-green-600' : 'text-red-600')}>
            {formatCurrency(row.original.variance, row.original.currency)}
          </span>
        ),
      },
    ],
    [expandedId]
  );

  return (
    <div className="space-y-4">
      {/* Filter bar */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-4">
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={department}
            onChange={(e) => setDepartment(e.target.value)}
            className="text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Departments</option>
            {departments.map((d) => <option key={d} value={d}>{d}</option>)}
          </select>
          <select
            value={manager}
            onChange={(e) => setManager(e.target.value)}
            className="text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Managers</option>
            {managers.map((m) => <option key={m} value={m}>{m}</option>)}
          </select>
          <select
            value={level}
            onChange={(e) => setLevel(e.target.value)}
            className="text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Levels</option>
            <option value="Original">Original</option>
            <option value="New Addition">New Addition</option>
            <option value="Discrepancy">Discrepancy</option>
          </select>
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Search client..."
              className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            onClick={handleSearch}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Search
          </button>
        </div>
      </div>

      {/* Table */}
      <DataTable
        columns={columns}
        data={data}
        loading={loading}
        emptyMessage="No budget lines found"
        onRowClick={toggleExpand}
      />

      {/* Expanded monthly breakdown */}
      {expandedId !== null && expandedLine && (
        <div className="bg-white rounded-xl shadow-sm border border-blue-200 p-5">
          <h3 className="text-sm font-semibold text-slate-900 mb-4">Monthly Breakdown</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200">
                  <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600">Month</th>
                  <th className="px-3 py-2 text-right text-xs font-semibold text-slate-600">Expected</th>
                  <th className="px-3 py-2 text-right text-xs font-semibold text-slate-600">Actual</th>
                  <th className="px-3 py-2 text-right text-xs font-semibold text-slate-600">Variance</th>
                  <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600">Reason</th>
                  <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600">Remarks</th>
                </tr>
              </thead>
              <tbody>
                {(expandedLine.monthly_data.length > 0
                  ? expandedLine.monthly_data
                  : MONTHS.map((m, idx) => ({ id: 0, month: m, month_index: idx, expected: 0, actual: 0, mtd_variance: 0, ytd_variance: 0, reason: null, remark: null }))
                ).map((m, i) => {
                  const variance = (m.expected ?? 0) - (m.actual ?? 0);
                  return (
                    <tr key={m.month} className={cn('border-b border-slate-100', i % 2 === 1 && 'bg-slate-50/50')}>
                      <td className="px-3 py-2 font-medium text-slate-800">{m.month}</td>
                      <td className="px-3 py-2 text-right text-slate-700">{formatCurrency(m.expected)}</td>
                      <td className="px-3 py-2 text-right text-slate-700">{formatCurrency(m.actual)}</td>
                      <td className={cn('px-3 py-2 text-right font-medium', variance >= 0 ? 'text-green-600' : 'text-red-600')}>
                        {formatCurrency(variance)}
                      </td>
                      <td className="px-3 py-2">
                        <select
                          value={m.reason ?? ''}
                          onChange={(e) => handleVarianceUpdate(expandedId, m.month, 'reason', e.target.value)}
                          className="text-xs border border-slate-200 rounded px-2 py-1 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                        >
                          {varianceReasons.map((r) => <option key={r} value={r}>{r || '-- Select --'}</option>)}
                        </select>
                      </td>
                      <td className="px-3 py-2">
                        <input
                          type="text"
                          defaultValue={m.remark ?? ''}
                          onBlur={(e) => handleVarianceUpdate(expandedId, m.month, 'remark', e.target.value)}
                          className="text-xs border border-slate-200 rounded px-2 py-1 w-full bg-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                          placeholder="Add remarks..."
                        />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
