import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import {
  CreditCard,
  Plus,
  Copy,
  Check,
  Eye,
  EyeOff,
  ArrowDownLeft,
  Repeat,
  ArrowUpRight,
  Clock,
  RefreshCw,
} from 'lucide-react';
import { formatPaiseToINR, formatDate, maskAccountNumber } from '../utils/formatters';
import bankingService from '../services/bankingService';
import Button from '../components/common/Button';
import Badge from '../components/common/Badge';
import EmptyState from '../components/common/EmptyState';

export const AccountsPage = () => {
  const {
    accounts,
    loadingAccounts,
    refreshAccounts,
    openDeposit,
    openTransfer,
    openCreateAccount,
  } = useOutletContext();

  const [accountIdState, setAccountIdState] = useState(null);
  const selectedAccountId = accountIdState || accounts[0]?.account_id;

  const [accountTransactions, setAccountTransactions] = useState([]);
  const [loadingTx, setLoadingTx] = useState(false);
  const [txPage, setTxPage] = useState(1);
  const [txTotalPages, setTxTotalPages] = useState(1);
  const [txTypeFilter, setTxTypeFilter] = useState('');
  const [copiedId, setCopiedId] = useState(null);
  const [unmaskedAccounts, setUnmaskedAccounts] = useState({});
  const [refreshing, setRefreshing] = useState(false);

  // Fetch account-specific transactions when selected account or filters change
  useEffect(() => {
    if (!selectedAccountId) return;

    let isMounted = true;
    const fetchTransactions = async () => {
      try {
        setLoadingTx(true);
        const data = await bankingService.getAccountTransactions(selectedAccountId, {
          page: txPage,
          limit: 10,
          type: txTypeFilter || null,
        });
        if (isMounted) {
          setAccountTransactions(data.transactions || []);
          if (data.pagination) {
            setTxTotalPages(data.pagination.total_pages || 1);
          }
        }
      } catch (err) {
        console.error('Failed to load account transactions:', err);
      } finally {
        if (isMounted) setLoadingTx(false);
      }
    };

    fetchTransactions();
    return () => {
      isMounted = false;
    };
  }, [selectedAccountId, txPage, txTypeFilter]);

  const handleCopy = (accNum, id) => {
    navigator.clipboard.writeText(accNum);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const toggleMask = (id) => {
    setUnmaskedAccounts((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const handleManualRefresh = async () => {
    setRefreshing(true);
    await refreshAccounts();
    setRefreshing(false);
  };

  const selectedAccount = accounts.find((a) => a.account_id === selectedAccountId);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Bank Accounts</h1>
          <p className="text-sm text-slate-500">
            Manage your deposit and checking accounts with atomic balance updates.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            icon={RefreshCw}
            loading={refreshing}
            onClick={handleManualRefresh}
          >
            Sync
          </Button>
          <Button
            variant="primary"
            size="sm"
            icon={Plus}
            onClick={openCreateAccount}
            className="shadow-sm"
          >
            Open New Account
          </Button>
        </div>
      </div>

      {/* Account Cards Grid */}
      {loadingAccounts ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-48 bg-slate-100 animate-pulse rounded-2xl" />
          ))}
        </div>
      ) : accounts.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200/80 p-8">
          <EmptyState
            title="No bank accounts found"
            description="You do not have any active bank accounts. Open a savings or checking account with zero or initial deposit."
            actionLabel="Open Account"
            onAction={openCreateAccount}
          />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {accounts.map((acc) => {
            const isSelected = acc.account_id === selectedAccountId;
            const isCopied = copiedId === acc.account_id;
            const isUnmasked = unmaskedAccounts[acc.account_id];
            const displayAccNum = isUnmasked
              ? acc.account_number
              : maskAccountNumber(acc.account_number);

            return (
              <div
                key={acc.account_id}
                onClick={() => setAccountIdState(acc.account_id)}
                className={`relative rounded-2xl p-5 border cursor-pointer transition-all ${
                  isSelected
                    ? 'border-brand-600 bg-white ring-2 ring-brand-500/10 shadow-md'
                    : 'border-slate-200/80 bg-white hover:border-slate-300 hover:shadow-sm'
                }`}
              >
                {/* Account Type and Status */}
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <div className="p-2 rounded-xl bg-brand-50 text-brand-600">
                      <CreditCard className="w-5 h-5" />
                    </div>
                    <div>
                      <h2 className="text-sm font-semibold text-slate-900">
                        {acc.account_type === 'SAVINGS' ? 'Apex Savings' : 'Apex Checking'}
                      </h2>
                      <span className="text-[11px] text-slate-400">
                        ID: {acc.account_id?.slice(-6)}
                      </span>
                    </div>
                  </div>
                  <Badge variant={acc.status || 'ACTIVE'} size="sm">
                    {acc.status || 'ACTIVE'}
                  </Badge>
                </div>

                {/* Account Number with copy and mask */}
                <div className="flex items-center justify-between p-2.5 bg-slate-50 rounded-xl mb-4 text-xs font-mono">
                  <span className="text-slate-700 tracking-wider font-semibold">
                    {displayAccNum}
                  </span>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleMask(acc.account_id);
                      }}
                      className="p-1 rounded text-slate-400 hover:text-slate-600"
                      title={isUnmasked ? 'Mask Account Number' : 'Reveal Account Number'}
                    >
                      {isUnmasked ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCopy(acc.account_number, acc.account_id);
                      }}
                      className="p-1 rounded text-slate-400 hover:text-slate-600"
                      title="Copy to clipboard"
                    >
                      {isCopied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>

                {/* Balance Display */}
                <div className="mb-4">
                  <span className="text-xs text-slate-500 font-medium">Available Balance</span>
                  <div className="text-2xl font-bold text-slate-900 tracking-tight">
                    {formatPaiseToINR(acc.balance_paise)}
                  </div>
                </div>

                {/* Quick Action Footer */}
                <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="text-slate-400">
                    Opened {formatDate(acc.created_at)}
                  </span>
                  <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
                    <button
                      onClick={openDeposit}
                      className="px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-700 font-medium hover:bg-emerald-100 transition-colors"
                    >
                      Deposit
                    </button>
                    <button
                      onClick={openTransfer}
                      className="px-2.5 py-1 rounded-lg bg-indigo-50 text-indigo-700 font-medium hover:bg-indigo-100 transition-colors"
                    >
                      Transfer
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Selected Account Detailed History */}
      {selectedAccount && (
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
          <div className="p-5 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-semibold text-slate-900">
                  Account Ledger: {maskAccountNumber(selectedAccount.account_number)}
                </h2>
                <Badge variant={selectedAccount.account_type} size="sm">
                  {selectedAccount.account_type}
                </Badge>
              </div>
              <p className="text-xs text-slate-500">
                Detailed statement for account ID {selectedAccount.account_id}
              </p>
            </div>

            {/* Filter by Type */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 font-medium">Filter:</span>
              <select
                value={txTypeFilter}
                onChange={(e) => {
                  setTxTypeFilter(e.target.value);
                  setTxPage(1);
                }}
                className="text-xs font-medium rounded-lg border-slate-200 bg-slate-50 py-1.5 px-3 text-slate-700 focus:outline-none focus:ring-1 focus:ring-brand-500"
              >
                <option value="">All Transactions</option>
                <option value="DEPOSIT">Deposits Only</option>
                <option value="WITHDRAWAL">Withdrawals Only</option>
                <option value="TRANSFER">Transfers Only</option>
              </select>
            </div>
          </div>

          {/* Transactions Table */}
          {loadingTx ? (
            <div className="p-8 text-center text-sm text-slate-500">
              <Clock className="w-6 h-6 animate-spin mx-auto text-brand-600 mb-2" />
              Loading statement entries...
            </div>
          ) : accountTransactions.length === 0 ? (
            <div className="py-8">
              <EmptyState
                title="No transactions for this account"
                description={
                  txTypeFilter
                    ? `No ${txTypeFilter.toLowerCase()} transactions found.`
                    : 'This account has no transaction history yet.'
                }
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
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-normal">
                    {accountTransactions.map((tx) => {
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
                          <td className="py-3.5 px-4 text-xs text-slate-800 max-w-sm truncate">
                            {tx.description || (isTransfer ? `Transfer to ${tx.destination_account_number}` : 'Standard transaction')}
                          </td>
                          <td className="py-3.5 px-4 text-right font-bold text-xs whitespace-nowrap">
                            <span className={isDeposit ? 'text-emerald-600' : 'text-slate-900'}>
                              {isDeposit ? '+' : '-'} {formatPaiseToINR(tx.amount_paise)}
                            </span>
                          </td>
                          <td className="py-3.5 px-4 text-right text-xs font-mono text-slate-600 whitespace-nowrap">
                            {formatPaiseToINR(tx.balance_after_paise)}
                          </td>
                          <td className="py-3.5 px-4 text-center">
                            <Badge variant={tx.risk_level || 'NORMAL'} size="sm">
                              {tx.risk_level || 'NORMAL'}
                            </Badge>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Statement Pagination */}
              {txTotalPages > 1 && (
                <div className="p-4 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="text-slate-500">
                    Page {txPage} of {txTotalPages}
                  </span>
                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={txPage <= 1}
                      onClick={() => setTxPage((p) => Math.max(1, p - 1))}
                    >
                      Previous
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={txPage >= txTotalPages}
                      onClick={() => setTxPage((p) => Math.min(txTotalPages, p + 1))}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default AccountsPage;
