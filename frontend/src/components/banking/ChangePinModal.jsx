import React, { useState } from 'react';
import { Lock, ShieldCheck, CheckCircle2, AlertCircle } from 'lucide-react';
import Modal from '../common/Modal';
import Button from '../common/Button';
import Alert from '../common/Alert';
import authService from '../../services/authService';

export const ChangePinModal = ({ isOpen, onClose, onSuccess }) => {
  const [pin, setPin] = useState('');
  const [confirmPin, setConfirmPin] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);

    const cleanPin = pin.trim();
    const cleanConfirm = confirmPin.trim();

    if (!/^\d{4}$/.test(cleanPin)) {
      setError('PIN must be exactly 4 numeric digits (0-9).');
      return;
    }

    if (cleanPin !== cleanConfirm) {
      setError('New PIN and confirmation PIN do not match.');
      return;
    }

    setLoading(true);
    try {
      await authService.setTransactionPin({
        pin: cleanPin,
        confirm_pin: cleanConfirm,
      });
      setSuccessMsg('4-Digit UPI Transaction PIN updated successfully!');
      setTimeout(() => {
        setPin('');
        setConfirmPin('');
        setSuccessMsg(null);
        onSuccess?.();
        onClose();
      }, 1200);
    } catch (err) {
      setError(err.message || 'Failed to update transaction PIN. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setPin('');
      setConfirmPin('');
      setError(null);
      setSuccessMsg(null);
      onClose();
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Set / Change UPI PIN"
      subtitle="Your 4-digit security PIN is required to authorize all outgoing transfers."
    >
      {error && <Alert variant="error" className="mb-4">{error}</Alert>}
      {successMsg && <Alert variant="success" className="mb-4">{successMsg}</Alert>}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
            New 4-Digit UPI PIN
          </label>
          <div className="relative">
            <input
              type="password"
              maxLength={4}
              inputMode="numeric"
              pattern="\d{4}"
              value={pin}
              onChange={(e) => setPin(e.target.value.replace(/\D/g, '').slice(0, 4))}
              placeholder="••••"
              className="w-full px-4 py-2.5 text-center tracking-[0.5em] text-lg font-bold border border-slate-300 rounded-xl text-slate-900 focus:outline-none focus:ring-2 focus:ring-brand-500"
              required
            />
          </div>
          <p className="text-[11px] text-slate-500 mt-1">
            Choose a secret 4-digit number that you can easily remember.
          </p>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
            Confirm 4-Digit UPI PIN
          </label>
          <div className="relative">
            <input
              type="password"
              maxLength={4}
              inputMode="numeric"
              pattern="\d{4}"
              value={confirmPin}
              onChange={(e) => setConfirmPin(e.target.value.replace(/\D/g, '').slice(0, 4))}
              placeholder="••••"
              className="w-full px-4 py-2.5 text-center tracking-[0.5em] text-lg font-bold border border-slate-300 rounded-xl text-slate-900 focus:outline-none focus:ring-2 focus:ring-brand-500"
              required
            />
          </div>
        </div>

        <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-600 flex items-start gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
          <span>
            Your PIN is irreversibly hashed using standard Bcrypt security before storage. It is never visible in plaintext.
          </span>
        </div>

        <div className="flex items-center justify-end gap-3 pt-2">
          <Button variant="outline" type="button" onClick={handleClose} disabled={loading}>
            Cancel
          </Button>
          <Button variant="primary" type="submit" loading={loading} disabled={pin.length !== 4 || confirmPin.length !== 4}>
            Save UPI PIN
          </Button>
        </div>
      </form>
    </Modal>
  );
};

export default ChangePinModal;
