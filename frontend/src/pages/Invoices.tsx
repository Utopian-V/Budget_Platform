import { useEffect, useState, useMemo } from 'react';
import { type ColumnDef } from '@tanstack/react-table';
import { Loader2, Search } from 'lucide-react';
import DataTable from '../components/DataTable';
import StatCard from '../components/StatCard';
import { getInvoices, getInvoiceSummary } from '../lib/api';
import { formatCurrency, cn, MONTHS, getStatusColor } from '../lib/utils';

interface Invoice {
  id: number;
  invoice_date: string;
  invoice_number: string;
  customer_name: string;
  item_name: string;
  item_total: number;
  total: number;
  invoice_status: string;
  sales_order_number: string;
  department: string;
  billing_entity: string;
  is_voided: boolean;
}

interface InvoiceSummaryData {
  month: string;
  total_amount: number;
  voided_count: number;
  credit_note_count: number;
  credit_note_total: number;
  net_amount: number;
}

export default function Invoices() {
  const [data, setData] = useState<Invoice[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [summary, setSummary] = useState<InvoiceSummaryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [month, setMonth] = useState(MONTHS[0]);
  const [status, setStatus] = useState('');
  const [customerSearch, setCustomerSearch] = useState('');
  const [billingEntity, setBillingEntity] = useState('');

  const fetchData = async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { month };
      if (status) params.status = status;
      if (customerSearch) params.customer = customerSearch;
      if (billingEntity) params.billing_entity = billingEntity;

      const [invRes, sumRes] = await Promise.all([
        getInvoices(params),
        getInvoiceSummary(month),
      ]);
      setData(invRes.data?.data ?? []);
      setTotalCount(invRes.data?.total ?? 0);
      setSummary(sumRes.data);
    } catch {
      setData([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [month, status, billingEntity]);

  const billingEntities = useMemo(
    () => [...new Set(data.map((d) => d.billing_entity).filter(Boolean))].sort(),
    [data]
  );

  const columns: ColumnDef<Invoice, unknown>[] = useMemo(
    () => [
      { accessorKey: 'invoice_date', header: 'Date', size: 100 },
      { accessorKey: 'invoice_number', header: 'Invoice #' },
      { accessorKey: 'customer_name', header: 'Customer' },
      { accessorKey: 'item_name', header: 'Item Name' },
      {
        accessorKey: 'item_total',
        header: 'Amount',
        cell: ({ row }) => (
          <span className={cn(row.original.is_voided && 'line-through text-red-400')}>
            {formatCurrency(row.original.item_total)}
          </span>
        ),
      },
      {
        accessorKey: 'invoice_status',
        header: 'Status',
        cell: ({ row }) => (
          <span className={cn('px-2 py-1 rounded-full text-xs font-medium', getStatusColor(row.original.invoice_status))}>
            {row.original.invoice_status}
          </span>
        ),
      },
      { accessorKey: 'sales_order_number', header: 'SO Number' },
      { accessorKey: 'department', header: 'Department' },
    ],
    []
  );

  return (
    <div className="space-y-4">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Invoices"
          value={String(totalCount)}
          color="blue"
        />
        <StatCard
          title="Voided (Auto-Cleaned)"
          value={String(summary?.voided_count ?? 0)}
          color="red"
        />
        <StatCard
          title="Credit Note Adjustments"
          value={formatCurrency(summary?.credit_note_total)}
          color="orange"
        />
        <StatCard
          title="Net Revenue"
          value={formatCurrency(summary?.net_amount)}
          color="green"
        />
      </div>

      {/* Filter bar */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-4">
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={month}
            onChange={(e) => setMonth(e.target.value)}
            className="text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {MONTHS.map((m) => <option key={m} value={m}>{m}</option>)}
          </select>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="Paid">Paid</option>
            <option value="Void">Void</option>
            <option value="Draft">Draft</option>
            <option value="Overdue">Overdue</option>
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
        <DataTable columns={columns} data={data} emptyMessage="No invoices found for this period" />
      )}
    </div>
  );
}
