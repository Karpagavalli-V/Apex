import React, { useState } from 'react';
import Modal from '../common/Modal';
import Button from '../common/Button';
import Alert from '../common/Alert';
import { formatINR } from '../../utils/formatters';
import bankingService from '../../services/bankingService';

export const CreateAccountModal = ({ isOpen, onClose, onSuccess }) => {
  const [accountType, setAccountType] = useState('SAVINGS');
  const [initialDeposit, setInitialDeposit] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const numDeposit = parseFloat(initialDeposit) || 0;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const newAccount = await bankingService.createAccount({
        account_type: accountType,
        initial_deposit: numDeposit,
      });
      setInitialDeposit('');
      setAccountType('SAVINGS');
      onSuccess?.(newAccount);
      onClose();
    } catch (err) {
      setError(err.message || 'Account creation failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Open New Bank Account"
      subtitle="Create a verified high-yield Savings or flexible Checking account."
    >
      {error && <Alert variant="error" className="mb-4">{error}</Alert>}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
            Account Type
          </label>
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => setAccountType('SAVINGS')}
              className={`p-3 rounded-xl border text-left transition-all ${
                accountType === 'SAVINGS'
                  ? 'border-brand-600 bg-brand-50/50 text-brand-900 ring-2 ring-brand-500'
                  : 'border-slate-200 bg-white hover:bg-slate-50 text-slate-700'
              }`}
            >
              <div className="font-bold text-sm">SAVINGS</div>
              <p className="text-[11px] text-slate-500 mt-0.5">High liquidity with interest</p>
            </button>

            <button
              type="button"
              onClick={() => setAccountType('CHECKING')}
              className={`p-3 rounded-xl border text-left transition-all ${
                accountType === 'CHECKING'
                  ? 'border-brand-600 bg-brand-50/50 text-brand-900 ring-2 ring-brand-500'
                  : 'border-slate-200 bg-white hover:bg-slate-50 text-slate-700'
              }`}
            >
              <div className="font-bold text-sm">CHECKING</div>
              <p className="text-[11px] text-slate-500 mt-0.5">Everyday debit transactions</p>
            </button>
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
            Initial Deposit (Optional)
          </label>
          <div className="relative">
            <span className="absolute left-3 top-2.5 text-slate-400 font-semibold">₹</span>
            <input
              type="number"
              step="0.01"
              min="0"
              value={initialDeposit}
              onChange={(e) => setInitialDeposit(e.target.value)}
              placeholder="0.00"
              className="w-full pl-8 pr-3 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-brand-500 font-medium"
            />
          </div>
          <p className="mt-1 text-xs text-slate-500">
            {numDeposit > 0
              ? `Opening credit of ${formatINR(numDeposit)} will be ledger-recorded.`
              : 'Accounts can be opened with a ₹0.00 zero-balance.'}
          </p>
        </div>

        <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
          <Button variant="outline" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" loading={loading}>
            Create Account
          </Button>
        </div>
      </form>
    </Modal>
  );
};

export default CreateAccountModal;
