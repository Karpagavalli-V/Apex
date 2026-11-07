import React, { useState } from 'react';
import Modal from '../common/Modal';
import Button from '../common/Button';
import Alert from '../common/Alert';
import { formatINR } from '../../utils/formatters';
import bankingService from '../../services/bankingService';

const DEMO_BENEFICIARIES = [
  { name: 'Charu (Savings)', number: '100466777930' },
  { name: 'Charu (Checking)', number: '100777536164' },
  { name: 'Maha', number: '100247052120' },
  { name: 'Suruthika', number: '100684224129' },
  { name: 'Divya', number: '100735941819' },
];

export const TransferModal = ({ isOpen, onClose, accounts = [], onSuccess }) => {
  const [accountIdState, setAccountIdState] = useState('');
  const selectedAccountId = accountIdState || accounts[0]?.account_id || '';
  const [destinationAccount, setDestinationAccount] = useState('');
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showConfirm, setShowConfirm] = useState(false);

  const numAmount = parseFloat(amount) || 0;
  const sourceAccount = accounts.find((a) => a.account_id === selectedAccountId);
  const currentBalance = sourceAccount?.balance_inr !== undefined
    ? sourceAccount.balance_inr
    : (sourceAccount?.balance_paise || 0) / 100;
  const isOverdraft = numAmount > currentBalance;
  const isSameAccount = destinationAccount.trim() === sourceAccount?.account_number;

  const handleSubmit = (e) => {
    e.preventDefault();
    setError(null);

    if (!selectedAccountId) {
      setError('Please select a source account.');
      return;
    }

    if (!destinationAccount.trim() || destinationAccount.trim().length !== 12) {
      setError('Destination account number must be exactly 12 digits (e.g. 100XXXXXXXXX).');
      return;
    }

    if (isSameAccount) {
      setError('Cannot transfer funds to the same account. Please specify a different recipient.');
      return;
    }

    if (numAmount <= 0) {
      setError('Please enter a transfer amount greater than ₹0.');
      return;
    }

    if (isOverdraft) {
      setError(`Insufficient balance. Current balance is ${formatINR(currentBalance)}.`);
      return;
    }

    setShowConfirm(true);
  };

  const handleConfirmExecute = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await bankingService.transfer(selectedAccountId, {
        destination_account_number: destinationAccount.trim(),
        amount: numAmount,
        description: description.trim() || 'Account Transfer',
      });
      setShowConfirm(false);
      setAmount('');
      setDestinationAccount('');
      setDescription('');
      onSuccess?.(result);
      onClose();
    } catch (err) {
      setShowConfirm(false);
      setError(err.message || 'Transfer failed. Please check details and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Transfer Money"
      subtitle="Instantly transfer funds to another verified bank account."
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
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                Recipient Account Number (12 Digits)
              </label>
              {accounts.filter((a) => a.account_id !== selectedAccountId).length > 0 && (
                <select
                  onChange={(e) => {
                    if (e.target.value) setDestinationAccount(e.target.value);
                  }}
                  value=""
                  className="text-xs bg-slate-100 border border-slate-200 text-slate-700 rounded-md px-1.5 py-0.5 focus:outline-none cursor-pointer hover:bg-slate-200"
                >
                  <option value="">Or your other account...</option>
                  {accounts
                    .filter((a) => a.account_id !== selectedAccountId)
                    .map((a) => (
                      <option key={a.account_id} value={a.account_number}>
                        {a.account_type} ({a.account_number})
                      </option>
                    ))}
                </select>
              )}
            </div>
            <input
              type="text"
              maxLength={12}
              pattern="\d{12}"
              value={destinationAccount}
              onChange={(e) => setDestinationAccount(e.target.value.replace(/\D/g, ''))}
              placeholder="100XXXXXXXXX"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-brand-500 font-mono tracking-wider"
              required
            />
            {isSameAccount && (
              <p className="mt-1 text-xs text-rose-600 font-medium">
                Destination cannot be the same as your source account.
              </p>
            )}

            {/* Quick Demo Beneficiaries */}
            <div className="mt-2.5">
              <div className="text-[11px] text-slate-500 font-medium mb-1.5 flex items-center justify-between">
                <span>Quick Select Recipient (Testing):</span>
                <span className="text-[10px] text-slate-400">Full 12-digit account</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {DEMO_BENEFICIARIES
                  .filter((b) => b.number !== sourceAccount?.account_number)
                  .map((b) => (
                    <button
                      key={b.number}
                      type="button"
                      onClick={() => setDestinationAccount(b.number)}
                      className={`text-[11px] px-2.5 py-1 rounded-full border transition-all ${
                        destinationAccount === b.number
                          ? 'bg-brand-50 border-brand-500 text-brand-700 font-semibold shadow-xs'
                          : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100 hover:border-slate-300'
                      }`}
                    >
                      {b.name} ({b.number.slice(-4)})
                    </button>
                  ))}
              </div>
            </div>
          </div>

          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                Transfer Amount (INR)
              </label>
              <span className="text-xs text-slate-500">
                Avail: {formatINR(currentBalance)}
              </span>
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
                placeholder="1,500.00"
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
                Amount exceeds available balance of {formatINR(currentBalance)}.
              </p>
            )}
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Transfer Purpose / Memo
            </label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g. Shared expenses, Payment, Loan return"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
            <Button variant="outline" onClick={onClose} disabled={loading}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={isOverdraft || isSameAccount} loading={loading}>
              Review Transfer
            </Button>
          </div>
        </form>
      ) : (
        <div className="space-y-4 text-left">
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2 text-sm">
            <div className="flex justify-between text-slate-600">
              <span>From:</span>
              <span className="font-semibold text-slate-900">
                {sourceAccount?.account_type} ({sourceAccount?.account_number})
              </span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>To:</span>
              <span className="font-mono font-semibold text-slate-900 tracking-wider">
                {destinationAccount}
              </span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Transfer Amount:</span>
              <span className="font-bold text-brand-600 text-base">{formatINR(numAmount)}</span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>New Source Balance:</span>
              <span className="font-semibold text-slate-900">
                {formatINR(currentBalance - numAmount)}
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
            Transfers are processed atomically across MongoDB replica set with automatic rollback if either debit or credit fails.
          </p>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
            <Button variant="outline" onClick={() => setShowConfirm(false)} disabled={loading}>
              Back
            </Button>
            <Button variant="primary" onClick={handleConfirmExecute} loading={loading}>
              Execute Transfer
            </Button>
          </div>
        </div>
      )}
    </Modal>
  );
};

export default TransferModal;
