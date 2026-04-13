import { useEffect, useState, useMemo } from 'react';
import { type ColumnDef } from '@tanstack/react-table';
import { Loader2, Search } from 'lucide-react';
import DataTable from '../components/DataTable';
import { getSalesOrders } from '../lib/api';
import { formatCurrency, cn, getStatusColor } from '../lib/utils';

interface SalesOrder {
  id: number;
  order_date: string;
  salesorder_number: string;
  status: string;
  customer_name: string;
  quotation_no: string;
  item_name: string;
  quantity_ordered: number;
  quantity_invoiced: number;
  item_total: number;
}

export default function SalesOrders() {
  const [data, setData] = useState<SalesOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState('');
  const [search, setSearch] = useState('');

  const fetchData = async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = {};
      if (status) params.status = status;
      if (search) params.customer = search;
      const res = await getSalesOrders(params);
      setData(res.data?.data ?? []);
    } catch {
      setData([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [status]);

  const columns: ColumnDef<SalesOrder, unknown>[] = useMemo(
    () => [
      { accessorKey: 'order_date', header: 'Order Date', size: 100 },
      { accessorKey: 'salesorder_number', header: 'SO Number' },
      {
        accessorKey: 'status',
        header: 'Status',
        cell: ({ row }) => (
          <span className={cn('px-2 py-1 rounded-full text-xs font-medium', getStatusColor(row.original.status))}>
            {row.original.status}
          </span>
        ),
      },
      { accessorKey: 'customer_name', header: 'Customer' },
      { accessorKey: 'quotation_no', header: 'Quotation No' },
      { accessorKey: 'item_name', header: 'Item' },
      {
        accessorKey: 'quantity_ordered',
        header: 'Qty Ordered',
        cell: ({ getValue }) => (getValue() as number)?.toLocaleString() ?? '0',
      },
      {
        accessorKey: 'quantity_invoiced',
        header: 'Qty Invoiced',
        cell: ({ getValue }) => (getValue() as number)?.toLocaleString() ?? '0',
      },
      {
        accessorKey: 'item_total',
        header: 'Item Total',
        cell: ({ row }) => formatCurrency(row.original.item_total),
      },
    ],
    []
  );

  return (
    <div className="space-y-4">
      {/* Filter bar */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-4">
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="Closed">Closed</option>
            <option value="Invoiced">Invoiced</option>
            <option value="Partially_Invoiced">Partially Invoiced</option>
            <option value="Draft">Draft</option>
          </select>
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
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
        <DataTable columns={columns} data={data} emptyMessage="No sales orders found" />
      )}
    </div>
  );
}
