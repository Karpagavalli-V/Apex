import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import {
  ArrowDownLeft,
  ArrowUpRight,
  Repeat,
  ShieldCheck,
  CheckCircle2,
} from 'lucide-react';
import bankingService from '../services/bankingService';
import { formatINR, maskAccountNumber } from '../utils/formatters';
import Button from '../components/common/Button';
import Alert from '../components/common/Alert';
import Badge from '../components/common/Badge';
import Modal from '../components/common/Modal';

export const OperationsPage = () => {
  const { accounts, loadingAccounts, refreshAccounts } = useOutletContext();

  const [activeTab, setActiveTab] = useState('deposit'); // deposit | withdraw | transfer

  // Common Form States
  const [accountIdState, setAccountIdState] = useState('');
  const selectedAccountId = accountIdState || accounts[0]?.account_id || '';
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');

  // Transfer specific
  const [destinationAccount, setDestinationAccount] = useState('');

  // UI / Submission state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [lastReceipt, setLastReceipt] = useState(null);

  const currentAccount = accounts.find((a) => a.account_id === selectedAccountId);
  const numericAmount = parseFloat(amount) || 0;
  const amountPaise = Math.round(numericAmount * 100);

  // Validation
  const validateForm = () => {
    setError(null);
    if (!currentAccount) {
      setError('Please select an active account for this operation.');
      return false;
    }
    if (!amount || numericAmount <= 0) {
      setError('Please enter a valid amount greater than ₹0.00.');
      return false;
    }

    if (activeTab === 'withdraw' || activeTab === 'transfer') {
      if (amountPaise > currentAccount.balance_paise) {
        setError(
          `Insufficient funds. Available balance is ${formatINR(currentAccount.balance_paise)}.`
        );
        return false;
      }
    }

    if (activeTab === 'transfer') {
      const trimmedDest = destinationAccount.trim();
      if (!trimmedDest || trimmedDest.length !== 12 || !/^\d{12}$/.test(trimmedDest)) {
        setError('Destination account number must be exactly 12 numeric digits.');
        return false;
      }
      if (trimmedDest === currentAccount.account_number) {
        setError('Self-transfers to the same account are prohibited.');
        return false;
      }
    }

    return true;
  };

  const handleInitiate = (e) => {
    e.preventDefault();
    if (validateForm()) {
      setShowConfirmModal(true);
    }
  };

  const handleExecuteOperation = async () => {
    setShowConfirmModal(false);
    setLoading(true);
    setError(null);
    setLastReceipt(null);

    try {
      let result;
      if (activeTab === 'deposit') {
        result = await bankingService.deposit(selectedAccountId, {
          amount: numericAmount,
          description: description || 'Account deposit',
        });
      } else if (activeTab === 'withdraw') {
        result = await bankingService.withdraw(selectedAccountId, {
          amount: numericAmount,
          description: description || 'Account withdrawal',
        });
      } else if (activeTab === 'transfer') {
        result = await bankingService.transfer(selectedAccountId, {
          destination_account_number: destinationAccount.trim(),
          amount: numericAmount,
          description: description || 'Account fund transfer',
        });
      }

      setLastReceipt(result);
      setAmount('');
      setDescription('');
      if (activeTab === 'transfer') {
        setDestinationAccount('');
      }
      await refreshAccounts();
    } catch (err) {
      console.error('Operation error:', err);
      setError(err.message || 'Operation failed. Please check parameters and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Banking Operations Hub</h1>
        <p className="text-sm text-slate-500">
          Execute deposits, withdrawals, and inter-account transfers with idempotency and real-time ML risk scoring.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200">
        <button
          onClick={() => {
            setActiveTab('deposit');
            setError(null);
          }}
          className={`flex items-center gap-2 py-3 px-5 border-b-2 font-medium text-sm transition-all ${
            activeTab === 'deposit'
              ? 'border-emerald-600 text-emerald-600'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <ArrowDownLeft className="w-4 h-4" />
          Deposit Funds
        </button>
        <button
          onClick={() => {
            setActiveTab('withdraw');
            setError(null);
          }}
          className={`flex items-center gap-2 py-3 px-5 border-b-2 font-medium text-sm transition-all ${
            activeTab === 'withdraw'
              ? 'border-rose-600 text-rose-600'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <ArrowUpRight className="w-4 h-4" />
          Withdraw Funds
        </button>
        <button
          onClick={() => {
            setActiveTab('transfer');
            setError(null);
          }}
          className={`flex items-center gap-2 py-3 px-5 border-b-2 font-medium text-sm transition-all ${
            activeTab === 'transfer'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <Repeat className="w-4 h-4" />
          Money Transfer
        </button>
      </div>

      {error && (
        <Alert variant="error" title="Transaction Validation Error">
          {error}
        </Alert>
      )}

      {/* Transaction Receipt Card */}
      {lastReceipt && (
        <div className="bg-emerald-50/70 border border-emerald-200 rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5 text-emerald-800">
              <CheckCircle2 className="w-6 h-6 text-emerald-600" />
              <div>
                <h3 className="font-semibold text-base">Transaction Completed Successfully</h3>
                <p className="text-xs text-emerald-600">
                  Transaction ID: <span className="font-mono font-bold">{lastReceipt.transaction?.transaction_id || lastReceipt.transaction_id}</span>
                </p>
              </div>
            </div>
            <Badge variant={lastReceipt.transaction?.risk_level || 'NORMAL'} size="md">
              {lastReceipt.transaction?.risk_level || 'NORMAL'}
            </Badge>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-3 border-t border-emerald-100 text-xs">
            <div>
              <span className="text-slate-500 block">Amount Processed</span>
              <span className="font-bold text-slate-900 text-sm">
                {formatINR(lastReceipt.transaction?.amount_paise || (numericAmount * 100))}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block">Updated Balance</span>
              <span className="font-bold text-slate-900 text-sm">
                {formatINR(lastReceipt.account?.balance_paise || lastReceipt.balance_paise || 0)}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block">ML Risk Probability</span>
              <span className="font-bold text-slate-900 text-sm font-mono">
                {lastReceipt.transaction?.fraud_probability !== undefined
                  ? `${(lastReceipt.transaction.fraud_probability * 100).toFixed(2)}%`
                  : '0.00%'}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block">Ledger Status</span>
              <span className="font-bold text-emerald-700 text-sm">
                COMPLETED
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Main Operations Card */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-6 sm:p-8 shadow-sm">
        <form onSubmit={handleInitiate} className="space-y-6">
          {/* Account Selector */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Select Source Account
            </label>
            {loadingAccounts ? (
              <div className="h-10 bg-slate-100 animate-pulse rounded-xl" />
            ) : accounts.length === 0 ? (
              <p className="text-sm text-slate-500">No active accounts available.</p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {accounts.map((acc) => {
                  const isSelected = acc.account_id === selectedAccountId;
                  return (
                    <div
                      key={acc.account_id}
                      onClick={() => setAccountIdState(acc.account_id)}
                      className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                        isSelected
                          ? 'border-brand-600 bg-brand-50/40 ring-2 ring-brand-500/20'
                          : 'border-slate-200 hover:border-slate-300 bg-slate-50/50'
                      }`}
                    >
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-medium text-slate-900">
                          {acc.account_type === 'SAVINGS' ? 'Apex Savings' : 'Apex Checking'}
                        </span>
                        <Badge variant={acc.account_type} size="sm">
                          {acc.account_type}
                        </Badge>
                      </div>
                      <div className="mt-2 flex items-baseline justify-between">
                        <span className="font-mono text-xs text-slate-500">
                          {maskAccountNumber(acc.account_number)}
                        </span>
                        <span className="font-bold text-sm text-slate-900">
                          {formatINR(acc.balance_paise)}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Transfer Destination Field (Only for Transfer tab) */}
          {activeTab === 'transfer' && (
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                Recipient 12-Digit Account Number
              </label>
              <input
                type="text"
                maxLength={12}
                value={destinationAccount}
                onChange={(e) => setDestinationAccount(e.target.value.replace(/\D/g, ''))}
                placeholder="e.g. 100010002000"
                className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <p className="text-xs text-slate-400 mt-1">
                Must be an existing 12-digit Apex Bank account number.
              </p>
            </div>
          )}

          {/* Amount Field */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                Transaction Amount (INR)
              </label>
              {currentAccount && (activeTab === 'withdraw' || activeTab === 'transfer') && (
                <button
                  type="button"
                  onClick={() => setAmount((currentAccount.balance_paise / 100).toFixed(2))}
                  className="text-xs font-semibold text-brand-600 hover:text-brand-700"
                >
                  Use Max Available ({formatINR(currentAccount.balance_paise)})
                </button>
              )}
            </div>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400 font-semibold">
                ₹
              </div>
              <input
                type="number"
                step="0.01"
                min="0.01"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.00"
                className="w-full pl-8 pr-4 py-2.5 rounded-xl border border-slate-200 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
            {numericAmount > 0 && (
              <p className="text-xs text-slate-500 mt-1">
                Backend representation:{' '}
                <span className="font-mono font-semibold">{amountPaise} paise</span>
              </p>
            )}
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Transaction Memo / Reference (Optional)
            </label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder={
                activeTab === 'deposit'
                  ? 'e.g. Salary deposit, Consulting fee'
                  : activeTab === 'withdraw'
                  ? 'e.g. ATM cash withdrawal'
                  : 'e.g. Rent payment, Vendor disbursement'
              }
              className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>

          {/* Security Notice */}
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100 flex items-start gap-3">
            <ShieldCheck className="w-5 h-5 text-brand-600 flex-shrink-0 mt-0.5" />
            <div className="text-xs text-slate-600 leading-relaxed">
              <span className="font-semibold text-slate-800">Idempotent Execution & Anti-Fraud: </span>
              Each transaction transmits a unique idempotency UUID to prevent accidental double-billing. All requests are evaluated synchronously by our Random Forest classifier.
            </div>
          </div>

          {/* Submit Button */}
          <Button
            type="submit"
            variant="primary"
            size="lg"
            className="w-full justify-center shadow-md"
            disabled={loading || accounts.length === 0}
          >
            Review & Confirm {activeTab.toUpperCase()}
          </Button>
        </form>
      </div>

      {/* Confirmation Modal */}
      {showConfirmModal && (
        <Modal
          isOpen={showConfirmModal}
          onClose={() => setShowConfirmModal(false)}
          title={`Confirm ${activeTab.toUpperCase()}`}
        >
          <div className="space-y-4 text-sm">
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-100 space-y-3">
              <div className="flex justify-between items-center text-xs text-slate-500">
                <span>Operation</span>
                <span className="font-bold text-slate-900 uppercase">{activeTab}</span>
              </div>
              <div className="flex justify-between items-center text-xs text-slate-500">
                <span>Source Account</span>
                <span className="font-mono text-slate-900">
                  {currentAccount?.account_number}
                </span>
              </div>
              {activeTab === 'transfer' && (
                <div className="flex justify-between items-center text-xs text-slate-500">
                  <span>Destination Account</span>
                  <span className="font-mono text-slate-900">{destinationAccount}</span>
                </div>
              )}
              <div className="flex justify-between items-center text-xs text-slate-500">
                <span>Amount</span>
                <span className="text-base font-bold text-slate-900">{formatINR(amountPaise)}</span>
              </div>
              <div className="flex justify-between items-center text-xs text-slate-500">
                <span>Balance After (Estimated)</span>
                <span className="font-mono font-medium text-slate-900">
                  {activeTab === 'deposit'
                    ? formatINR(currentAccount.balance_paise + amountPaise)
                    : formatINR(currentAccount.balance_paise - amountPaise)}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                className="w-1/2 justify-center"
                onClick={() => setShowConfirmModal(false)}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                className="w-1/2 justify-center"
                loading={loading}
                onClick={handleExecuteOperation}
              >
                Execute Now
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

export default OperationsPage;
