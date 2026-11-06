/**
 * Formatting utilities for Indian Rupee currency, dates, and account numbers.
 */

export const formatINR = (amount) => {
  const numeric = Number(amount) || 0;
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(numeric);
};

export const formatPaiseToINR = (paise) => {
  const numericPaise = Number(paise) || 0;
  return formatINR(numericPaise / 100);
};

export const formatDate = (dateString, includeTime = true) => {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return dateString;

  const options = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    ...(includeTime && { hour: '2-digit', minute: '2-digit' }),
  };

  return new Intl.DateTimeFormat('en-IN', options).format(date);
};

export const maskAccountNumber = (accountNumber) => {
  if (!accountNumber) return '••••';
  const str = String(accountNumber);
  if (str.length <= 6) return str;
  return `${str.slice(0, 3)}••••${str.slice(-4)}`;
};
