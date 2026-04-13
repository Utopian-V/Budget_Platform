import { useEffect, useState, useMemo } from 'react';
import { type ColumnDef } from '@tanstack/react-table';
import { Loader2, Search } from 'lucide-react';
import DataTable from '../components/DataTable';
import StatCard from '../components/StatCard';
import { getProposals, getProposalStats } from '../lib/api';
import { formatCurrency, cn, getStatusColor } from '../lib/utils';

interface Proposal {
  id: number;
  month: string;
  customer_name: string;
  service_description: string;
  service_category: string;
  fee_proposed: number;
  status: string;
  quotation_no: string;
  so_number: string;
  days_since_proposal: number;
  billing_entity: string;
}

interface FeeByStatus {
  status: string;
  total_fee: number;
}

interface ProposalStats {
  total_proposals: number;
  accepted_count: number;
  follow_up_count: number;
  rejected_count: number;
  fee_by_status: FeeByStatus[];
}

export default function Proposals() {
  const [data, setData] = useState<Proposal[]>([]);
  const [stats, setStats] = useState<ProposalStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState('');
  const [customerSearch, setCustomerSearch] = useState('');
  const [billingEntity, setBillingEntity] = useState('');

  const fetchData = async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = {};
      if (status) params.status = status;
      if (customerSearch) params.customer = customerSearch;
      if (billingEntity) params.billing_entity = billingEntity;

      const [propRes, statsRes] = await Promise.all([
        getProposals(params),
        getProposalStats(),
      ]);
      setData(propRes.data?.data ?? []);
      setStats(statsRes.data);
    } catch {
      setData([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [status, billingEntity]);

  const billingEntities = useMemo(
    () => [...new Set(data.map((d) => d.billing_entity).filter(Boolean))].sort(),
    [data]
  );

  const totalFeeProposed = useMemo(() => {
    if (!stats?.fee_by_status) return 0;
    return stats.fee_by_status.reduce((sum, s) => sum + (s.total_fee ?? 0), 0);
  }, [stats]);

  const columns: ColumnDef<Proposal, unknown>[] = useMemo(
    () => [
      { accessorKey: 'month', header: 'Month', size: 80 },
      { accessorKey: 'customer_name', header: 'Customer' },
      {
        accessorKey: 'service_description',
        header: 'Service Description',
        cell: ({ getValue }) => (
          <span className="max-w-xs truncate block" title={getValue() as string}>
            {getValue() as string}
          </span>
        ),
      },
      { accessorKey: 'service_category', header: 'Category' },
      {
        accessorKey: 'fee_proposed',
        header: 'Fee Proposed',
        cell: ({ row }) => formatCurrency(row.original.fee_proposed),
      },
      {
        accessorKey: 'status',
        header: 'Status',
        cell: ({ row }) => (
          <span className={cn('px-2 py-1 rounded-full text-xs font-medium', getStatusColor(row.original.status))}>
            {row.original.status}
          </span>
        ),
      },
      { accessorKey: 'quotation_no', header: 'Quotation No' },
      { accessorKey: 'so_number', header: 'SO Number' },
      {
        accessorKey: 'days_since_proposal',
        header: 'Days Aging',
        cell: ({ row }) => (
          <span className={cn(
            'font-medium',
            (row.original.days_since_proposal ?? 0) > 30 && row.original.status !== 'Accepted' ? 'text-orange-600' : 'text-slate-700'
          )}>
            {row.original.days_since_proposal ?? 0}
          </span>
        ),
      },
    ],
    []
  );

  return (
    <div className="space-y-4">
      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard title="Total Proposals" value={String(stats?.total_proposals ?? 0)} color="blue" />
        <StatCard title="Accepted" value={String(stats?.accepted_count ?? 0)} color="green" />
        <StatCard title="Follow-up" value={String(stats?.follow_up_count ?? 0)} color="orange" />
        <StatCard title="Rejected" value={String(stats?.rejected_count ?? 0)} color="red" />
        <StatCard title="Total Fee Proposed" value={formatCurrency(totalFeeProposed)} color="purple" />
      </div>

      {/* Filter bar */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-4">
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="Accepted">Accepted</option>
            <option value="Follow Up">Follow Up</option>
            <option value="Rejected">Rejected</option>
          </select>
          <select
            value={billingEntity}
            onChange={(e) => setBillingEntity(e.target.value)}
            className="text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Billing Entities</option>
            {billingEntities.map((b) => <option key={b} value={b}>{b}</option>)}
          </select>
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={customerSearch}
              onChange={(e) => setCustomerSearch(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && fetchData()}
              placeholder="Search customer..."
              className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            onClick={fetchData}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Search
          </button>
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      ) : (
        <DataTable
          columns={columns}
          data={data}
          emptyMessage="No proposals found"
        />
      )}
    </div>
  );
}
