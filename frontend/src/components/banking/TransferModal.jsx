import React, { useState, useEffect, useRef } from 'react';
import { Search, CheckCircle2, User, X, ShieldCheck } from 'lucide-react';
import Modal from '../common/Modal';
import Button from '../common/Button';
import Alert from '../common/Alert';
import { formatINR } from '../../utils/formatters';
import bankingService from '../../services/bankingService';
import UpiPinModal from './UpiPinModal';

export const TransferModal = ({ isOpen, onClose, accounts = [], onSuccess }) => {
  const [accountIdState, setAccountIdState] = useState('');
  const selectedAccountId = accountIdState || accounts[0]?.account_id || '';
  const [destinationAccount, setDestinationAccount] = useState('');
  const [selectedBeneficiary, setSelectedBeneficiary] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef(null);

  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showConfirm, setShowConfirm] = useState(false);
  const [showPinModal, setShowPinModal] = useState(false);
  const [pinError, setPinError] = useState(null);

  const numAmount = parseFloat(amount) || 0;
  const sourceAccount = accounts.find((a) => a.account_id === selectedAccountId);
  const currentBalance = sourceAccount?.balance_inr !== undefined
    ? sourceAccount.balance_inr
    : (sourceAccount?.balance_paise || 0) / 100;
  const isOverdraft = numAmount > currentBalance;
  const isSameAccount = destinationAccount.trim() === sourceAccount?.account_number;

  // Search beneficiaries as user types (GPay style)
  useEffect(() => {
    let active = true;
    const fetchBeneficiaries = async () => {
      try {
        setIsSearching(true);
        const results = await bankingService.lookupBeneficiaries(searchQuery.trim());
        if (active) {
          // Filter out source account
          const filtered = (results || []).filter(
            (b) => b.account_number !== sourceAccount?.account_number
          );
          setSearchResults(filtered);
        }
      } catch (err) {
        console.error('Failed to lookup beneficiaries:', err);
      } finally {
        if (active) setIsSearching(false);
      }
    };

    const timer = setTimeout(fetchBeneficiaries, 200);
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [searchQuery, sourceAccount?.account_number]);

  // Handle outside click to close dropdown
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelectBeneficiary = (b) => {
    setSelectedBeneficiary(b);
    setDestinationAccount(b.account_number || b.apex_pay_id);
    setSearchQuery('');
    setShowDropdown(false);
    setError(null);
  };

  const handleClearBeneficiary = () => {
    setSelectedBeneficiary(null);
    setDestinationAccount('');
    setSearchQuery('');
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setError(null);

    if (!selectedAccountId) {
      setError('Please select a source account.');
      return;
    }

    const trimmedDest = destinationAccount.trim() || searchQuery.trim();
    if (!trimmedDest) {
      setError('Please select or enter a recipient (Name, Phone, Apex Pay ID, or Account Number).');
      return;
    }

    if (trimmedDest === sourceAccount?.account_number) {
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

  const handleProceedToPin = () => {
    setPinError(null);
    setShowPinModal(true);
  };

  const handlePinConfirm = async (enteredPin) => {
    setLoading(true);
    setPinError(null);
    setError(null);
    try {
      const targetParam = destinationAccount.trim() || searchQuery.trim();
      const result = await bankingService.transfer(selectedAccountId, {
        destination_account_number: targetParam,
        target_account: targetParam,
        amount: numAmount,
        description: description.trim() || 'Account Transfer',
        transaction_pin: enteredPin,
      });
      setShowPinModal(false);
      setShowConfirm(false);
      setAmount('');
      setDestinationAccount('');
      setSelectedBeneficiary(null);
      setDescription('');
      onSuccess?.(result);
      onClose();
    } catch (err) {
      setPinError(err.message || 'Transfer failed. Please check your UPI PIN and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Transfer Money"
      subtitle="Instantly transfer funds by Apex Pay ID, Phone Number, Name, or Account."
    >
      {error && <Alert variant="error" className="mb-4">{error}</Alert>}

      {!showConfirm ? (
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Source Account Selection */}
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

          {/* Recipient Field: GPay Style Search or Verified Card */}
          <div ref={dropdownRef} className="relative">
            <div className="flex justify-between items-center mb-1.5">
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                Recipient (Pay ID, Phone, or Account)
              </label>
              {accounts.filter((a) => a.account_id !== selectedAccountId).length > 0 && (
                <select
                  onChange={(e) => {
                    if (e.target.value) {
                      setDestinationAccount(e.target.value);
                      setSelectedBeneficiary(null);
                    }
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

            {selectedBeneficiary ? (
              /* Verified Recipient Card (GPay style) */
              <div className="p-3 bg-emerald-50/80 border border-emerald-200 rounded-xl flex items-center justify-between transition-all">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-emerald-600 to-teal-500 text-white font-bold flex items-center justify-center text-sm shadow-sm ring-2 ring-emerald-100">
                    {selectedBeneficiary.full_name?.charAt(0).toUpperCase() || 'U'}
                  </div>
                  <div>
                    <div className="flex items-center gap-1.5 font-semibold text-slate-900 text-sm">
                      <span>{selectedBeneficiary.full_name}</span>
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                      <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100/80 px-1.5 py-0.2 rounded-full">
                        VERIFIED
                      </span>
                    </div>
                    <div className="text-xs text-slate-500 flex items-center gap-2 mt-0.5 font-mono">
                      <span className="text-emerald-700 font-medium">{selectedBeneficiary.apex_pay_id}</span>
                      {selectedBeneficiary.phone_number && (
                        <span>• {selectedBeneficiary.phone_number}</span>
                      )}
                    </div>
                    <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                      A/C: {selectedBeneficiary.account_number} ({selectedBeneficiary.account_type})
                    </div>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={handleClearBeneficiary}
                  className="text-xs font-semibold text-slate-600 hover:text-slate-900 bg-white hover:bg-slate-50 px-2.5 py-1.5 rounded-lg border border-slate-200 transition-colors"
                >
                  Change
                </button>
              </div>
            ) : (
              /* Dynamic Autocomplete Input */
              <div className="relative">
                <div className="relative flex items-center">
                  <input
                    type="text"
                    value={searchQuery || destinationAccount}
                    onChange={(e) => {
                      const val = e.target.value;
                      setSearchQuery(val);
                      setDestinationAccount(val);
                      setShowDropdown(true);
                    }}
                    onFocus={() => setShowDropdown(true)}
                    placeholder="Search Name, Phone, or charu_01@apex..."
                    className="w-full pl-9 pr-8 py-2.5 border border-slate-300 rounded-xl text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-brand-500"
                    required
                  />
                  <Search className="w-4 h-4 text-slate-400 absolute left-3 pointer-events-none" />
                  {(searchQuery || destinationAccount) && (
                    <button
                      type="button"
                      onClick={() => {
                        setSearchQuery('');
                        setDestinationAccount('');
                      }}
                      className="absolute right-2.5 p-1 text-slate-400 hover:text-slate-600 rounded-md"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>

                {/* Dropdown with Real-Time Suggestions */}
                {showDropdown && searchResults.length > 0 && (
                  <div className="absolute top-full left-0 right-0 mt-1.5 bg-white border border-slate-200 rounded-2xl shadow-xl z-50 max-h-60 overflow-y-auto divide-y divide-slate-100">
                    <div className="px-3 py-1.5 bg-slate-50 text-[10px] font-bold uppercase tracking-wider text-slate-500 sticky top-0">
                      Suggested Verified Beneficiaries
                    </div>
                    {searchResults.map((b) => (
                      <button
                        key={b.account_id || b.account_number || b.username}
                        type="button"
                        onClick={() => handleSelectBeneficiary(b)}
                        className="w-full p-3 text-left hover:bg-brand-50/60 transition-colors flex items-center justify-between gap-3 group"
                      >
                        <div className="flex items-center gap-2.5 min-w-0">
                          <div className="w-8 h-8 rounded-full bg-brand-100 border border-brand-200 text-brand-700 font-bold text-xs flex items-center justify-center shrink-0 group-hover:bg-brand-600 group-hover:text-white transition-colors">
                            {b.full_name?.charAt(0).toUpperCase() || <User className="w-3.5 h-3.5" />}
                          </div>
                          <div className="min-w-0">
                            <div className="flex items-center gap-1.5">
                              <span className="font-semibold text-xs text-slate-900 truncate">
                                {b.full_name}
                              </span>
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                            </div>
                            <div className="text-[11px] text-slate-500 truncate flex items-center gap-1.5 font-mono">
                              <span className="text-brand-600 font-medium">{b.apex_pay_id}</span>
                              {b.phone_number && (
                                <span>• {b.phone_number}</span>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="text-right shrink-0">
                          <span className="text-[10px] font-mono bg-slate-100 text-slate-600 px-2 py-0.5 rounded-md border border-slate-200">
                            A/C: ••••{b.account_number?.slice(-4)}
                          </span>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {isSameAccount && (
              <p className="mt-1 text-xs text-rose-600 font-medium">
                Destination cannot be the same as your source account.
              </p>
            )}
          </div>

          {/* Transfer Amount Field */}
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

          {/* Memo / Description */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Transfer Purpose / Memo
            </label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g. Dinner split, Rent, Fee settlement"
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
        /* Confirmation Screen */
        <div className="space-y-4 text-left">
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2.5 text-sm">
            <div className="flex justify-between text-slate-600">
              <span>From Account:</span>
              <span className="font-semibold text-slate-900">
                {sourceAccount?.account_type} ({sourceAccount?.account_number})
              </span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Recipient:</span>
              <span className="font-semibold text-slate-900 flex items-center gap-1">
                {selectedBeneficiary ? (
                  <>
                    <span>{selectedBeneficiary.full_name}</span>
                    <span className="text-xs text-brand-700 font-mono">({selectedBeneficiary.apex_pay_id})</span>
                  </>
                ) : (
                  <span className="font-mono">{destinationAccount}</span>
                )}
              </span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Amount:</span>
              <span className="font-bold text-slate-900 text-base text-brand-700">
                {formatINR(numAmount)}
              </span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Purpose:</span>
              <span className="text-slate-800">{description || 'Account Transfer'}</span>
            </div>
            <div className="pt-2 border-t border-slate-200 flex justify-between text-xs text-slate-500">
              <span>Remaining Balance:</span>
              <span className="font-medium text-slate-700">
                {formatINR(currentBalance - numAmount)}
              </span>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-indigo-50/60 border border-indigo-100 flex items-start gap-2 text-xs text-indigo-700">
            <ShieldCheck className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
            <span>
              This transfer will execute atomically via Apex Private Ledger with real-time ML risk scoring.
            </span>
          </div>

          <div className="flex items-center justify-end gap-3 pt-2">
            <Button variant="outline" onClick={() => setShowConfirm(false)} disabled={loading}>
              Back
            </Button>
            <Button variant="primary" onClick={handleProceedToPin} loading={loading}>
              Proceed to UPI PIN
            </Button>
          </div>
        </div>
      )}

      {/* 4-Digit UPI PIN Verification Modal (GPay / PhonePe style) */}
      <UpiPinModal
        isOpen={showPinModal}
        onClose={() => {
          if (!loading) setShowPinModal(false);
        }}
        onConfirm={handlePinConfirm}
        amount={numAmount}
        recipient={selectedBeneficiary ? `${selectedBeneficiary.full_name} (${selectedBeneficiary.apex_pay_id})` : (destinationAccount.trim() || searchQuery.trim())}
        sourceAccount={sourceAccount}
        loading={loading}
        error={pinError}
      />
    </Modal>
  );
};

export default TransferModal;
