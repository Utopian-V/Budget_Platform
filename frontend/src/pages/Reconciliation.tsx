import { useEffect, useState } from 'react';
import { Loader2, Play, CheckCircle2, XCircle, AlertTriangle, Plus, ChevronDown, ChevronRight, ArrowUpCircle, Camera } from 'lucide-react';
import StatCard from '../components/StatCard';
import { runReconciliation, getRecoSummary, getUnmatched, getNewAdditions, promoteToBudget, createSnapshot } from '../lib/api';
import { formatCurrency, cn, MONTHS } from '../lib/utils';

interface RecoSummary {
  month: string;
  total_records: number;
  matched: number;
  unmatched: number;
  total_budget_amount: number;
  total_invoice_amount: number;
  total_difference: number;
}

interface MatchedItem {
  id: number;
  unique_code: string;
  budget_amount: number;
  invoice_amount: number;
  difference: number;
}

interface UnmatchedCategories {
  [category: string]: MatchedItem[];
}

interface NewAdditionItem {
  id: number;
  unique_code: string;
  invoice_amount: number;
  detail: string;
}

export default function Reconciliation() {
  const [month, setMonth] = useState<string>(MONTHS[0]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [summary, setSummary] = useState<RecoSummary | null>(null);
  const [unmatchedCategories, setUnmatchedCategories] = useState<UnmatchedCategories>({});
  const [newAdditions, setNewAdditions] = useState<NewAdditionItem[]>([]);
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  const fetchData = async () => {
    setLoading(true);
    try {
      const [sumRes, unmRes, naRes] = await Promise.all([
        getRecoSummary(month),
        getUnmatched(month),
        getNewAdditions(month),
      ]);
      setSummary(sumRes.data);
      setUnmatchedCategories(unmRes.data?.categories ?? {});
      setNewAdditions(naRes.data?.data ?? []);
    } catch {
      setSummary(null);
      setUnmatchedCategories({});
      setNewAdditions([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [month]);

  const handleRun = async () => {
    setRunning(true);
    try {
      await runReconciliation(month);
      await fetchData();
    } catch {
      // handle error
    } finally {
      setRunning(false);
    }
  };

  const [promotedIds, setPromotedIds] = useState<Set<number>>(new Set());
  const [snapshotting, setSnapshotting] = useState(false);

  const handlePromote = async (id: number) => {
    try {
      await promoteToBudget(id);
      setPromotedIds((prev) => new Set(prev).add(id));
    } catch {
      // handle error
    }
  };

  const handleSnapshot = async () => {
    setSnapshotting(true);
    try {
      await createSnapshot(month);
    } catch {
      // handle error
    } finally {
      setSnapshotting(false);
    }
  };

  const toggleGroup = (type: string) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return next;
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex flex-wrap items-center gap-3">
        <select
          value={month}
          onChange={(e) => setMonth(e.target.value)}
          className="text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {MONTHS.map((m) => <option key={m} value={m}>{m}</option>)}
        </select>
        <button
          onClick={handleRun}
          disabled={running}
          className="flex items-center gap-2 px-5 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-60 transition-colors"
        >
          {running ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
          Run Reconciliation
        </button>
        <button
          onClick={handleSnapshot}
          disabled={snapshotting}
          className="flex items-center gap-2 px-5 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-60 transition-colors"
        >
          {snapshotting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Camera className="w-4 h-4" />}
          Save Snapshot
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Matched"
          value={String(summary?.matched ?? 0)}
          subtitle={`of ${summary?.total_records ?? 0} records`}
          icon={<CheckCircle2 className="w-5 h-5" />}
          color="green"
        />
        <StatCard
          title="Unmatched"
          value={String(summary?.unmatched ?? 0)}
          icon={<XCircle className="w-5 h-5" />}
          color="red"
        />
        <StatCard
          title="Budget Total"
          value={formatCurrency(summary?.total_budget_amount)}
          icon={<Plus className="w-5 h-5" />}
          color="blue"
        />
        <StatCard
          title="Invoice Total"
          value={formatCurrency(summary?.total_invoice_amount)}
          icon={<AlertTriangle className="w-5 h-5" />}
          color="orange"
        />
      </div>

      {/* Unmatched Items by Category */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
        <div className="flex items-center gap-2 px-6 py-4 border-b border-slate-100">
          <div className="w-1 h-6 rounded-full bg-red-500" />
          <h2 className="text-lg font-semibold text-slate-900">Unmatched Items by Category</h2>
        </div>
        <div className="divide-y divide-slate-100">
          {Object.keys(unmatchedCategories).length === 0 ? (
            <div className="px-6 py-12 text-center text-slate-400">Run reconciliation to see results</div>
          ) : (
            Object.entries(unmatchedCategories).map(([category, items]) => (
              <div key={category}>
                <button
                  onClick={() => toggleGroup(category)}
                  className="w-full flex items-center gap-3 px-6 py-3 hover:bg-slate-50 transition-colors"
                >
                  {expandedGroups.has(category) ? (
                    <ChevronDown className="w-4 h-4 text-slate-500" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-slate-500" />
                  )}
                  <span className="text-sm font-semibold text-slate-800 capitalize">{category.replace(/_/g, ' ')}</span>
                  <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700">
                    {items.length}
                  </span>
                </button>
                {expandedGroups.has(category) && (
                  <div className="px-6 pb-4">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="bg-slate-50 border-b border-slate-200">
                          <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600">Unique Code</th>
                          <th className="px-3 py-2 text-right text-xs font-semibold text-slate-600">Budget</th>
                          <th className="px-3 py-2 text-right text-xs font-semibold text-slate-600">Invoice</th>
                          <th className="px-3 py-2 text-right text-xs font-semibold text-slate-600">Diff</th>
                          <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600">Detail</th>
                        </tr>
                      </thead>
                      <tbody>
                        {items.map((item: MatchedItem & { detail?: string }, i: number) => (
                          <tr key={item.id} className={cn('border-b border-slate-100', i % 2 === 1 && 'bg-slate-50/30')}>
                            <td className="px-3 py-2 text-slate-700 text-xs">{item.unique_code ?? '-'}</td>
                            <td className="px-3 py-2 text-right text-slate-700">{formatCurrency(item.budget_amount)}</td>
                            <td className="px-3 py-2 text-right text-slate-700">{formatCurrency(item.invoice_amount)}</td>
                            <td className="px-3 py-2 text-right text-red-600 font-medium">{formatCurrency(item.difference)}</td>
                            <td className="px-3 py-2 text-slate-500 text-xs max-w-xs truncate">{(item as unknown as Record<string, string>).detail ?? ''}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* New Additions */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
        <div className="flex items-center gap-2 px-6 py-4 border-b border-slate-100">
          <div className="w-1 h-6 rounded-full bg-orange-500" />
          <h2 className="text-lg font-semibold text-slate-900">New Additions</h2>
          <span className="ml-auto text-sm text-slate-500">{newAdditions.length} items</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200">
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Unique Code</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase">Invoice Amount</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Detail</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-slate-600 uppercase">Action</th>
              </tr>
            </thead>
            <tbody>
              {newAdditions.length === 0 ? (
                <tr><td colSpan={4} className="px-4 py-12 text-center text-slate-400">No new additions</td></tr>
              ) : (
                newAdditions.map((item, i) => (
                  <tr key={item.id} className={cn('border-b border-slate-100', i % 2 === 1 && 'bg-slate-50/50')}>
                    <td className="px-4 py-3 text-slate-700 text-xs">{item.unique_code ?? '-'}</td>
                    <td className="px-4 py-3 text-right text-slate-700">{formatCurrency(item.invoice_amount)}</td>
                    <td className="px-4 py-3 text-slate-500 text-xs">{item.detail}</td>
                    <td className="px-4 py-3 text-center">
                      {promotedIds.has(item.id) ? (
                        <span className="text-xs text-green-600 font-medium">Promoted</span>
                      ) : (
                        <button
                          onClick={() => handlePromote(item.id)}
                          className="inline-flex items-center gap-1 px-3 py-1 text-xs font-medium text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
                        >
                          <ArrowUpCircle className="w-3.5 h-3.5" />
                          Promote
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
