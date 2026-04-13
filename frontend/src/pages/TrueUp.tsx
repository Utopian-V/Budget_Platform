import { useEffect, useState } from 'react';
import { Loader2, CheckCircle2, AlertTriangle } from 'lucide-react';
import { getTrueUpCandidates } from '../lib/api';
import { formatCurrency, cn } from '../lib/utils';

interface TrueUpCandidate {
  budget_line_id: number;
  client_name: string;
  department: string;
  service_category: string;
  manager: string;
  total_expected: number;
  total_actual: number;
  variance: number;
  variance_ratio: number;
}

export default function TrueUp() {
  const [candidates, setCandidates] = useState<TrueUpCandidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [threshold, setThreshold] = useState(0.1);
  const [resolvedIds, setResolvedIds] = useState<Set<number>>(new Set());

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await getTrueUpCandidates(threshold);
      setCandidates(Array.isArray(res.data) ? res.data : []);
    } catch {
      setCandidates([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [threshold]);

  const toggleResolved = (id: number) => {
    setResolvedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const unresolvedCount = candidates.filter((c) => !resolvedIds.has(c.budget_line_id)).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Quarterly True-Up Review</h1>
          <p className="text-sm text-slate-500 mt-1">
            Budget lines where cumulative variance exceeds the threshold, suggesting adjustment.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <label className="text-sm text-slate-600">Variance Threshold:</label>
          <select
            value={threshold}
            onChange={(e) => setThreshold(parseFloat(e.target.value))}
            className="text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value={0.05}>5%</option>
            <option value={0.1}>10%</option>
            <option value={0.15}>15%</option>
            <option value={0.2}>20%</option>
            <option value={0.25}>25%</option>
          </select>
        </div>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-5">
          <p className="text-sm font-medium text-slate-500">Total Candidates</p>
          <p className="mt-1 text-2xl font-bold text-slate-900">{candidates.length}</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-5">
          <p className="text-sm font-medium text-slate-500">Pending Review</p>
          <p className="mt-1 text-2xl font-bold text-orange-600">{unresolvedCount}</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-5">
          <p className="text-sm font-medium text-slate-500">Resolved</p>
          <p className="mt-1 text-2xl font-bold text-green-600">{resolvedIds.size}</p>
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200">
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Client</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Department</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Service Category</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Manager</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase">Expected</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase">Actual</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase">Variance</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase">Var %</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-slate-600 uppercase">Status</th>
                </tr>
              </thead>
              <tbody>
                {candidates.length === 0 ? (
                  <tr><td colSpan={9} className="px-4 py-12 text-center text-slate-400">No candidates exceed the threshold</td></tr>
                ) : (
                  candidates.map((c, i) => {
                    const isResolved = resolvedIds.has(c.budget_line_id);
                    return (
                      <tr key={c.budget_line_id} className={cn('border-b border-slate-100', i % 2 === 1 && 'bg-slate-50/50', isResolved && 'opacity-50')}>
                        <td className="px-4 py-3 font-medium text-slate-800">{c.client_name}</td>
                        <td className="px-4 py-3 text-slate-600">{c.department}</td>
                        <td className="px-4 py-3 text-slate-600 text-xs">{c.service_category}</td>
                        <td className="px-4 py-3 text-slate-600">{c.manager}</td>
                        <td className="px-4 py-3 text-right text-slate-700">{formatCurrency(c.total_expected)}</td>
                        <td className="px-4 py-3 text-right text-slate-700">{formatCurrency(c.total_actual)}</td>
                        <td className={cn('px-4 py-3 text-right font-medium', c.variance >= 0 ? 'text-green-600' : 'text-red-600')}>
                          {formatCurrency(c.variance)}
                        </td>
                        <td className="px-4 py-3 text-right text-slate-700">{(c.variance_ratio * 100).toFixed(1)}%</td>
                        <td className="px-4 py-3 text-center">
                          {isResolved ? (
                            <button
                              onClick={() => toggleResolved(c.budget_line_id)}
                              className="inline-flex items-center gap-1 px-3 py-1 text-xs font-medium text-green-600 bg-green-50 rounded-lg hover:bg-green-100 transition-colors"
                            >
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              Resolved
                            </button>
                          ) : (
                            <button
                              onClick={() => toggleResolved(c.budget_line_id)}
                              className="inline-flex items-center gap-1 px-3 py-1 text-xs font-medium text-orange-600 bg-orange-50 rounded-lg hover:bg-orange-100 transition-colors"
                            >
                              <AlertTriangle className="w-3.5 h-3.5" />
                              Mark Resolved
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
