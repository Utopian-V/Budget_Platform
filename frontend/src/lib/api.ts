import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

// Dashboard
export const getDashboardSummary = () => api.get('/dashboard/summary');
export const getDepartmentSummary = () => api.get('/dashboard/department-summary');
export const getRecentActivity = () => api.get('/dashboard/recent-activity');

// Budget
export const getBudgetLines = (params: Record<string, unknown>) => api.get('/budget/lines', { params });
export const getBudgetLine = (id: number) => api.get(`/budget/lines/${id}`);
export const updateBudgetLine = (id: number, data: Record<string, unknown>) => api.put(`/budget/lines/${id}`, data);
export const getVarianceData = (params: Record<string, unknown>) => api.get('/budget/variance', { params });
export const updateVariance = (budgetLineId: number, month: string, data: Record<string, unknown>) =>
  api.put(`/budget/variance/${budgetLineId}/${month}`, data);

// Invoices
export const getInvoices = (params: Record<string, unknown>) => api.get('/invoices', { params });
export const getInvoiceSummary = (month: string) => api.get(`/invoices/summary/${month}`);
export const getCleanupReport = () => api.get('/invoices/cleanup-report');

// Sales Orders
export const getSalesOrders = (params: Record<string, unknown>) => api.get('/sales-orders', { params });

// Credit Notes
export const getCreditNotes = (params: Record<string, unknown>) => api.get('/credit-notes', { params });

// Proposals
export const getProposals = (params: Record<string, unknown>) => api.get('/proposals', { params });
export const getProposalStats = () => api.get('/proposals/stats');
export const getPipeline = (params: Record<string, unknown>) => api.get('/pipeline', { params });

// Reconciliation
export const runReconciliation = (month: string) => api.post(`/reconciliation/run/${month}`);
export const runFullReconciliation = () => api.post('/reconciliation/run-all');
export const getRecoSummary = (month: string) => api.get(`/reconciliation/summary/${month}`);
export const getUnmatched = (month: string) => api.get(`/reconciliation/unmatched/${month}`);
export const getNewAdditions = (month: string) => api.get(`/reconciliation/new-additions/${month}`);

// Snapshots
export const createSnapshot = (month: string) => api.post(`/reconciliation/snapshot/${month}`);
export const listSnapshots = () => api.get('/reconciliation/snapshots');
export const getSnapshot = (id: number) => api.get(`/reconciliation/snapshot/${id}`);

// Reports
export const getDeptVarianceReport = (month: string) => api.get(`/reports/department-variance/${month}`);
export const getMtdYtdReport = () => api.get('/reports/mtd-ytd');
export const getClientSummary = () => api.get('/reports/client-summary');
export const getTrueUpCandidates = (threshold?: number) => api.get('/reports/true-up-candidates', { params: threshold ? { threshold } : {} });
export const exportReport = (reportType: string, month?: string) =>
  api.get(`/reports/export/${reportType}`, { params: month ? { month } : {}, responseType: 'blob' });

// Budget - Promote
export const promoteToBudget = (recoId: number) => api.post(`/budget/promote`, { reconciliation_record_id: recoId });

// Master
export const getMasterData = (type: string) => api.get(`/master/${type}`);
export const createMasterItem = (type: string, data: Record<string, unknown>) => api.post(`/master/${type}`, data);
export const updateMasterItem = (type: string, id: number, data: Record<string, unknown>) => api.put(`/master/${type}/${id}`, data);
export const deleteMasterItem = (type: string, id: number) => api.delete(`/master/${type}/${id}`);

// Import
export const importAll = () => api.post('/import/all');
export const importSpecific = (type: string) => api.post(`/import/${type}`);

// Zoho
export const getZohoStatus = () => api.get('/zoho/status');
export const syncZohoAll = () => api.post('/zoho/sync/all');
export const syncZohoInvoices = () => api.post('/zoho/sync/invoices');
export const syncZohoSalesOrders = () => api.post('/zoho/sync/sales-orders');
export const syncZohoCreditNotes = () => api.post('/zoho/sync/credit-notes');

export default api;
