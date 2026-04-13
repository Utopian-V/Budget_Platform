import { useState, useEffect } from 'react';
import { Upload, Loader2, CheckCircle2, Clock, Shield, Key, RefreshCw, AlertCircle } from 'lucide-react';
import { importSpecific, getZohoStatus, syncZohoAll, syncZohoInvoices, syncZohoSalesOrders, syncZohoCreditNotes } from '../lib/api';
import { cn } from '../lib/utils';

const IMPORT_TYPES = [
  { key: 'budget', label: 'Budget Sheet', description: 'Import budget lines and expected values' },
  { key: 'invoices', label: 'Invoices', description: 'Import invoice data from Excel files' },
  { key: 'sales-orders', label: 'Sales Orders', description: 'Import sales order data' },
  { key: 'credit-notes', label: 'Credit Notes', description: 'Import credit note adjustments' },
  { key: 'proposals', label: 'Proposals', description: 'Import proposal/pipeline data' },
] as const;

const ZOHO_SYNC_TYPES = [
  { key: 'invoices', label: 'Invoices', fn: syncZohoInvoices },
  { key: 'sales-orders', label: 'Sales Orders', fn: syncZohoSalesOrders },
  { key: 'credit-notes', label: 'Credit Notes', fn: syncZohoCreditNotes },
] as const;

type ImportKey = (typeof IMPORT_TYPES)[number]['key'];

interface ImportStatus {
  loading: boolean;
  success: boolean;
  error: boolean;
  time: string | null;
}

