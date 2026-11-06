import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Building2, User, Mail, Lock, Check, X, ShieldCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import Button from '../components/common/Button';
import Alert from '../components/common/Alert';

export const RegisterPage = () => {
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    username: '',
    password: '',
    confirm_password: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  // Password rules validation
  const pwd = formData.password;
  const rules = {
    length: pwd.length >= 8,
    upper: /[A-Z]/.test(pwd),
    lower: /[a-z]/.test(pwd),
    number: /[0-9]/.test(pwd),
    special: /[@$!%*?&#]/.test(pwd),
    match: pwd && pwd === formData.confirm_password,
  };
  const usernameIsValid = /^[a-zA-Z0-9_-]{3,30}$/.test(formData.username.trim());

  const isFormValid =
    formData.full_name.trim() &&
    formData.email.trim() &&
    usernameIsValid &&
    rules.length &&
    rules.upper &&
    rules.lower &&
    rules.number &&
    rules.special &&
    rules.match;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!rules.match) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    try {
      await register({
        full_name: formData.full_name.trim(),
        email: formData.email.trim(),
        username: formData.username.trim(),
        password: formData.password,
      });
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setError(
        err.details?.length
          ? err.details.join('. ')
          : err.message || 'Registration failed. Please check inputs and try again.'
      );
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
            Create an account to see your finances clearly, manage day-to-day banking, and get helpful AI-powered insights.
          </p>
          <div className="mt-10 rounded-2xl border border-white/10 bg-white/[0.07] p-5 backdrop-blur-sm">
            <ShieldCheck className="mb-3 h-5 w-5 text-emerald-300" />
            <p className="text-sm font-semibold">A secure start, every step of the way</p>
            <p className="mt-1 text-xs leading-relaxed text-blue-100/60">Your information is protected with secure authentication and account safeguards.</p>
          </div>
        </div>
        <p className="relative text-xs text-blue-100/45">Banking made personal. Built around you.</p>
      </aside>

      <main className="flex min-h-screen items-center justify-center px-4 py-8 sm:px-8 lg:px-10">
        <div className="w-full max-w-[480px]">
          <div className="mb-6 text-center lg:text-left">
            <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-600 text-white shadow-lg shadow-brand-500/25 lg:hidden">
              <Building2 className="h-6 w-6" />
            </div>
            <p className="mb-1 text-xs font-bold uppercase tracking-[0.16em] text-brand-700">Get started</p>
            <h2 className="text-2xl font-bold tracking-tight text-slate-900">Open a customer account</h2>
            <p className="mt-2 text-sm text-slate-500">Join Apex Bank for thoughtful, AI-enhanced banking.</p>
          </div>

          <div className="rounded-3xl border border-slate-200/80 bg-white p-6 shadow-[0_20px_60px_-28px_rgba(15,23,42,0.22)] sm:p-8">
          {error && <Alert variant="error" className="mb-5">{error}</Alert>}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Full Legal Name
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400">
                  <User className="w-4 h-4" />
                </span>
                <input
                  type="text"
                  name="full_name"
                  value={formData.full_name}
                  onChange={handleChange}
                  placeholder="e.g. Eleanor Vance"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50/60 py-2.5 pl-10 pr-3 text-sm text-slate-900 transition focus:border-brand-400 focus:bg-white focus:outline-none focus:ring-4 focus:ring-brand-500/10"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Email Address
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400">
                  <Mail className="w-4 h-4" />
                </span>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="name@example.com"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50/60 py-2.5 pl-10 pr-3 text-sm text-slate-900 transition focus:border-brand-400 focus:bg-white focus:outline-none focus:ring-4 focus:ring-brand-500/10"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Username
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400">
                  <User className="w-4 h-4" />
                </span>
                <input
                  type="text"
                  name="username"
                  value={formData.username}
                  onChange={handleChange}
                  placeholder="choose_username"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50/60 py-2.5 pl-10 pr-3 text-sm text-slate-900 transition focus:border-brand-400 focus:bg-white focus:outline-none focus:ring-4 focus:ring-brand-500/10"
                  required
                />
              </div>
              <p className="mt-1 text-xs text-slate-500">
                Use 3-30 letters, numbers, underscores, or hyphens.
              </p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Password
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400">
                  <Lock className="w-4 h-4" />
                </span>
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="••••••••••••"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50/60 py-2.5 pl-10 pr-3 text-sm font-medium text-slate-900 transition focus:border-brand-400 focus:bg-white focus:outline-none focus:ring-4 focus:ring-brand-500/10"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Confirm Password
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400">
                  <Lock className="w-4 h-4" />
                </span>
                <input
                  type="password"
                  name="confirm_password"
                  value={formData.confirm_password}
                  onChange={handleChange}
                  placeholder="••••••••••••"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50/60 py-2.5 pl-10 pr-3 text-sm font-medium text-slate-900 transition focus:border-brand-400 focus:bg-white focus:outline-none focus:ring-4 focus:ring-brand-500/10"
                  required
                />
              </div>
            </div>

            {/* Password Validation Hints */}
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-[11px] space-y-1 text-slate-600">
              <div className="font-semibold text-slate-700 mb-1">Security Requirements:</div>
              <div className="grid grid-cols-2 gap-1">
                <div className={`flex items-center gap-1 ${rules.length ? 'text-emerald-600 font-medium' : 'text-slate-400'}`}>
                  {rules.length ? <Check className="w-3 h-3" /> : <X className="w-3 h-3" />}
                  <span>8+ characters</span>
                </div>
                <div className={`flex items-center gap-1 ${rules.upper ? 'text-emerald-600 font-medium' : 'text-slate-400'}`}>
                  {rules.upper ? <Check className="w-3 h-3" /> : <X className="w-3 h-3" />}
                  <span>Uppercase letter</span>
                </div>
                <div className={`flex items-center gap-1 ${rules.lower ? 'text-emerald-600 font-medium' : 'text-slate-400'}`}>
                  {rules.lower ? <Check className="w-3 h-3" /> : <X className="w-3 h-3" />}
                  <span>Lowercase letter</span>
                </div>
                <div className={`flex items-center gap-1 ${rules.number ? 'text-emerald-600 font-medium' : 'text-slate-400'}`}>
                  {rules.number ? <Check className="w-3 h-3" /> : <X className="w-3 h-3" />}
                  <span>1+ Number</span>
                </div>
                <div className={`flex items-center gap-1 ${rules.special ? 'text-emerald-600 font-medium' : 'text-slate-400'}`}>
                  {rules.special ? <Check className="w-3 h-3" /> : <X className="w-3 h-3" />}
                  <span>Special char (@$!%*?&#)</span>
                </div>
                <div className={`flex items-center gap-1 ${rules.match && pwd ? 'text-emerald-600 font-medium' : 'text-slate-400'}`}>
                  {rules.match && pwd ? <Check className="w-3 h-3" /> : <X className="w-3 h-3" />}
                  <span>Passwords match</span>
                </div>
              </div>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              disabled={!isFormValid}
              loading={loading}
              className="mt-1 w-full rounded-xl py-3"
            >
              Complete Registration
            </Button>
          </form>

          <div className="mt-5 text-center text-xs text-slate-500">
            Already registered?{' '}
            <Link to="/login" className="font-semibold text-brand-700 hover:text-brand-800">
              Sign In Instead
            </Link>
          </div>
          </div>
          <div className="mt-5 flex items-center justify-center gap-2 text-xs text-slate-500">
            <ShieldCheck className="h-4 w-4 text-emerald-500" />
            <span>Your information is protected with secure authentication.</span>
          </div>
        </div>
      </main>
    </div>
  );
};

export default RegisterPage;
