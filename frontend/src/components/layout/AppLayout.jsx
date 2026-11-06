import React, { useState, useEffect, useCallback } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Navbar from './Navbar';
import DepositModal from '../banking/DepositModal';
import WithdrawModal from '../banking/WithdrawModal';
import TransferModal from '../banking/TransferModal';
import CreateAccountModal from '../banking/CreateAccountModal';
import bankingService from '../../services/bankingService';

export const AppLayout = () => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [accounts, setAccounts] = useState([]);
  const [loadingAccounts, setLoadingAccounts] = useState(true);

  // Global Banking Modals State
  const [depositOpen, setDepositOpen] = useState(false);
  const [withdrawOpen, setWithdrawOpen] = useState(false);
  const [transferOpen, setTransferOpen] = useState(false);
  const [createAccountOpen, setCreateAccountOpen] = useState(false);

  // Success Notification banner/toast if needed
  const [successToast, setSuccessToast] = useState(null);

  const fetchAccounts = useCallback(async () => {
    try {
      const accts = await bankingService.getMyAccounts();
      setAccounts(accts);
    } catch (err) {
      console.error('Failed to load accounts in AppLayout:', err);
    } finally {
      setLoadingAccounts(false);
    }
  }, []);

  useEffect(() => {
    fetchAccounts();
  }, [fetchAccounts]);

  const handleOperationSuccess = (result, message) => {
    fetchAccounts();
    setSuccessToast(message || 'Banking transaction completed successfully!');
    setTimeout(() => setSuccessToast(null), 5000);
  };

  return (
    <div className="min-h-screen bg-[#f5f7fb] flex">
      {/* Sidebar */}
      <Sidebar mobileOpen={mobileOpen} setMobileOpen={setMobileOpen} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 lg:pl-64">
        <Navbar
          setMobileOpen={setMobileOpen}
          onOpenDeposit={() => setDepositOpen(true)}
          onOpenWithdraw={() => setWithdrawOpen(true)}
          onOpenTransfer={() => setTransferOpen(true)}
          onOpenCreateAccount={() => setCreateAccountOpen(true)}
        />

        {/* Global Toast */}
        {successToast && (
          <div className="mx-4 sm:mx-6 lg:mx-8 mt-4 animate-in slide-in-from-top-3 duration-200">
            <div className="bg-emerald-600 text-white px-4 py-2.5 rounded-xl shadow-md text-sm font-medium flex items-center justify-between">
              <span>✓ {successToast}</span>
              <button
                onClick={() => setSuccessToast(null)}
                className="text-white/80 hover:text-white ml-3 text-xs"
              >
                Dismiss
              </button>
            </div>
          </div>
        )}

        {/* Page Outlet */}
        <main className="flex-1 p-4 sm:p-6 xl:p-8 max-w-[1600px] w-full mx-auto">
          <Outlet
            context={{
              accounts,
              loadingAccounts,
              refreshAccounts: fetchAccounts,
              openDeposit: () => setDepositOpen(true),
              openWithdraw: () => setWithdrawOpen(true),
              openTransfer: () => setTransferOpen(true),
              openCreateAccount: () => setCreateAccountOpen(true),
            }}
          />
        </main>
      </div>

      {/* Banking Modals */}
      <DepositModal
        isOpen={depositOpen}
        onClose={() => setDepositOpen(false)}
        accounts={accounts}
        onSuccess={(res) => handleOperationSuccess(res, 'Deposit executed successfully!')}
      />

      <WithdrawModal
        isOpen={withdrawOpen}
        onClose={() => setWithdrawOpen(false)}
        accounts={accounts}
        onSuccess={(res) => handleOperationSuccess(res, 'Withdrawal executed successfully!')}
      />

      <TransferModal
        isOpen={transferOpen}
        onClose={() => setTransferOpen(false)}
        accounts={accounts}
        onSuccess={(res) => handleOperationSuccess(res, 'Transfer completed successfully!')}
      />

      <CreateAccountModal
        isOpen={createAccountOpen}
        onClose={() => setCreateAccountOpen(false)}
        onSuccess={(res) => handleOperationSuccess(res, 'Bank account created successfully!')}
      />
    </div>
  );
};

export default AppLayout;
