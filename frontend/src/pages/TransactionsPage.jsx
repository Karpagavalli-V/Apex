import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  ArrowDownLeft,
  ArrowUpRight,
  Repeat,
  Search,
  Eye,
  Clock,
  ShieldCheck,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
} from 'lucide-react';
import transactionService from '../services/transactionService';
import { formatINR, formatDate } from '../utils/formatters';
import Badge from '../components/common/Badge';
import Button from '../components/common/Button';
import EmptyState from '../components/common/EmptyState';
import Modal from '../components/common/Modal';

export const TransactionsPage = () => {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  // Filters
  const [typeFilter, setTypeFilter] = useState('ALL');
  const [riskFilter, setRiskFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Selected Transaction for Details Modal
  const [selectedTx, setSelectedTx] = useState(null);

  const fetchTransactions = useCallback(async () => {
    try {
      setLoading(true);
      const data = await transactionService.getMyTransactions({
        page,
        limit: 12,
        type: typeFilter !== 'ALL' ? typeFilter : null,
      });
      setTransactions(data.transactions || []);
      if (data.pagination) {
        setTotalPages(data.pagination.total_pages || 1);
        setTotalCount(data.pagination.total_count || 0);
      }
    } catch (err) {
      console.error('Failed to fetch transactions:', err);
    } finally {
      setLoading(false);
    }
  }, [page, typeFilter]);

  useEffect(() => {
    fetchTransactions();
  }, [fetchTransactions]);

  // Client-side search and risk filtering on the loaded page
  const filteredTransactions = useMemo(() => {
    return transactions.filter((tx) => {
      // Risk filter
      if (riskFilter !== 'ALL') {
        if ((tx.risk_level || 'NORMAL') !== riskFilter) {
          return false;
        }
      }

      // Search query filter
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const desc = (tx.description || '').toLowerCase();
        const txId = (tx.transaction_id || '').toLowerCase();
        const dest = (tx.destination_account_number || '').toLowerCase();
        return desc.includes(q) || txId.includes(q) || dest.includes(q);
      }

      return true;
    });
  }, [transactions, riskFilter, searchQuery]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Transaction History</h1>
          <p className="text-sm text-slate-500">
            Immutable financial audit trail across all your personal Apex Bank accounts.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            icon={RefreshCw}
            loading={loading}
            onClick={fetchTransactions}
          >
            Refresh
          </Button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Search Input */}
        <div className="relative w-full md:w-80">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
            <Search className="w-4 h-4" />
          </div>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search memo, ID, or recipient..."
            className="w-full pl-9 pr-4 py-2 rounded-xl border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          {/* Type Filter */}
          <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium">
            <span>Type:</span>
            <select
              value={typeFilter}
              onChange={(e) => {
                setTypeFilter(e.target.value);
                setPage(1);
              }}
              className="text-xs font-semibold rounded-lg border-slate-200 bg-slate-50 py-1.5 px-3 text-slate-700 focus:outline-none focus:ring-1 focus:ring-brand-500"
            >
              <option value="ALL">All Operations</option>
              <option value="DEPOSIT">Deposits</option>
              <option value="WITHDRAWAL">Withdrawals</option>
              <option value="TRANSFER">Transfers</option>
            </select>
          </div>

          {/* Risk Level Filter */}
          <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium">
            <span>Risk Tier:</span>
            <select
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
              className="text-xs font-semibold rounded-lg border-slate-200 bg-slate-50 py-1.5 px-3 text-slate-700 focus:outline-none focus:ring-1 focus:ring-brand-500"
            >
              <option value="ALL">All Risk Tiers</option>
              <option value="NORMAL">Normal</option>
              <option value="SUSPICIOUS">Suspicious</option>
              <option value="HIGH_RISK">High Risk</option>
            </select>
          </div>
        </div>
      </div>

      {/* Ledger Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-sm text-slate-500">
            <Clock className="w-8 h-8 animate-spin mx-auto text-brand-600 mb-2" />
            Loading transactions ledger...
          </div>
        ) : filteredTransactions.length === 0 ? (
          <div className="py-12">
            <EmptyState
              title="No transactions match your criteria"
              description="Try adjusting your search terms or clearing the active type/risk filters."
              actionLabel="Clear Filters"
              onAction={() => {
                setTypeFilter('ALL');
                setRiskFilter('ALL');
                setSearchQuery('');
              }}
            />
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-sm">
                <thead>
                  <tr className="bg-slate-50/80 border-b border-slate-100 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    <th className="py-3 px-4 sm:px-6">Type</th>
                    <th className="py-3 px-4">Date & Time</th>
                    <th className="py-3 px-4">Description</th>
                    <th className="py-3 px-4 text-right">Amount</th>
                    <th className="py-3 px-4 text-right">Balance After</th>
                    <th className="py-3 px-4 text-center">Risk Assessment</th>
                    <th className="py-3 px-4 text-center">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-normal">
                  {filteredTransactions.map((tx) => {
                    const isDeposit = tx.type === 'DEPOSIT';
                    const isTransfer = tx.type === 'TRANSFER';
                    return (
                      <tr key={tx.transaction_id} className="hover:bg-slate-50/60 transition-colors">
                        <td className="py-3.5 px-4 sm:px-6">
                          <div className="flex items-center gap-2">
                            <div
                              className={`p-1.5 rounded-lg ${
                                isDeposit
                                  ? 'bg-emerald-50 text-emerald-600'
                                  : isTransfer
                                  ? 'bg-indigo-50 text-indigo-600'
                                  : 'bg-rose-50 text-rose-600'
                              }`}
                            >
                              {isDeposit ? (
                                <ArrowDownLeft className="w-3.5 h-3.5" />
                              ) : isTransfer ? (
                                <Repeat className="w-3.5 h-3.5" />
                              ) : (
                                <ArrowUpRight className="w-3.5 h-3.5" />
                              )}
                            </div>
                            <span className="font-semibold text-xs text-slate-900">{tx.type}</span>
                          </div>
                        </td>
                        <td className="py-3.5 px-4 text-xs text-slate-600 whitespace-nowrap">
                          {formatDate(tx.timestamp)}
                        </td>
                        <td className="py-3.5 px-4 text-xs text-slate-800 max-w-xs truncate">
                          {tx.description || (isTransfer ? `Transfer to ${tx.destination_account_number}` : 'Banking transaction')}
                        </td>
                        <td className="py-3.5 px-4 text-right font-bold text-xs whitespace-nowrap">
                          <span className={isDeposit ? 'text-emerald-600' : 'text-slate-900'}>
                            {isDeposit ? '+' : '-'} {formatINR(tx.amount_paise)}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-right text-xs font-mono text-slate-600 whitespace-nowrap">
                          {formatINR(tx.balance_after_paise)}
                        </td>
                        <td className="py-3.5 px-4 text-center">
                          <Badge variant={tx.risk_level || 'NORMAL'} size="sm">
                            {tx.risk_level || 'NORMAL'}
                          </Badge>
                        </td>
                        <td className="py-3.5 px-4 text-center">
                          <button
                            onClick={() => setSelectedTx(tx)}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-brand-600 hover:bg-brand-50 transition-colors"
                            title="Inspect Details"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div className="p-4 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs">
              <span className="text-slate-500">
                Showing {filteredTransactions.length} of {totalCount} transactions (Page {page} of {totalPages})
              </span>
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  icon={ChevronLeft}
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  Previous
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                >
                  Next <ChevronRight className="w-3.5 h-3.5 ml-1" />
                </Button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Details Modal */}
      {selectedTx && (
        <Modal
          isOpen={!!selectedTx}
          onClose={() => setSelectedTx(null)}
          title="Transaction Audit Record"
        >
          <div className="space-y-4 text-sm">
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 space-y-2">
              <div className="flex justify-between items-center text-xs text-slate-500">
                <span>Transaction ID</span>
                <span className="font-mono font-medium text-slate-900">{selectedTx.transaction_id}</span>
              </div>
              <div className="flex justify-between items-center text-xs text-slate-500">
                <span>Account ID</span>
                <span className="font-mono text-slate-900">{selectedTx.account_id}</span>
              </div>
              <div className="flex justify-between items-center text-xs text-slate-500">
                <span>Timestamp</span>
                <span className="text-slate-900">{formatDate(selectedTx.timestamp)}</span>
              </div>
              <div className="flex justify-between items-center text-xs text-slate-500">
                <span>Type</span>
                <Badge variant={selectedTx.type} size="sm">{selectedTx.type}</Badge>
              </div>
              <div className="flex justify-between items-center text-xs text-slate-500">
                <span>Ledger Status</span>
                <Badge variant={selectedTx.status || 'COMPLETED'} size="sm">{selectedTx.status || 'COMPLETED'}</Badge>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-baseline py-1 border-b border-slate-100">
                <span className="text-slate-600">Amount</span>
                <span className="text-base font-bold text-slate-900">{formatINR(selectedTx.amount_paise)}</span>
              </div>
              <div className="flex justify-between items-baseline py-1 border-b border-slate-100">
                <span className="text-slate-600">Balance After</span>
                <span className="font-mono font-medium text-slate-900">{formatINR(selectedTx.balance_after_paise)}</span>
              </div>
              <div className="flex justify-between items-baseline py-1 border-b border-slate-100">
                <span className="text-slate-600">Memo / Description</span>
                <span className="text-slate-900">{selectedTx.description || 'N/A'}</span>
              </div>
              {selectedTx.destination_account_number && (
                <div className="flex justify-between items-baseline py-1 border-b border-slate-100">
                  <span className="text-slate-600">Counterparty Account</span>
                  <span className="font-mono font-medium text-slate-900">{selectedTx.destination_account_number}</span>
                </div>
              )}
            </div>

            {/* Random Forest Risk Metadata */}
            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-brand-600" />
                  Machine Learning Inference
                </span>
                <Badge variant={selectedTx.risk_level || 'NORMAL'} size="sm">
                  {selectedTx.risk_level || 'NORMAL'}
                </Badge>
              </div>
              <div className="text-xs text-slate-600 space-y-1">
                <div className="flex justify-between">
                  <span>Fraud Probability:</span>
                  <span className="font-mono font-medium text-slate-900">
                    {selectedTx.fraud_probability !== undefined
                      ? `${(selectedTx.fraud_probability * 100).toFixed(2)}%`
                      : '0.00%'}
                  </span>
                </div>
                {selectedTx.risk_explanation && (
                  <p className="text-slate-500 pt-1 border-t border-slate-200/60">
                    {selectedTx.risk_explanation}
                  </p>
                )}
              </div>
            </div>

            <Button
              variant="secondary"
              className="w-full justify-center"
              onClick={() => setSelectedTx(null)}
            >
              Close
            </Button>
          </div>
        </Modal>
      )}
    </div>
  );
};

export default TransactionsPage;