export default function Settings() {
  const [importStatuses, setImportStatuses] = useState<Record<ImportKey, ImportStatus>>(
    Object.fromEntries(
      IMPORT_TYPES.map(({ key }) => [key, { loading: false, success: false, error: false, time: null }])
    ) as Record<ImportKey, ImportStatus>
  );

  const [zohoStatus, setZohoStatus] = useState<{ configured: boolean; has_token: boolean; org_id: string | null } | null>(null);
  const [zohoSyncing, setZohoSyncing] = useState<Record<string, boolean>>({});
  const [zohoSyncResult, setZohoSyncResult] = useState<Record<string, { count?: number; error?: string; time: string }>>({});
  const [zohoSyncAll, setZohoSyncAll] = useState(false);

  useEffect(() => {
    getZohoStatus().then((res) => setZohoStatus(res.data)).catch(() => {});
  }, []);

  const handleImport = async (key: ImportKey) => {
    setImportStatuses((prev) => ({
      ...prev,
      [key]: { loading: true, success: false, error: false, time: null },
    }));
    try {
      await importSpecific(key);
      setImportStatuses((prev) => ({
        ...prev,
        [key]: { loading: false, success: true, error: false, time: new Date().toLocaleTimeString() },
      }));
    } catch {
      setImportStatuses((prev) => ({
        ...prev,
        [key]: { loading: false, success: false, error: true, time: null },
      }));
    }
  };

  const handleZohoSync = async (key: string, fn: () => ReturnType<typeof syncZohoInvoices>) => {
    setZohoSyncing((prev) => ({ ...prev, [key]: true }));
    try {
      const res = await fn();
      setZohoSyncResult((prev) => ({
        ...prev,
        [key]: { count: res.data.synced, time: new Date().toLocaleTimeString() },
      }));
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Sync failed';
      setZohoSyncResult((prev) => ({
        ...prev,
        [key]: { error: msg, time: new Date().toLocaleTimeString() },
      }));
    } finally {
      setZohoSyncing((prev) => ({ ...prev, [key]: false }));
    }
  };

  const handleZohoSyncAll = async () => {
    setZohoSyncAll(true);
    try {
      const res = await syncZohoAll();
      const results = res.data.results || {};
      const now = new Date().toLocaleTimeString();
      setZohoSyncResult({
        invoices: results.invoices != null ? { count: results.invoices, time: now } : { error: results.invoices_error || 'Failed', time: now },
        'sales-orders': results.sales_orders != null ? { count: results.sales_orders, time: now } : { error: results.sales_orders_error || 'Failed', time: now },
        'credit-notes': results.credit_notes != null ? { count: results.credit_notes, time: now } : { error: results.credit_notes_error || 'Failed', time: now },
      });
    } catch {
      // handle error
    } finally {
      setZohoSyncAll(false);
    }
  };

  return (
    <div className="max-w-3xl space-y-8">
      {/* Import Data */}
      <section>
        <h2 className="text-lg font-bold text-slate-900 mb-1">Import Data (Excel)</h2>
        <p className="text-sm text-slate-500 mb-4">Import data from uploaded Excel files on the server</p>
        <div className="space-y-3">
          {IMPORT_TYPES.map(({ key, label, description }) => {
            const st = importStatuses[key];
            return (
              <div
                key={key}
                className="bg-white rounded-xl shadow-sm border border-slate-100 p-4 flex items-center gap-4"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-slate-800">{label}</p>
                  <p className="text-xs text-slate-500 mt-0.5">{description}</p>
                  {st.time && (
                    <div className="flex items-center gap-1.5 mt-1.5">
                      <Clock className="w-3 h-3 text-slate-400" />
                      <span className="text-xs text-slate-400">Last imported: {st.time}</span>
                    </div>
                  )}
                  {st.error && (
                    <div className="flex items-center gap-1.5 mt-1.5">
                      <AlertCircle className="w-3 h-3 text-red-400" />
                      <span className="text-xs text-red-500">Import failed</span>
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {st.success && <CheckCircle2 className="w-5 h-5 text-green-500" />}
                  <button
                    onClick={() => handleImport(key)}
                    disabled={st.loading}
                    className={cn(
                      'flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors',
                      'bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-60'
                    )}
                  >
                    {st.loading ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Upload className="w-4 h-4" />
                    )}
                    Import
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Zoho Integration */}
      <section>
        <h2 className="text-lg font-bold text-slate-900 mb-1">Zoho Books Integration</h2>
        <p className="text-sm text-slate-500 mb-4">Sync live data from Zoho Books API</p>
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6 space-y-5">
          {/* Status */}
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-lg bg-orange-50">
              <Key className="w-6 h-6 text-orange-600" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-semibold text-slate-800">Zoho Books API</p>
              <p className="text-xs text-slate-500 mt-0.5">
                {zohoStatus?.org_id ? `Organization: ${zohoStatus.org_id}` : 'Checking status...'}
              </p>
            </div>
            <span className={cn(
              'px-3 py-1 rounded-full text-xs font-medium',
              zohoStatus?.configured
                ? 'bg-green-100 text-green-800'
                : 'bg-yellow-100 text-yellow-800'
            )}>
              {zohoStatus?.configured ? 'Connected' : 'Not Configured'}
            </span>
          </div>

          {zohoStatus?.configured && (
            <>
              {/* Sync All */}
              <div className="pt-3 border-t border-slate-100">
                <button
                  onClick={handleZohoSyncAll}
                  disabled={zohoSyncAll}
                  className="flex items-center gap-2 px-5 py-2.5 text-sm font-medium text-white bg-orange-600 rounded-lg hover:bg-orange-700 disabled:opacity-60 transition-colors"
                >
                  {zohoSyncAll ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <RefreshCw className="w-4 h-4" />
                  )}
                  Sync All from Zoho
                </button>
              </div>

              {/* Individual Sync */}
              <div className="space-y-3">
                {ZOHO_SYNC_TYPES.map(({ key, label, fn }) => {
                  const syncing = zohoSyncing[key];
                  const result = zohoSyncResult[key];
                  return (
                    <div key={key} className="flex items-center gap-4 pl-2">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-700">{label}</p>
                        {result && !result.error && (
                          <p className="text-xs text-green-600 mt-0.5">
                            Synced {result.count} items at {result.time}
                          </p>
                        )}
                        {result?.error && (
                          <p className="text-xs text-red-500 mt-0.5">{result.error}</p>
                        )}
                      </div>
                      <button
                        onClick={() => handleZohoSync(key, fn)}
                        disabled={!!syncing || zohoSyncAll}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-orange-700 bg-orange-50 rounded-lg hover:bg-orange-100 disabled:opacity-50 transition-colors"
                      >
                        {syncing ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <RefreshCw className="w-3.5 h-3.5" />
                        )}
                        Sync
                      </button>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </div>
      </section>

      {/* Google SSO */}
      <section>
        <h2 className="text-lg font-bold text-slate-900 mb-1">Authentication</h2>
        <p className="text-sm text-slate-500 mb-4">Single Sign-On configuration</p>
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-lg bg-blue-50">
              <Shield className="w-6 h-6 text-blue-600" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-semibold text-slate-800">Google SSO</p>
              <p className="text-xs text-slate-500 mt-0.5">Sign in with Google workspace accounts</p>
            </div>
            <span className="px-3 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
              Pending Setup
            </span>
          </div>
        </div>
      </section>
    </div>
  );
}
