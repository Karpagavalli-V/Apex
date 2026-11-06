import React, { useState } from 'react';
import Modal from '../common/Modal';
import Button from '../common/Button';
import Alert from '../common/Alert';
import { formatINR } from '../../utils/formatters';
import bankingService from '../../services/bankingService';

export const DepositModal = ({ isOpen, onClose, accounts = [], onSuccess }) => {
  const [accountIdState, setAccountIdState] = useState('');
  const selectedAccountId = accountIdState || accounts[0]?.account_id || '';
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showConfirm, setShowConfirm] = useState(false);

  const numAmount = parseFloat(amount) || 0;
  const selectedAccount = accounts.find((a) => a.account_id === selectedAccountId);

  const handleSubmit = (e) => {
    e.preventDefault();
    setError(null);

    if (!selectedAccountId) {
      setError('Please select an account for the deposit.');
      return;
    }

    if (numAmount <= 0) {
      setError('Please enter a valid deposit amount greater than ₹0.');
      return;
    }

    setShowConfirm(true);
  };

  const handleConfirmExecute = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await bankingService.deposit(selectedAccountId, {
        amount: numAmount,
        description: description.trim() || 'Account Deposit',
      });
      setShowConfirm(false);
      setAmount('');
      setDescription('');
      onSuccess?.(result);
      onClose();
    } catch (err) {
      setShowConfirm(false);
      setError(err.message || 'Deposit failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Deposit Funds"
      subtitle="Instantly add funds to your verified banking account."
    >
      {error && <Alert variant="error" className="mb-4">{error}</Alert>}

      {!showConfirm ? (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Target Account
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
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Deposit Amount (INR)
            </label>
            <div className="relative">
              <span className="absolute left-3 top-2.5 text-slate-400 font-semibold">₹</span>
              <input
                type="number"
                step="0.01"
                min="1"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="5,000.00"
                className="w-full pl-8 pr-3 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-brand-500 font-medium"
                required
              />
            </div>
            {numAmount > 0 && (
              <p className="mt-1 text-xs text-slate-500">
                Equivalent to {Math.round(numAmount * 100).toLocaleString('en-IN')} integer paise.
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
              placeholder="e.g. Salary, Client retainer, Savings top-up"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
            <Button variant="outline" onClick={onClose} disabled={loading}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" loading={loading}>
              Review Deposit
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
              <span>Deposit Amount:</span>
              <span className="font-bold text-emerald-600 text-base">{formatINR(numAmount)}</span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>New Balance:</span>
              <span className="font-semibold text-slate-900">
                {formatINR((selectedAccount?.balance_inr !== undefined ? selectedAccount.balance_inr : (selectedAccount?.balance_paise || 0) / 100) + numAmount)}
              </span>
            </div>
            {description && (
              <div className="flex justify-between text-slate-600 text-xs pt-1 border-t border-slate-200">
                <span>Memo:</span>
                <span className="text-slate-800">{description}</span>
              </div>
            )}
          </div>

          <p className="text-xs text-slate-500">
            Deposited funds are verified and scored through real-time ML anomaly detection.
          </p>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
            <Button variant="outline" onClick={() => setShowConfirm(false)} disabled={loading}>
              Back
            </Button>
            <Button variant="success" onClick={handleConfirmExecute} loading={loading}>
              Confirm Deposit
            </Button>
          </div>
        </div>
      )}
    </Modal>
  );
};

export default DepositModal;
