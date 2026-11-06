import React, { useState } from 'react';
import Modal from '../common/Modal';
import Button from '../common/Button';
import Alert from '../common/Alert';
import { formatINR } from '../../utils/formatters';
import bankingService from '../../services/bankingService';

export const WithdrawModal = ({ isOpen, onClose, accounts = [], onSuccess }) => {
  const [accountIdState, setAccountIdState] = useState('');
  const selectedAccountId = accountIdState || accounts[0]?.account_id || '';
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showConfirm, setShowConfirm] = useState(false);

  const numAmount = parseFloat(amount) || 0;
  const selectedAccount = accounts.find((a) => a.account_id === selectedAccountId);
  const currentBalance = selectedAccount?.balance_inr !== undefined
    ? selectedAccount.balance_inr
    : (selectedAccount?.balance_paise || 0) / 100;
  const isOverdraft = numAmount > currentBalance;

  const handleSubmit = (e) => {
    e.preventDefault();
    setError(null);

    if (!selectedAccountId) {
      setError('Please select an account for withdrawal.');
      return;
    }

    if (numAmount <= 0) {
      setError('Please enter a valid withdrawal amount greater than ₹0.');
      return;
    }

    if (isOverdraft) {
      setError(`Insufficient funds. Your current balance is ${formatINR(currentBalance)}.`);
      return;
    }

    setShowConfirm(true);
  };

  const handleConfirmExecute = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await bankingService.withdraw(selectedAccountId, {
        amount: numAmount,
        description: description.trim() || 'Account Withdrawal',
      });
      setShowConfirm(false);
      setAmount('');
      setDescription('');
      onSuccess?.(result);
      onClose();
    } catch (err) {
      setShowConfirm(false);
      setError(err.message || 'Withdrawal failed. Please check your balance and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Withdraw Funds"
      subtitle="Safely withdraw funds with atomic overdraft protection."
    >
      {error && <Alert variant="error" className="mb-4">{error}</Alert>}

      {!showConfirm ? (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Source Account
            </label>
            <select
              value={selectedAccountId}
              onChange={(e) => setAccountIdState(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500"
              required
            >
              {accounts.map((acc) => (
                <option key={acc.account_id} value={acc.account_id}>
                  {acc.account_type} ({acc.account_number}) — Balance: {formatINR(acc.balance_inr !== undefined ? acc.balance_inr : (acc.balance_paise || 0) / 100)}
                </option>
              ))}
            </select>
          </div>

          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                Withdrawal Amount (INR)
              </label>
              <button
                type="button"
                onClick={() => setAmount(String(currentBalance))}
                className="text-xs font-semibold text-brand-600 hover:text-brand-700 underline"
              >
                Max ({formatINR(currentBalance)})
              </button>
            </div>
            <div className="relative">
              <span className="absolute left-3 top-2.5 text-slate-400 font-semibold">₹</span>
              <input
                type="number"
                step="0.01"
                min="1"
                max={currentBalance}
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="2,500.00"
                className={`w-full pl-8 pr-3 py-2 border rounded-lg text-sm text-slate-900 focus:outline-none focus:ring-2 font-medium ${
                  isOverdraft
                    ? 'border-rose-400 focus:ring-rose-500 bg-rose-50/20'
                    : 'border-slate-300 focus:ring-brand-500'
                }`}
                required
              />
            </div>
            {isOverdraft && (
              <p className="mt-1 text-xs text-rose-600 font-medium">
                Amount exceeds current balance of {formatINR(currentBalance)}.
              </p>
            )}
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Description (Optional)
            </label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g. ATM cash, Rent payment, Bill"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
            <Button variant="outline" onClick={onClose} disabled={loading}>
              Cancel
            </Button>
            <Button type="submit" variant="danger" disabled={isOverdraft} loading={loading}>
              Review Withdrawal
            </Button>
          </div>
        </form>
      ) : (
        <div className="space-y-4 text-left">
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2 text-sm">
            <div className="flex justify-between text-slate-600">
              <span>Account:</span>
              <span className="font-semibold text-slate-900">
                {selectedAccount?.account_type} ({selectedAccount?.account_number})
              </span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Withdrawal Amount:</span>
              <span className="font-bold text-rose-600 text-base">-{formatINR(numAmount)}</span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Remaining Balance:</span>
              <span className="font-semibold text-slate-900">
                {formatINR(currentBalance - numAmount)}
              </span>
            </div>
          </div>

          <p className="text-xs text-slate-500">
            Protected by atomic overdraft query. Withdrawal will not execute if funds are insufficient.
          </p>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
            <Button variant="outline" onClick={() => setShowConfirm(false)} disabled={loading}>
              Back
            </Button>
            <Button variant="danger" onClick={handleConfirmExecute} loading={loading}>
              Confirm Withdrawal
            </Button>
          </div>
        </div>
      )}
    </Modal>
  );
};

export default WithdrawModal;
