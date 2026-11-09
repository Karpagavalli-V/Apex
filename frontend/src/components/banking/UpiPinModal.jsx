import React, { useState, useEffect, useRef } from 'react';
import { Lock, Delete, Check, ShieldCheck, X, AlertCircle } from 'lucide-react';
import { formatINR } from '../../utils/formatters';

export const UpiPinModal = ({
  isOpen,
  onClose,
  onConfirm,
  amount = 0,
  recipient = '',
  sourceAccount = null,
  loading = false,
  error = null,
}) => {
  const [pin, setPin] = useState('');
  const [localError, setLocalError] = useState(null);
  const hiddenInputRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      setPin('');
      setLocalError(null);
      setTimeout(() => {
        hiddenInputRef.current?.focus();
      }, 100);
    }
  }, [isOpen]);

  useEffect(() => {
    if (error) {
      setLocalError(error);
      setPin('');
    }
  }, [error]);

  if (!isOpen) return null;

  const handleDigit = (digit) => {
    if (pin.length < 4) {
      const nextPin = pin + digit;
      setPin(nextPin);
      setLocalError(null);
    }
  };

  const handleBackspace = () => {
    setPin((prev) => prev.slice(0, -1));
    setLocalError(null);
  };

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if (pin.length !== 4) {
      setLocalError('Please enter all 4 digits of your UPI PIN.');
      return;
    }
    setLocalError(null);
    onConfirm(pin);
  };

  const handleKeyDown = (e) => {
    if (e.key >= '0' && e.key <= '9') {
      handleDigit(e.key);
    } else if (e.key === 'Backspace') {
      handleBackspace();
    } else if (e.key === 'Enter' && pin.length === 4) {
      handleSubmit();
    } else if (e.key === 'Escape') {
      onClose();
    }
  };

  const activeError = localError || error;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm transition-opacity"
        onClick={() => {
          if (!loading) onClose();
        }}
      />

      {/* Viewport centering wrapper (prevents top/bottom clipping) */}
      <div className="flex min-h-full items-center justify-center p-3 sm:p-4 text-center">
        <div
          className="relative w-full max-w-[340px] sm:max-w-sm my-auto bg-gradient-to-b from-[#0f172a] via-[#111e38] to-[#0c1322] rounded-3xl text-white shadow-2xl border border-slate-700/60 overflow-hidden flex flex-col text-left animate-in zoom-in-95 duration-150"
          onKeyDown={handleKeyDown}
          tabIndex={0}
        >
          {/* Hidden input to capture physical keyboard input seamlessly */}
          <input
            ref={hiddenInputRef}
            type="password"
            maxLength={4}
            inputMode="numeric"
            value={pin}
            onChange={(e) => {
              const clean = e.target.value.replace(/\D/g, '').slice(0, 4);
              setPin(clean);
            }}
            className="sr-only"
            autoFocus
          />

          {/* Top Bar */}
          <div className="flex items-center justify-between px-5 py-3 border-b border-white/10">
            <div className="flex items-center gap-2 text-xs font-bold tracking-wider uppercase text-blue-300">
              <Lock className="w-3.5 h-3.5 text-brand-400" />
              <span>Apex UPI Verification</span>
            </div>
            <button
              type="button"
              disabled={loading}
              onClick={onClose}
              className="p-1 rounded-full text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
              title="Close"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Transaction Summary Badge */}
          <div className="px-5 py-2.5 bg-white/5 border-b border-white/5 text-center">
            <p className="text-[11px] text-slate-300 font-medium">Paying to</p>
            <p className="text-sm font-bold text-white mt-0.5 truncate">{recipient}</p>
            <p className="text-2xl font-extrabold text-emerald-400 mt-0.5 font-mono tracking-tight">
              {formatINR(amount)}
            </p>
            {sourceAccount && (
              <p className="text-[10px] text-slate-400 mt-0.5 font-mono">
                Debiting A/C: ••••{sourceAccount.account_number?.slice(-4)}
              </p>
            )}
          </div>

          {/* PIN Entry Area */}
          <div className="px-5 pt-3.5 pb-2 flex flex-col items-center">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-300 mb-2.5">
              Enter 4-Digit UPI PIN
            </p>

            {/* 4 Masked Digits Display */}
            <div
              className="flex items-center justify-center gap-3 cursor-pointer"
              onClick={() => hiddenInputRef.current?.focus()}
            >
              {[0, 1, 2, 3].map((idx) => {
                const isFilled = pin.length > idx;
                const isCurrent = pin.length === idx;
                return (
                  <div
                    key={idx}
                    className={`w-11 h-12 rounded-xl border-2 flex items-center justify-center transition-all ${
                      isFilled
                        ? 'border-brand-400 bg-brand-500/20 shadow-inner'
                        : isCurrent
                        ? 'border-blue-400 bg-white/10 ring-2 ring-blue-400/40'
                        : 'border-slate-600 bg-white/5'
                    }`}
                  >
                    {isFilled ? (
                      <span className="w-3 h-3 rounded-full bg-brand-400 shadow-[0_0_8px_rgba(56,189,248,0.8)]" />
                    ) : (
                      <span className="text-xs text-slate-500 font-mono">•</span>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Error Banner */}
            {activeError && (
              <div className="mt-2 text-center text-xs text-rose-300 bg-rose-950/80 border border-rose-800/80 px-2.5 py-1 rounded-lg flex items-center gap-1.5 animate-shake">
                <AlertCircle className="w-3.5 h-3.5 shrink-0 text-rose-400" />
                <span>{activeError}</span>
              </div>
            )}
          </div>

          {/* On-Screen Numeric Keypad (GPay / PhonePe style) */}
          <div className="px-5 pb-4 pt-1 select-none">
            <div className="grid grid-cols-3 gap-2">
              {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((num) => (
                <button
                  key={num}
                  type="button"
                  disabled={loading}
                  onClick={() => handleDigit(String(num))}
                  className="h-11 sm:h-12 rounded-xl bg-white/10 hover:bg-white/20 active:bg-brand-500/30 text-white font-semibold text-lg border border-white/10 transition-all flex items-center justify-center disabled:opacity-50 cursor-pointer"
                >
                  {num}
                </button>
              ))}

              {/* Row 4: Backspace, 0, Submit */}
              <button
                type="button"
                disabled={loading || pin.length === 0}
                onClick={handleBackspace}
                className="h-11 sm:h-12 rounded-xl bg-white/5 hover:bg-white/15 text-slate-300 font-semibold border border-white/10 transition-all flex items-center justify-center disabled:opacity-40 cursor-pointer"
                title="Delete last digit"
              >
                <Delete className="w-5 h-5" />
              </button>

              <button
                type="button"
                disabled={loading}
                onClick={() => handleDigit('0')}
                className="h-11 sm:h-12 rounded-xl bg-white/10 hover:bg-white/20 active:bg-brand-500/30 text-white font-semibold text-lg border border-white/10 transition-all flex items-center justify-center disabled:opacity-50 cursor-pointer"
              >
                0
              </button>

              <button
                type="button"
                disabled={loading || pin.length !== 4}
                onClick={handleSubmit}
                className={`h-11 sm:h-12 rounded-xl font-bold border transition-all flex items-center justify-center ${
                  pin.length === 4 && !loading
                    ? 'bg-emerald-500 hover:bg-emerald-400 text-white border-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.5)] cursor-pointer'
                    : 'bg-white/5 text-slate-500 border-white/10 cursor-not-allowed opacity-40'
                }`}
                title="Submit PIN"
              >
                {loading ? (
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Check className="w-6 h-6" />
                )}
              </button>
            </div>

            <div className="flex items-center justify-center gap-1.5 text-[10px] text-slate-400 mt-2.5">
              <ShieldCheck className="w-3.5 h-3.5 text-brand-400" />
              <span>256-bit Bcrypt Encrypted PIN Verification</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UpiPinModal;
