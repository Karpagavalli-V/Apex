import React, { useState, useEffect, useMemo } from 'react';
import { useOutletContext, Link } from 'react-router-dom';
import {
  Wallet,
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  ArrowDownLeft,
  Repeat,
  Sparkles,
  Plus,
  ChevronRight,
  ShieldCheck,
  CreditCard,
  Clock,
  Eye,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { useAuth } from '../context/AuthContext';
import transactionService from '../services/transactionService';
import aiService from '../services/aiService';
import { formatINR, formatDate, maskAccountNumber } from '../utils/formatters';
import StatCard from '../components/common/StatCard';
import Badge from '../components/common/Badge';
import Button from '../components/common/Button';
import EmptyState from '../components/common/EmptyState';
import Modal from '../components/common/Modal';

export const DashboardPage = () => {
  const { user } = useAuth();
  const {
    accounts,
    loadingAccounts,
    openDeposit,
    openWithdraw,
    openTransfer,
    openCreateAccount,
  } = useOutletContext();

  const [recentTransactions, setRecentTransactions] = useState([]);
  const [loadingTransactions, setLoadingTransactions] = useState(true);
  const [aiSummary, setAiSummary] = useState(null);
  const [loadingAi, setLoadingAi] = useState(false);
  const [selectedTx, setSelectedTx] = useState(null);

  // Calculate aggregate metrics across all user accounts
  const totalBalancePaise = useMemo(() => {
    return accounts.reduce((acc, curr) => acc + (curr.balance_paise || 0), 0);
  }, [accounts]);

  // Load recent transactions
  useEffect(() => {
    let isMounted = true;
    const fetchDashboardData = async () => {
      try {
        setLoadingTransactions(true);
        const data = await transactionService.getMyTransactions({ page: 1, limit: 7 });
        if (isMounted) {
          setRecentTransactions(data.transactions || []);
        }
      } catch (err) {
        console.error('Failed to load recent transactions:', err);
      } finally {
        if (isMounted) setLoadingTransactions(false);
      }

      // Load AI summary for monthly metrics
      try {
        setLoadingAi(true);
        const summaryData = await aiService.getFinancialSummary();
        if (isMounted) {
          setAiSummary(summaryData);
        }
      } catch (err) {
        console.error('Failed to load AI financial summary:', err);
      } finally {
        if (isMounted) setLoadingAi(false);
      }
    };

    fetchDashboardData();
    return () => {
      isMounted = false;
    };
  }, [accounts]);

  // Prepare chart data from AI summary or transactions
  const currentMonthMetrics = aiSummary?.data?.metrics || aiSummary?.data?.current_month;
  const aiSummaryContent = aiSummary?.data?.summary;

  const monthlyData = useMemo(() => {
    if (currentMonthMetrics) {
      const cur = currentMonthMetrics;
      const prior = cur.mom_comparison;
      return [
        {
          name: prior?.has_prior_data ? (cur.previous_month || 'Previous Month') : 'Previous Month',
          Deposits: prior?.has_prior_data ? (prior.prev_deposits_inr || (prior.prev_deposits_paise / 100) || 0) : 0,
          Withdrawals: prior?.has_prior_data ? (prior.prev_outflow_inr || (prior.prev_outflow_paise / 100) || 0) : 0,
          Transfers: 0,
        },
        {
          name: cur.month || 'Current Month',
          Deposits: (cur.total_deposits_paise || (cur.total_deposits_inr * 100) || 0) / 100,
          Withdrawals: (cur.total_withdrawals_paise || (cur.total_withdrawals_inr * 100) || 0) / 100,
          Transfers: (cur.total_transfers_paise || (cur.total_transfers_inr * 100) || 0) / 100,
        },
      ];
    }
    // Fallback: estimate from recent transactions
    return [
      { name: 'Estimated Flow', Deposits: 0, Withdrawals: 0, Transfers: 0 }
    ];
  }, [currentMonthMetrics]);

  return (
    <div className="space-y-6 sm:space-y-7">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-br from-[#101d36] via-[#172b4d] to-[#1d3670] rounded-[26px] p-6 sm:p-8 lg:p-9 text-white shadow-xl shadow-slate-900/10 relative overflow-hidden ring-1 ring-white/10">
        <div className="absolute inset-0 opacity-[0.08] pointer-events-none" aria-hidden="true">
          <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.2)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.2)_1px,transparent_1px)] bg-[size:34px_34px]" />
        </div>
        <div className="absolute -right-16 -top-32 w-96 h-96 bg-brand-400/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute right-1/3 -bottom-40 w-72 h-72 bg-indigo-400/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col xl:flex-row xl:items-center justify-between gap-7">
          <div className="space-y-3 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/[0.09] backdrop-blur-md text-[11px] font-semibold tracking-wide text-blue-100 border border-white/[0.12]">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-300" />
              <span>YOUR MONEY, PROTECTED</span>
            </div>
            <h1 className="text-2xl sm:text-3xl lg:text-[34px] font-bold tracking-tight">
              Welcome back, {user?.full_name?.split(/\s+/)[0] || user?.username || 'there'}
            </h1>
            <p className="text-blue-100/75 text-sm sm:text-[15px] leading-relaxed max-w-xl">
              Your accounts, recent activity, and cash flow — all in one clear view.
            </p>
          </div>

          {/* Quick Action Buttons */}
          <div className="flex flex-wrap items-center gap-2.5">
            <Button
              variant="primary"
              size="sm"
              icon={ArrowDownLeft}
              onClick={openDeposit}
              className="bg-emerald-500 hover:bg-emerald-400 border-none shadow-lg shadow-emerald-950/25"
            >
              Deposit
            </Button>
            <Button
              variant="outline"
              size="sm"
              icon={ArrowUpRight}
              onClick={openWithdraw}
              className="border-white/20 text-white hover:bg-white/10 hover:border-white/40"
            >
              Withdraw
            </Button>
            <Button
              variant="outline"
              size="sm"
              icon={Repeat}
              onClick={openTransfer}
              className="border-white/20 text-white hover:bg-white/10 hover:border-white/40"
            >
              Transfer
            </Button>
            <Button
              variant="secondary"
              size="sm"
              icon={Plus}
              onClick={openCreateAccount}
            >
              New Account
            </Button>
          </div>
        </div>
      </div>

      {/* Primary Financial Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Liquidity"
          value={formatINR(totalBalancePaise)}
          subtitle={`${accounts.length} active account${accounts.length === 1 ? '' : 's'}`}
          icon={Wallet}
          accentColor="indigo"
          loading={loadingAccounts}
        />
        <StatCard
          title="Monthly Inflows"
          value={formatINR(currentMonthMetrics?.total_deposits_paise || 0)}
          subtitle="Total verified deposits"
          icon={TrendingUp}
          accentColor="emerald"
          loading={loadingAi}
        />
        <StatCard
          title="Monthly Outflows"
          value={formatINR((currentMonthMetrics?.total_withdrawals_paise || 0) + (currentMonthMetrics?.total_transfers_paise || 0))}
          subtitle="Withdrawals & Transfers"
          icon={TrendingDown}
          accentColor="rose"
          loading={loadingAi}
        />
        <StatCard
          title="Net Cash Flow"
          value={formatINR(currentMonthMetrics?.net_cash_flow_paise || 0)}
          subtitle={
            currentMonthMetrics?.cash_flow_health
              ? `Health: ${currentMonthMetrics.cash_flow_health}`
              : 'Monthly delta'
          }
          icon={Sparkles}
          accentColor="amber"
          loading={loadingAi}
        />
      </div>

      {/* Main Grid: Accounts & Spending Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: My Accounts (1 col) */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h2 className="text-base font-semibold text-slate-900">Your Bank Accounts</h2>
              <p className="text-xs text-slate-500">Atomic ledger records</p>
            </div>
            <Link
              to="/accounts"
              className="text-xs font-semibold text-brand-600 hover:text-brand-700 flex items-center gap-1"
            >
              View all <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {loadingAccounts ? (
            <div className="space-y-3">
              {[1, 2].map((i) => (
                <div key={i} className="h-24 bg-slate-100 animate-pulse rounded-xl" />
              ))}
            </div>
          ) : accounts.length === 0 ? (
            <div className="py-8 text-center space-y-3">
              <CreditCard className="w-10 h-10 text-slate-300 mx-auto" />
              <p className="text-sm text-slate-600 font-medium">No accounts active yet</p>
              <Button size="sm" variant="primary" onClick={openCreateAccount}>
                Open Your First Account
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              {accounts.slice(0, 3).map((account) => (
                <div
                  key={account.account_id}
                  className="p-4 rounded-xl border border-slate-100 bg-slate-50/70 hover:bg-slate-50 hover:border-slate-200 transition-all"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-mono font-medium text-slate-600 tracking-wider">
                      {maskAccountNumber(account.account_number)}
                    </span>
                    <Badge variant={account.account_type} size="sm">
                      {account.account_type}
                    </Badge>
                  </div>
                  <div className="flex items-baseline justify-between">
                    <div>
                      <p className="text-xs text-slate-500 font-medium">Available Balance</p>
                      <p className="text-lg font-bold text-slate-900">
                        {formatINR(account.balance_paise)}
                      </p>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={openDeposit}
                        className="p-1.5 rounded-lg bg-emerald-50 text-emerald-700 hover:bg-emerald-100 transition-colors"
                        title="Quick Deposit"
                      >
                        <ArrowDownLeft className="w-4 h-4" />
                      </button>
                      <button
                        onClick={openTransfer}
                        className="p-1.5 rounded-lg bg-indigo-50 text-indigo-700 hover:bg-indigo-100 transition-colors"
                        title="Quick Transfer"
                      >
                        <Repeat className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          <Button
            variant="outline"
            size="sm"
            className="w-full justify-center"
            icon={Plus}
            onClick={openCreateAccount}
          >
            Create Another Account
          </Button>
        </div>

        {/* Right Column: Financial Flow Chart (2 cols) */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-slate-100 mb-4">
              <div>
                <h2 className="text-base font-semibold text-slate-900">Monthly Cash Flow Breakdown</h2>
                <p className="text-xs text-slate-500">
                  Aggregated deposits vs withdrawals and transfers
                </p>
              </div>
              <div className="flex items-center gap-2">
                {currentMonthMetrics?.cash_flow_health && (
                  <Badge variant={currentMonthMetrics.cash_flow_health} size="sm">
                    Health: {currentMonthMetrics.cash_flow_health}
                  </Badge>
                )}
                <Link
                  to="/ai-assistant"
                  className="inline-flex items-center gap-1 text-xs font-semibold text-brand-600 hover:text-brand-700 bg-brand-50 px-2.5 py-1 rounded-lg"
                >
                  <Sparkles className="w-3.5 h-3.5" /> AI Analysis
                </Link>
              </div>
            </div>

            {/* Recharts BarChart */}
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={monthlyData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} tickLine={false} />
                  <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} tickFormatter={(val) => `₹${val}`} />
                  <Tooltip
                    formatter={(value) => [`₹${Number(value).toLocaleString('en-IN')}`, '']}
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderRadius: '12px',
                      color: '#ffffff',
                      border: 'none',
                      boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
                      fontSize: '12px',
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '8px' }} />
                  <Bar dataKey="Deposits" fill="#10b981" radius={[6, 6, 0, 0]} maxBarSize={45} />
                  <Bar dataKey="Withdrawals" fill="#f43f5e" radius={[6, 6, 0, 0]} maxBarSize={45} />
                  <Bar dataKey="Transfers" fill="#6366f1" radius={[6, 6, 0, 0]} maxBarSize={45} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* AI Narrative Preview */}
          {(aiSummaryContent?.overview || aiSummary?.data?.executive_overview) && (
            <div className="mt-4 p-3.5 rounded-xl bg-slate-50 border border-slate-100 flex items-start gap-3">
              <Sparkles className="w-5 h-5 text-brand-600 flex-shrink-0 mt-0.5" />
              <div className="text-xs text-slate-700 leading-relaxed">
                <span className="font-semibold text-slate-900">AI Financial Takeaway: </span>
                {aiSummaryContent?.overview || aiSummary?.data?.executive_overview}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Recent Transactions Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Recent Transactions</h2>
            <p className="text-xs text-slate-500">Live ledger activity and ML risk classifications</p>
          </div>
          <Link
            to="/transactions"
            className="text-xs font-semibold text-brand-600 hover:text-brand-700 flex items-center gap-1"
          >
            Full history <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {loadingTransactions ? (
          <div className="p-8 text-center text-sm text-slate-500">
            <Clock className="w-6 h-6 animate-spin mx-auto text-brand-600 mb-2" />
            Loading transaction ledger...
          </div>
        ) : recentTransactions.length === 0 ? (
          <div className="py-12">
            <EmptyState
              title="No transactions recorded yet"
              description="Make your initial deposit or transfer to start building your ledger history."
              actionLabel="Make a Deposit"
              onAction={openDeposit}
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="bg-slate-50/80 border-b border-slate-100 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  <th className="py-3 px-4 sm:px-6">Type</th>
                  <th className="py-3 px-4">Date & Time</th>
                  <th className="py-3 px-4">Description</th>
                  <th className="py-3 px-4 text-right">Amount</th>
                  <th className="py-3 px-4 text-right">Balance After</th>
                  <th className="py-3 px-4 text-center">Risk Level</th>
                  <th className="py-3 px-4 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-normal">
                {recentTransactions.map((tx) => {
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
                        {tx.description || (isTransfer ? `Transfer to ${tx.destination_account_number || 'account'}` : 'Banking transaction')}
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
                          title="View Details"
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
        )}
      </div>

      {/* Transaction Details Modal */}
      {selectedTx && (
        <Modal
          isOpen={!!selectedTx}
          onClose={() => setSelectedTx(null)}
          title="Transaction Details"
        >
          <div className="space-y-4 text-sm">
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 space-y-2">
              <div className="flex justify-between items-center text-xs text-slate-500">
                <span>Transaction ID</span>
                <span className="font-mono text-slate-900">{selectedTx.transaction_id}</span>
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
                <span>Status</span>
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
                <span className="text-slate-600">Description</span>
                <span className="text-slate-900">{selectedTx.description || 'N/A'}</span>
              </div>
              {selectedTx.destination_account_number && (
                <div className="flex justify-between items-baseline py-1 border-b border-slate-100">
                  <span className="text-slate-600">Recipient Account</span>
                  <span className="font-mono font-medium text-slate-900">{selectedTx.destination_account_number}</span>
                </div>
              )}
            </div>

            {/* ML Fraud Risk Section */}
            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-brand-600" />
                  Random Forest ML Evaluation
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

export default DashboardPage;
