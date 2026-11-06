import React, { useEffect, useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import {
  ArrowDownLeft,
  ArrowRight,
  ArrowUpRight,
  ArrowUpRightFromCircle,
  Building2,
  ChevronLeft,
  ChevronRight,
  CircleHelp,
  CreditCard,
  Eye,
  Menu,
  Pause,
  Play,
  Repeat,
  ShieldCheck,
  Sparkles,
  Wallet,
  X,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const slides = [
  {
    eyebrow: 'A MORE HUMAN WAY TO BANK',
    title: <>Your money.<br />Your next move.</>,
    description: 'Everyday banking that feels clear, calm, and ready for whatever comes next.',
    action: 'Explore your banking',
    tone: 'mint',
    tag: 'A clearer view of your finances',
    visualTitle: 'A little more in sync',
    visualNote: 'Your everyday money, all together.',
    visualIcon: Wallet,
    metric: 'One clear picture',
    cardLabel: 'YOUR APEX ACCOUNT',
  },
  {
    eyebrow: 'CONFIDENCE IN EVERY TRANSFER',
    title: <>Move money.<br />Keep your peace.</>,
    description: 'Simple deposits, withdrawals, and transfers—with helpful checks along the way.',
    action: 'See how it works',
    tone: 'blue',
    tag: 'Move money with clarity',
    visualTitle: 'A smoother way to send',
    visualNote: 'Review every detail before you go.',
    visualIcon: Repeat,
    metric: 'Clear at every step',
    cardLabel: 'MONEY, IN MOTION',
  },
  {
    eyebrow: 'A LITTLE HELP, RIGHT ON TIME',
    title: <>Meet your money<br />with fresh eyes.</>,
    description: 'Get a thoughtful view of your cash flow and practical insights from your AI financial assistant.',
    action: 'Meet your AI assistant',
    tone: 'violet',
    tag: 'Your finances, with perspective',
    visualTitle: 'Insight that feels useful',
    visualNote: 'Ask a question. Get a clearer view.',
    visualIcon: Sparkles,
    metric: 'A smarter perspective',
    cardLabel: 'YOUR AI MONEY COACH',
  },
];

const quickLinks = [
  { label: 'Accounts', detail: 'Keep your money in view', icon: Wallet },
  { label: 'Transfers', detail: 'Send with confidence', icon: Repeat },
  { label: 'Cards', detail: 'Everyday spending, simplified', icon: CreditCard },
  { label: 'AI money coach', detail: 'Insights that make sense', icon: Sparkles },
];

const productCards = [
  {
    index: '01',
    title: 'A better view of your money',
    description: 'See your accounts, balances, and recent activity together in one considered space.',
    icon: Eye,
    color: 'bg-[#e7f5ef] text-[#16775b]',
  },
  {
    index: '02',
    title: 'Everyday banking, made easier',
    description: 'Handle deposits, withdrawals, and transfers without the extra steps.',
    icon: ArrowUpRight,
    color: 'bg-[#eaf0ff] text-[#3159ba]',
  },
  {
    index: '03',
    title: 'A little intelligence goes a long way',
    description: 'Explore cash-flow summaries and helpful suggestions with your AI assistant.',
    icon: Sparkles,
    color: 'bg-[#f1eaff] text-[#7652ba]',
  },
];

function BrandMark({ light = false }) {
  return (
    <Link to="/" className="inline-flex items-center gap-3" aria-label="Apex Bank home">
      <span className="flex h-10 w-10 items-center justify-center rounded-[14px] bg-[#173b35] text-white shadow-sm">
        <Building2 className="h-[19px] w-[19px]" strokeWidth={1.8} />
      </span>
      <span className="leading-tight">
        <span className={`block text-[16px] font-bold tracking-[-0.04em] ${light ? 'text-white' : 'text-[#192b29]'}`}>
          apex<span className="font-medium">bank</span>
        </span>
        <span className={`mt-0.5 block text-[9px] font-semibold uppercase tracking-[0.18em] ${light ? 'text-white/55' : 'text-slate-400'}`}>
          Banking, reimagined
        </span>
      </span>
    </Link>
  );
}

function HeroArtwork({ slide, slideIndex }) {
  const ArtIcon = slide.visualIcon;

  return (
    <div className={`landing-art landing-art--${slide.tone} relative mx-auto flex aspect-[1/0.93] w-full max-w-[570px] items-center justify-center overflow-hidden rounded-[34px]`}>
      <div className="landing-art__grid absolute inset-0" aria-hidden="true" />
      <div className="landing-art__orb landing-float absolute h-[350px] w-[350px] rounded-full" aria-hidden="true" />
      <div className="landing-art__orbit absolute h-[390px] w-[390px] rounded-full border" aria-hidden="true" />
      <div className="landing-art__orbit landing-art__orbit--inner absolute h-[285px] w-[285px] rounded-full border" aria-hidden="true" />

      <div className="landing-float relative z-10 w-[min(74%,360px)] -rotate-[5deg] rounded-[26px] border border-white/80 bg-white/90 p-5 shadow-[0_35px_80px_-28px_rgba(16,54,49,0.42)] backdrop-blur-xl sm:p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-[14px] bg-[#e6f4ee] text-[#19765c]">
              <ArtIcon className="h-5 w-5" />
            </span>
            <div>
              <p className="text-[13px] font-bold text-[#1b302c]">{slide.visualTitle}</p>
              <p className="mt-1 text-[10px] text-slate-500">Apex digital banking</p>
            </div>
          </div>
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[#f3f6f4] text-slate-500">
            <ArrowUpRightFromCircle className="h-4 w-4" />
          </span>
        </div>

        <div className={`landing-art__card mt-5 overflow-hidden rounded-[20px] p-5 text-white sm:p-6`}>
          <div className="flex items-center justify-between">
            <span className="text-[9px] font-semibold uppercase tracking-[0.2em] text-white/65">{slide.cardLabel}</span>
            <span className="flex h-8 w-8 items-center justify-center rounded-full border border-white/20 bg-white/10">
              <Building2 className="h-4 w-4 text-white/85" />
            </span>
          </div>
          <div className="mt-7 flex items-end justify-between gap-3">
            <div>
              <p className="text-[10px] text-white/60">{slide.tag}</p>
              <p className="mt-2 text-[19px] font-semibold tracking-tight sm:text-[22px]">{slide.metric}</p>
            </div>
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-white/10">
              <ArtIcon className="h-5 w-5 text-white" />
            </div>
          </div>
          <div className="mt-5 h-px bg-white/15" />
          <div className="mt-3 flex items-center justify-between text-[10px] text-white/65">
            <span>{slide.visualNote}</span>
            <span className="flex items-center gap-1">
              <ShieldCheck className="h-3 w-3" />
              Protected
            </span>
          </div>
        </div>

        <div className="mt-4 flex items-center justify-between px-1">
          <span className="text-[10px] font-medium text-slate-400">Thoughtful tools for real life</span>
          <div className="flex -space-x-1.5" aria-hidden="true">
            <span className="h-5 w-5 rounded-full border-2 border-white bg-[#9bd9be]" />
            <span className="h-5 w-5 rounded-full border-2 border-white bg-[#aabcf3]" />
            <span className="h-5 w-5 rounded-full border-2 border-white bg-[#e9c39b]" />
          </div>
        </div>
      </div>

      <div className="landing-float landing-float--slow absolute bottom-[12%] left-[5%] z-20 hidden items-center gap-3 rounded-2xl border border-white/70 bg-white/90 px-4 py-3 shadow-xl shadow-slate-900/10 backdrop-blur-md sm:flex">
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#e8f5ee] text-[#16805c]">
          <ArrowDownLeft className="h-[18px] w-[18px]" />
        </span>
        <span>
          <span className="block text-[11px] font-semibold text-slate-800">Money, made clearer</span>
          <span className="mt-0.5 block text-[10px] text-slate-500">All your activity in one place</span>
        </span>
      </div>

      <div className="landing-float landing-float--reverse absolute right-[4%] top-[13%] z-20 hidden items-center gap-2 rounded-full border border-white/60 bg-white/85 px-3.5 py-2.5 text-[10px] font-semibold text-[#214d40] shadow-lg shadow-slate-900/10 backdrop-blur-md sm:flex">
        <span className="h-2 w-2 rounded-full bg-[#3ab48b] shadow-[0_0_0_4px_rgba(58,180,139,0.13)]" />
        A calmer kind of banking
      </div>
      <span className="sr-only">Illustration {slideIndex + 1} of 3</span>
    </div>
  );
}

export const HomePage = () => {
  const { isAuthenticated, loading } = useAuth();
  const [activeSlide, setActiveSlide] = useState(0);
  const [interactionPaused, setInteractionPaused] = useState(false);
  const [userPaused, setUserPaused] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const motionPreference = window.matchMedia('(prefers-reduced-motion: reduce)');
    const updateMotionPreference = () => setReducedMotion(motionPreference.matches);
    updateMotionPreference();
    motionPreference.addEventListener('change', updateMotionPreference);
    return () => motionPreference.removeEventListener('change', updateMotionPreference);
  }, []);

  useEffect(() => {
    if (interactionPaused || userPaused || reducedMotion) return undefined;
    const timer = window.setInterval(() => {
      setActiveSlide((current) => (current + 1) % slides.length);
    }, 6500);
    return () => window.clearInterval(timer);
  }, [interactionPaused, userPaused, reducedMotion]);

  useEffect(() => {
    if (!mobileMenuOpen) return undefined;
    const closeOnEscape = (event) => {
      if (event.key === 'Escape') setMobileMenuOpen(false);
    };
    window.addEventListener('keydown', closeOnEscape);
    return () => window.removeEventListener('keydown', closeOnEscape);
  }, [mobileMenuOpen]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#f7f8f5]">
        <span className="h-8 w-8 animate-spin rounded-full border-[3px] border-[#dce9e3] border-t-[#1b6651]" role="status" aria-label="Loading Apex Bank" />
      </div>
    );
  }

  if (isAuthenticated) return <Navigate to="/dashboard" replace />;

  const slide = slides[activeSlide];
  const showSlide = (index) => setActiveSlide((index + slides.length) % slides.length);

  return (
    <div className="min-h-screen overflow-hidden bg-[#fbfcfa] text-[#1c2927]">
      <div className="border-b border-[#e7ece8] bg-[#f2f6f2]">
        <div className="mx-auto flex max-w-[1320px] items-center justify-between px-5 py-2.5 text-[11px] sm:px-8 lg:px-12">
          <p className="flex items-center gap-2 font-medium text-[#52645e]">
            <ShieldCheck className="h-3.5 w-3.5 text-[#28826a]" />
            A little more clarity in your everyday banking.
          </p>
          <Link to="/login" className="hidden items-center gap-1 font-semibold text-[#26705b] transition hover:text-[#173b35] sm:inline-flex">
            Existing customer? Sign in <ArrowRight className="h-3 w-3" />
          </Link>
        </div>
      </div>

      <header className="sticky top-0 z-40 border-b border-[#e9eeeb]/80 bg-[#fbfcfa]/90 backdrop-blur-xl">
        <div className="mx-auto flex h-[76px] max-w-[1320px] items-center justify-between px-5 sm:px-8 lg:px-12">
          <BrandMark />

          <nav className="hidden items-center gap-8 md:flex" aria-label="Main navigation">
            <a href="#banking" className="text-[13px] font-medium text-slate-600 transition hover:text-[#1d6b55]">Everyday banking</a>
            <a href="#experience" className="text-[13px] font-medium text-slate-600 transition hover:text-[#1d6b55]">The Apex difference</a>
            <a href="#support" className="text-[13px] font-medium text-slate-600 transition hover:text-[#1d6b55]">Support</a>
          </nav>

          <div className="hidden items-center gap-3 md:flex">
            <Link to="/login" className="rounded-full px-4 py-2.5 text-[13px] font-semibold text-[#344741] transition hover:bg-[#f1f5f2]">Sign in</Link>
            <Link to="/register" className="inline-flex items-center gap-2 rounded-full bg-[#183e36] px-5 py-2.5 text-[13px] font-semibold text-white shadow-md shadow-[#183e36]/15 transition hover:-translate-y-0.5 hover:bg-[#245449]">
              Open an account <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          <button
            type="button"
            className="flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 text-slate-700 md:hidden"
            aria-label={mobileMenuOpen ? 'Close menu' : 'Open menu'}
            aria-expanded={mobileMenuOpen}
            onClick={() => setMobileMenuOpen((open) => !open)}
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
        {mobileMenuOpen && (
          <nav className="border-t border-slate-100 bg-[#fbfcfa] px-5 py-4 shadow-lg md:hidden" aria-label="Mobile navigation">
            <div className="mx-auto flex max-w-[1320px] flex-col gap-1">
              <a href="#banking" onClick={() => setMobileMenuOpen(false)} className="rounded-xl px-3 py-3 text-sm font-medium text-slate-700 hover:bg-slate-50">Everyday banking</a>
              <a href="#experience" onClick={() => setMobileMenuOpen(false)} className="rounded-xl px-3 py-3 text-sm font-medium text-slate-700 hover:bg-slate-50">The Apex difference</a>
              <a href="#support" onClick={() => setMobileMenuOpen(false)} className="rounded-xl px-3 py-3 text-sm font-medium text-slate-700 hover:bg-slate-50">Support</a>
              <div className="mt-2 grid grid-cols-2 gap-2 border-t border-slate-100 pt-4">
                <Link to="/login" className="rounded-xl border border-slate-200 px-4 py-3 text-center text-sm font-semibold text-slate-700">Sign in</Link>
                <Link to="/register" className="rounded-xl bg-[#183e36] px-4 py-3 text-center text-sm font-semibold text-white">Open an account</Link>
              </div>
            </div>
          </nav>
        )}
      </header>

      <main>
        <section
          className="landing-hero relative"
          aria-roledescription="carousel"
          aria-label="Apex banking highlights"
          onMouseEnter={() => setInteractionPaused(true)}
          onMouseLeave={() => setInteractionPaused(false)}
          onFocusCapture={() => setInteractionPaused(true)}
          onBlurCapture={(event) => {
            if (!event.currentTarget.contains(event.relatedTarget)) setInteractionPaused(false);
          }}
        >
          <div className="landing-hero__glow landing-hero__glow--one" aria-hidden="true" />
          <div className="landing-hero__glow landing-hero__glow--two" aria-hidden="true" />
          <div className="landing-hero__dots" aria-hidden="true" />
          <div className="relative mx-auto grid min-h-[620px] max-w-[1320px] items-center gap-8 px-5 py-10 sm:px-8 sm:py-14 lg:min-h-[650px] lg:grid-cols-[0.93fr_1.07fr] lg:gap-6 lg:px-12 lg:py-10">
            <div key={activeSlide} className="landing-copy relative z-10 max-w-[570px]">
              <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-[#dfe9e2] bg-white/80 px-3.5 py-2 text-[10px] font-bold tracking-[0.16em] text-[#39705d] shadow-sm shadow-slate-900/[0.03]">
                <span className="h-1.5 w-1.5 rounded-full bg-[#44aa83]" />
                {slide.eyebrow}
              </div>
              <h1 className="max-w-[620px] text-[42px] font-semibold leading-[1.06] tracking-[-0.055em] text-[#182b26] sm:text-[54px] lg:text-[64px]">
                {slide.title}
              </h1>
              <p className="mt-6 max-w-[490px] text-[15px] leading-7 text-[#65736d] sm:text-[16px]">
                {slide.description}
              </p>
              <div className="mt-8 flex flex-wrap items-center gap-3">
                <Link to="/register" className="group inline-flex items-center gap-3 rounded-full bg-[#183e36] px-6 py-3.5 text-[13px] font-semibold text-white shadow-lg shadow-[#183e36]/15 transition hover:-translate-y-0.5 hover:bg-[#245449]">
                  {slide.action}
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-white/15 transition group-hover:translate-x-0.5">
                    <ArrowRight className="h-3.5 w-3.5" />
                  </span>
                </Link>
                <a href="#banking" className="inline-flex items-center gap-2 rounded-full px-4 py-3 text-[13px] font-semibold text-[#49625a] transition hover:bg-white/70">
                  Take a look <ChevronRight className="h-4 w-4" />
                </a>
              </div>
              <div className="mt-9 flex items-center gap-2 text-[11px] text-[#7a8882]">
                <ShieldCheck className="h-4 w-4 text-[#38836b]" />
                Secure sign-in and helpful checks built into your banking.
              </div>
            </div>

            <div key={`art-${activeSlide}`} className="landing-art-wrap relative z-10 flex min-h-[320px] items-center justify-center lg:min-h-[500px]">
              <HeroArtwork slide={slide} slideIndex={activeSlide} />
            </div>
          </div>

          <div className="absolute inset-x-0 bottom-5 z-20 mx-auto flex max-w-[1320px] items-center justify-between px-5 sm:px-8 lg:bottom-7 lg:px-12">
            <div className="flex items-center gap-2.5" role="group" aria-label="Choose a banking highlight">
              {slides.map((item, index) => (
                <button
                  key={item.eyebrow}
                  type="button"
                  aria-label={`Show highlight ${index + 1}: ${item.eyebrow.toLowerCase()}`}
                  aria-current={activeSlide === index ? 'true' : undefined}
                  onClick={() => showSlide(index)}
                  className={`landing-dot ${activeSlide === index ? 'landing-dot--active' : ''}`}
                >
                  <span className="sr-only">{index + 1}</span>
                </button>
              ))}
              <span className="ml-2 hidden text-[10px] font-medium tracking-wide text-slate-400 sm:inline">
                0{activeSlide + 1} <span className="mx-1 text-slate-300">/</span> 0{slides.length}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                aria-label={userPaused ? 'Play automatic highlights' : 'Pause automatic highlights'}
                aria-pressed={userPaused}
                onClick={() => setUserPaused((paused) => !paused)}
                className="landing-control"
              >
                {userPaused ? <Play className="h-3.5 w-3.5" /> : <Pause className="h-3.5 w-3.5" />}
              </button>
              <button
                type="button"
                aria-label="Previous highlight"
                onClick={() => showSlide(activeSlide - 1)}
                className="landing-control"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <button
                type="button"
                aria-label="Next highlight"
                onClick={() => showSlide(activeSlide + 1)}
                className="landing-control"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </section>

        <section className="relative z-20 mx-auto -mt-2 max-w-[1230px] px-5 sm:px-8 lg:-mt-8 lg:px-12">
          <div className="grid overflow-hidden rounded-[24px] border border-[#e7ece8] bg-white shadow-[0_18px_48px_-30px_rgba(28,53,45,0.3)] sm:grid-cols-2 lg:grid-cols-4">
            {quickLinks.map((item, index) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.label}
                  to="/login"
                  className={`group flex items-center gap-3.5 px-5 py-5 transition hover:bg-[#f5f9f6] sm:px-6 lg:px-5 xl:px-7 ${index < quickLinks.length - 1 ? 'border-b border-[#edf0ed] sm:border-r lg:border-b-0' : ''} ${index === 0 || index === 2 ? 'sm:border-r lg:border-r' : ''}`}
                >
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[14px] bg-[#edf6f1] text-[#28745b] transition group-hover:scale-105 group-hover:bg-[#dff0e7]">
                    <Icon className="h-[18px] w-[18px]" />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block text-[13px] font-semibold text-[#293a34]">{item.label}</span>
                    <span className="mt-1 block text-[10px] leading-4 text-slate-500">{item.detail}</span>
                  </span>
                  <ArrowRight className="h-4 w-4 shrink-0 text-slate-300 transition group-hover:translate-x-1 group-hover:text-[#28745b]" />
                </Link>
              );
            })}
          </div>
        </section>

        <section id="banking" className="mx-auto max-w-[1320px] scroll-mt-24 px-5 pb-20 pt-24 sm:px-8 lg:px-12 lg:pb-28 lg:pt-32">
          <div className="flex flex-col justify-between gap-6 md:flex-row md:items-end">
            <div className="max-w-[600px]">
              <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#378069]">Banking that fits real life</p>
              <h2 className="mt-4 text-3xl font-semibold leading-tight tracking-[-0.045em] text-[#1b2d28] sm:text-[40px]">
                Less searching.<br className="hidden sm:block" /> More getting on with it.
              </h2>
            </div>
            <p className="max-w-[390px] text-sm leading-6 text-[#74817b]">
              The little things should feel simple. Apex brings your everyday banking and useful insights into one clear experience.
            </p>
          </div>

          <div className="mt-10 grid gap-4 md:grid-cols-3">
            {productCards.map((card, index) => {
              const Icon = card.icon;
              return (
                <Link
                  key={card.index}
                  to={index === 2 ? '/login' : '/login'}
                  className="group relative overflow-hidden rounded-[24px] border border-[#e8ede8] bg-white p-6 transition duration-300 hover:-translate-y-1 hover:border-[#d3e2d8] hover:shadow-[0_24px_50px_-32px_rgba(28,53,45,0.28)] sm:p-7"
                >
                  <div className="flex items-start justify-between">
                    <span className={`flex h-12 w-12 items-center justify-center rounded-[16px] ${card.color}`}>
                      <Icon className="h-5 w-5" />
                    </span>
                    <span className="text-[10px] font-semibold tracking-[0.16em] text-slate-300">{card.index}</span>
                  </div>
                  <h3 className="mt-8 text-[18px] font-semibold tracking-tight text-[#23352f]">{card.title}</h3>
                  <p className="mt-2.5 min-h-[48px] text-[13px] leading-6 text-[#738079]">{card.description}</p>
                  <span className="mt-6 inline-flex items-center gap-2 text-[12px] font-semibold text-[#28745b]">
                    Explore Apex <ArrowRight className="h-3.5 w-3.5 transition group-hover:translate-x-1" />
                  </span>
                  <span className="pointer-events-none absolute -bottom-16 -right-12 h-36 w-36 rounded-full border border-[#edf2ed] transition duration-500 group-hover:scale-125" />
                </Link>
              );
            })}
          </div>
        </section>

        <section id="experience" className="relative overflow-hidden bg-[#173b35]">
          <div className="landing-story__orb landing-float absolute -right-20 top-1/2 h-[440px] w-[440px] -translate-y-1/2 rounded-full" aria-hidden="true" />
          <div className="relative mx-auto grid max-w-[1320px] items-center gap-10 px-5 py-16 sm:px-8 lg:grid-cols-[1.1fr_0.9fr] lg:px-12 lg:py-24">
            <div className="max-w-[620px]">
              <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#9be0c1]">The Apex difference</p>
              <h2 className="mt-4 text-3xl font-semibold leading-tight tracking-[-0.045em] text-white sm:text-[42px]">
                Banking should leave you feeling more in control.
              </h2>
              <p className="mt-5 max-w-[510px] text-sm leading-7 text-white/65">
                From the first sign-in to the last transfer, we keep the important details easy to find and the next step easy to understand.
              </p>
              <Link to="/register" className="mt-8 inline-flex items-center gap-3 rounded-full bg-[#b9f1d4] px-5 py-3 text-[13px] font-semibold text-[#183b32] transition hover:-translate-y-0.5 hover:bg-white">
                Get started with Apex <ArrowRight className="h-4 w-4" />
              </Link>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-[22px] border border-white/10 bg-white/[0.07] p-5 backdrop-blur-sm sm:translate-y-6">
                <span className="flex h-10 w-10 items-center justify-center rounded-[14px] bg-white/10 text-[#a8e8c9]"><ShieldCheck className="h-5 w-5" /></span>
                <h3 className="mt-5 text-sm font-semibold text-white">Thoughtful protection</h3>
                <p className="mt-2 text-xs leading-5 text-white/55">Useful checks and a clear record help you stay informed about account activity.</p>
              </div>
              <div className="rounded-[22px] border border-white/10 bg-white/[0.07] p-5 backdrop-blur-sm">
                <span className="flex h-10 w-10 items-center justify-center rounded-[14px] bg-white/10 text-[#a8e8c9]"><Sparkles className="h-5 w-5" /></span>
                <h3 className="mt-5 text-sm font-semibold text-white">A smarter perspective</h3>
                <p className="mt-2 text-xs leading-5 text-white/55">Turn your financial activity into helpful summaries and practical insights.</p>
              </div>
            </div>
          </div>
        </section>

        <section id="support" className="mx-auto flex max-w-[1320px] flex-col gap-6 px-5 py-12 sm:px-8 md:flex-row md:items-center md:justify-between lg:px-12">
          <div className="flex items-start gap-4">
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-[15px] bg-[#edf5f0] text-[#28745b]"><CircleHelp className="h-5 w-5" /></span>
            <div>
              <h2 className="text-sm font-semibold text-[#293b35]">Need a hand getting started?</h2>
              <p className="mt-1 text-xs leading-5 text-slate-500">Sign in or create your account to find your way around.</p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link to="/login" className="rounded-full border border-[#dfe7e1] px-4 py-2.5 text-xs font-semibold text-[#3c534a] transition hover:bg-white">Sign in</Link>
            <Link to="/register" className="inline-flex items-center gap-2 rounded-full bg-[#183e36] px-4 py-2.5 text-xs font-semibold text-white transition hover:bg-[#245449]">Create an account <ArrowRight className="h-3.5 w-3.5" /></Link>
          </div>
        </section>
      </main>

      <footer className="border-t border-[#e8ede9] bg-white">
        <div className="mx-auto flex max-w-[1320px] flex-col gap-5 px-5 py-7 sm:px-8 md:flex-row md:items-center md:justify-between lg:px-12">
          <BrandMark />
          <p className="text-[10px] leading-5 text-slate-400">Apex Bank is a demonstration banking experience. Features and availability depend on your account.</p>
          <div className="flex gap-5 text-[11px] font-medium text-slate-500">
            <Link to="/login" className="transition hover:text-[#28745b]">Sign in</Link>
            <Link to="/register" className="transition hover:text-[#28745b]">Create account</Link>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default HomePage;
