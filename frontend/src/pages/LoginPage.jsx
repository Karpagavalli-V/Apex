import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Building2, ShieldCheck, Lock, User, ArrowUpRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import Button from '../components/common/Button';
import Alert from '../components/common/Alert';

export const LoginPage = () => {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || '/dashboard';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await login(identifier.trim(), password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(err.message || 'Invalid username or password. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f5f7fb] lg:grid lg:grid-cols-2">
      <aside className="relative hidden min-h-screen overflow-hidden bg-gradient-to-br from-[#101d36] via-[#172b4d] to-[#1d3670] p-12 text-white lg:flex lg:flex-col lg:justify-between xl:p-16">
        <div className="absolute inset-0 opacity-[0.08]" aria-hidden="true">
          <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.2)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.2)_1px,transparent_1px)] bg-[size:36px_36px]" />
        </div>
        <div className="absolute -right-32 top-1/4 h-96 w-96 rounded-full bg-brand-400/20 blur-3xl" />
        <div className="relative flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-400 to-brand-700 shadow-lg shadow-brand-950/30 ring-1 ring-white/15">
            <Building2 className="h-5 w-5" />
          </div>
          <div>
            <p className="font-bold tracking-tight">Apex Bank</p>
            <p className="text-xs text-blue-100/60">Private banking</p>
          </div>
        </div>

        <div className="relative max-w-xl py-16">
          <h1 className="text-4xl font-bold leading-tight tracking-tight xl:text-5xl">
            Your finances, thoughtfully in sync.
          </h1>
          <p className="mt-5 max-w-lg text-base leading-relaxed text-blue-100/70">
            Stay on top of your accounts, move money with confidence, and make informed decisions with a little help from AI.
          </p>

          <div className="mt-10 grid gap-3 sm:grid-cols-2">
            <div className="rounded-2xl border border-white/10 bg-white/[0.07] p-4 backdrop-blur-sm">
              <ShieldCheck className="mb-3 h-5 w-5 text-emerald-300" />
              <p className="text-sm font-semibold">Protected by design</p>
              <p className="mt-1 text-xs leading-relaxed text-blue-100/60">Security checks help safeguard every session.</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/[0.07] p-4 backdrop-blur-sm">
              <ArrowUpRight className="mb-3 h-5 w-5 text-blue-200" />
              <p className="text-sm font-semibold">Your money in motion</p>
              <p className="mt-1 text-xs leading-relaxed text-blue-100/60">See balances and transactions together.</p>
            </div>
          </div>
        </div>
        <p className="relative text-xs text-blue-100/45">Banking made personal. Built around you.</p>
      </aside>

      <main className="flex min-h-screen items-center justify-center px-4 py-10 sm:px-8 lg:px-10">
        <div className="w-full max-w-[440px]">
          <div className="mb-8 text-center lg:text-left">
            <div className="mb-5 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-600 text-white shadow-lg shadow-brand-500/25 lg:hidden">
              <Building2 className="h-6 w-6" />
            </div>
            <p className="mb-2 text-xs font-bold uppercase tracking-[0.16em] text-brand-700">Welcome to Apex</p>
            <h2 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-[28px]">Sign in to your account</h2>
            <p className="mt-2 text-sm text-slate-500">Enter your details to securely continue.</p>
          </div>

          <div className="rounded-3xl border border-slate-200/80 bg-white p-6 shadow-[0_20px_60px_-28px_rgba(15,23,42,0.22)] sm:p-8">
          {error && <Alert variant="error" className="mb-5">{error}</Alert>}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="login-identifier" className="mb-2 block text-sm font-semibold text-slate-700">
                Username or Email
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400">
                  <User className="w-4 h-4" />
                </span>
                <input
                  id="login-identifier"
                  type="text"
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  placeholder="Enter username or email"
                  autoComplete="username"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50/60 py-3 pl-10 pr-3 text-sm text-slate-900 transition placeholder:text-slate-400 focus:border-brand-400 focus:bg-white focus:outline-none focus:ring-4 focus:ring-brand-500/10"
                  required
                />
              </div>
            </div>

            <div>
              <label htmlFor="login-password" className="mb-2 block text-sm font-semibold text-slate-700">
                Password
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400">
                  <Lock className="w-4 h-4" />
                </span>
                <input
                  id="login-password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  autoComplete="current-password"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50/60 py-3 pl-10 pr-3 text-sm font-medium text-slate-900 transition placeholder:text-slate-400 focus:border-brand-400 focus:bg-white focus:outline-none focus:ring-4 focus:ring-brand-500/10"
                  required
                />
              </div>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              loading={loading}
              className="mt-1 w-full rounded-xl py-3"
            >
              Sign In to Account
            </Button>
          </form>

          <div className="mt-5 text-center text-xs text-slate-500">
            Don't have an account yet?{' '}
            <Link to="/register" className="font-semibold text-brand-700 hover:text-brand-800">
              Register as Customer
            </Link>
          </div>

          </div>
          <div className="mt-6 flex items-center justify-center gap-2 text-xs text-slate-500">
          <ShieldCheck className="w-4 h-4 text-emerald-500" />
          <span>Your sign-in is protected with secure authentication.</span>
          </div>
        </div>
      </main>
    </div>
  );
};

export default LoginPage;
