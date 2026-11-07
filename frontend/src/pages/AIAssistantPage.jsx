import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Sparkles,
  Send,
  Bot,
  User,
  TrendingDown,
  ShieldAlert,
  AlertCircle,
  PieChart,
  Lightbulb,
  ChevronRight,
  Info,
  Clock,
} from 'lucide-react';
import aiService from '../services/aiService';
import { formatPaiseToINR, formatDate } from '../utils/formatters';
import Button from '../components/common/Button';
import Badge from '../components/common/Badge';
import Alert from '../components/common/Alert';
import EmptyState from '../components/common/EmptyState';

const INITIAL_MESSAGES = [
  {
    id: 1,
    sender: 'assistant',
    text: "Hello! I am your AI Financial Assistant powered by Gemini and financial heuristics. I can summarize your monthly cash flow, analyze spending patterns, and provide personalized savings strategies based on your ledger activity. How can I assist you today?",
    timestamp: 'Just now',
    fallback: false,
  },
];

const createChatMessage = (sender, text, fallback = false) => ({
  id: `${Date.now()}-${Math.random()}`,
  sender,
  text,
  fallback,
  timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
});

export const AIAssistantPage = () => {
  const [activeTab, setActiveTab] = useState('chat'); // 'chat' | 'summary' | 'spending' | 'savings'

  // Chat State
  const [messages, setMessages] = useState(INITIAL_MESSAGES);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState(null);
  const chatBottomRef = useRef(null);

  // Financial Summary State
  const [summaryData, setSummaryData] = useState(null);
  const [summaryMonth, setSummaryMonth] = useState('');
  const [loadingSummary, setLoadingSummary] = useState(false);

  // Spending Analysis State
  const [spendingData, setSpendingData] = useState(null);
  const [spendingDays, setSpendingDays] = useState(30);
  const [loadingSpending, setLoadingSpending] = useState(false);

  // Savings Suggestions State
  const [savingsData, setSavingsData] = useState(null);
  const [loadingSavings, setLoadingSavings] = useState(false);

  // Provider Info
  const [providerInfo, setProviderInfo] = useState(null);

  const loadSummary = useCallback(async (month = null) => {
    try {
      setLoadingSummary(true);
      const res = await aiService.getFinancialSummary(month || null);
      setSummaryData(res);
    } catch (err) {
      console.error('Failed to load summary:', err);
    } finally {
      setLoadingSummary(false);
    }
  }, []);

  const loadSpending = useCallback(async (days) => {
    try {
      setLoadingSpending(true);
      const res = await aiService.getSpendingAnalysis(days);
      setSpendingData(res);
    } catch (err) {
      console.error('Failed to load spending analysis:', err);
    } finally {
      setLoadingSpending(false);
    }
  }, []);

  const loadSavings = useCallback(async () => {
    try {
      setLoadingSavings(true);
      const res = await aiService.getSavingsSuggestions();
      setSavingsData(res);
    } catch (err) {
      console.error('Failed to load savings suggestions:', err);
    } finally {
      setLoadingSavings(false);
    }
  }, []);

  useEffect(() => {
    // Fetch provider info on load
    aiService.getProviderInfo().then((res) => setProviderInfo(res)).catch(() => {});
  }, []);

  // Scroll to bottom of chat
  useEffect(() => {
    if (activeTab === 'chat') {
      chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, activeTab]);

  // Handle Tab Switch Data Fetching
  useEffect(() => {
    if (activeTab === 'summary' && !summaryData) {
      loadSummary();
    } else if (activeTab === 'spending' && !spendingData) {
      loadSpending(spendingDays);
    } else if (activeTab === 'savings' && !savingsData) {
      loadSavings();
    }
  }, [activeTab, summaryData, spendingData, spendingDays, savingsData, loadSummary, loadSpending, loadSavings]);

  const handleSendMessage = async (customText = null) => {
    const textToSend = customText || chatInput;
    if (!textToSend.trim() || chatLoading) return;

    const userMsg = createChatMessage('user', textToSend.trim());

    setMessages((prev) => [...prev, userMsg]);
    if (!customText) setChatInput('');
    setChatLoading(true);
    setChatError(null);

    try {
      const res = await aiService.sendChatMessage({ message: textToSend.trim() });
      const replyText = res.data?.reply || res.data?.response || res.reply || res.response || 'I was unable to generate a response.';
      const isFallback = res.data?.is_fallback || res.data?.fallback || res.is_fallback || false;
      const assistantMsg = createChatMessage('assistant', replyText, isFallback);
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      console.error('Chat error:', err);
      setChatError(err.message || 'Failed to communicate with AI Assistant.');
    } finally {
      setChatLoading(false);
    }
  };

  const promptSuggestions = [
    'How much did I spend this month?',
    'What are my largest transactions?',
    'Show my monthly financial summary',
    'How can I improve my savings rate?',
  ];

  // Normalized tab data accessors (supports both nested data and direct properties)
  const summaryMetrics =
    summaryData?.data?.metrics ||
    summaryData?.metrics ||
    summaryData?.data?.current_month ||
    summaryData?.current_month;

  const summaryContent =
    summaryData?.data?.summary ||
    summaryData?.summary;

  const summaryObservations =
    summaryContent?.key_observations ||
    summaryData?.data?.observations ||
    summaryData?.observations ||
    [];

  const spendingMetrics =
    spendingData?.data?.metrics ||
    spendingData?.metrics ||
    spendingData?.data ||
    spendingData;

  const spendingAnalysis =
    spendingData?.data?.analysis ||
    spendingData?.analysis;

  const spendingOutliers =
    spendingMetrics?.outliers ||
    spendingData?.data?.high_spending_transactions ||
    spendingData?.high_spending_transactions ||
    [];

  const savingsMetrics =
    savingsData?.data?.metrics ||
    savingsData?.metrics ||
    savingsData?.data ||
    savingsData;

  const savingsSuggestions =
    savingsData?.data?.suggestions ||
    savingsData?.suggestions;

  const savingsRecs =
    savingsSuggestions?.practical_recommendations ||
    savingsData?.data?.recommendations ||
    savingsData?.recommendations ||
    [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
              AI Financial Assistant
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-indigo-100 text-indigo-800 flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-indigo-600" />
              {providerInfo?.model ? `${providerInfo.model} Active` : (providerInfo?.provider === 'gemini' ? 'Gemini Active' : 'Hybrid AI Core')}
            </span>
          </div>
          <p className="text-sm text-slate-500">
            Intelligent insights, spending behavior diagnostics, and conversational finance.
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 overflow-x-auto">
        <button
          onClick={() => setActiveTab('chat')}
          className={`flex items-center gap-2 py-3 px-5 border-b-2 font-medium text-sm whitespace-nowrap transition-all ${
            activeTab === 'chat'
              ? 'border-brand-600 text-brand-600'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <Bot className="w-4 h-4" />
          Conversational Advisory
        </button>
        <button
          onClick={() => setActiveTab('summary')}
          className={`flex items-center gap-2 py-3 px-5 border-b-2 font-medium text-sm whitespace-nowrap transition-all ${
            activeTab === 'summary'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <PieChart className="w-4 h-4" />
          Monthly Financial Summary
        </button>
        <button
          onClick={() => setActiveTab('spending')}
          className={`flex items-center gap-2 py-3 px-5 border-b-2 font-medium text-sm whitespace-nowrap transition-all ${
            activeTab === 'spending'
              ? 'border-rose-600 text-rose-600'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <TrendingDown className="w-4 h-4" />
          Spending Pattern Analysis
        </button>
        <button
          onClick={() => setActiveTab('savings')}
          className={`flex items-center gap-2 py-3 px-5 border-b-2 font-medium text-sm whitespace-nowrap transition-all ${
            activeTab === 'savings'
              ? 'border-emerald-600 text-emerald-600'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <Lightbulb className="w-4 h-4" />
          Smart Savings Suggestions
        </button>
      </div>

      {/* TAB 1: Conversational Advisory */}
      {activeTab === 'chat' && (
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm flex flex-col h-[650px] overflow-hidden">
          {/* Safety Guardrail Notice */}
          <div className="p-3 bg-slate-50 border-b border-slate-100 flex items-center justify-between text-xs text-slate-600">
            <div className="flex items-center gap-2">
              <Info className="w-4 h-4 text-brand-600 flex-shrink-0" />
              <span>
                <strong>Guardrail Active:</strong> This assistant provides analytical guidance only. Money transfers and balance mutations cannot be triggered via chat.
              </span>
            </div>
          </div>

          {/* Messages Scroll Area */}
          <div className="flex-1 p-6 overflow-y-auto space-y-4">
            {messages.map((msg) => {
              const isAssistant = msg.sender === 'assistant';
              return (
                <div
                  key={msg.id}
                  className={`flex items-start gap-3 ${
                    isAssistant ? 'justify-start' : 'justify-end'
                  }`}
                >
                  {isAssistant && (
                    <div className="w-8 h-8 rounded-xl bg-brand-600 text-white flex items-center justify-center flex-shrink-0 shadow-sm">
                      <Bot className="w-4 h-4" />
                    </div>
                  )}

                  <div
                    className={`max-w-xl rounded-2xl p-4 text-sm leading-relaxed ${
                      isAssistant
                        ? 'bg-slate-100/80 text-slate-800 border border-slate-200/50'
                        : 'bg-brand-600 text-white shadow-sm'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{msg.text}</p>
                    {isAssistant && msg.fallback && (
                      <div className="mt-2.5 pt-2 border-t border-slate-200 text-[11px] text-amber-700 flex items-center gap-1 font-medium">
                        <AlertCircle className="w-3.5 h-3.5" />
                        Generated using deterministic banking heuristics (LLM fallback)
                      </div>
                    )}
                    <span
                      className={`block text-[10px] mt-1.5 ${
                        isAssistant ? 'text-slate-400' : 'text-brand-200 text-right'
                      }`}
                    >
                      {formatDate(msg.timestamp)}
                    </span>
                  </div>

                  {!isAssistant && (
                    <div className="w-8 h-8 rounded-xl bg-slate-800 text-white flex items-center justify-center flex-shrink-0 shadow-sm">
                      <User className="w-4 h-4" />
                    </div>
                  )}
                </div>
              );
            })}

            {chatLoading && (
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-xl bg-brand-600 text-white flex items-center justify-center flex-shrink-0 shadow-sm">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="bg-slate-100 rounded-2xl p-4 text-xs text-slate-500 flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-brand-600 animate-bounce" />
                  <div className="w-2 h-2 rounded-full bg-brand-600 animate-bounce [animation-delay:0.2s]" />
                  <div className="w-2 h-2 rounded-full bg-brand-600 animate-bounce [animation-delay:0.4s]" />
                  <span className="ml-1 font-medium">Analyzing ledger transactions...</span>
                </div>
              </div>
            )}

            {chatError && (
              <Alert variant="error" title="Assistant Error">
                {chatError}
              </Alert>
            )}

            <div ref={chatBottomRef} />
          </div>

          {/* Quick Prompt Chips */}
          <div className="px-6 py-2.5 bg-slate-50 border-t border-slate-100 flex items-center gap-2 overflow-x-auto">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex-shrink-0">
              Suggestions:
            </span>
            {promptSuggestions.map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => handleSendMessage(prompt)}
                disabled={chatLoading}
                className="text-xs px-3 py-1.5 rounded-full bg-white border border-slate-200 text-slate-600 hover:text-brand-600 hover:border-brand-300 hover:bg-brand-50/50 whitespace-nowrap transition-colors shadow-2xs font-medium"
              >
                {prompt}
              </button>
            ))}
          </div>

          {/* Message Input Box */}
          <div className="p-4 bg-white border-t border-slate-200 flex items-center gap-3">
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder="Ask a question about your accounts, expenses, or savings..."
              disabled={chatLoading}
              className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
            <Button
              variant="primary"
              size="md"
              icon={Send}
              loading={chatLoading}
              onClick={() => handleSendMessage()}
              disabled={!chatInput.trim()}
            >
              Send
            </Button>
          </div>
        </div>
      )}

      {/* TAB 2: Monthly Financial Summary */}
      {activeTab === 'summary' && (
        <div className="space-y-6">
          {/* Controls */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-base font-semibold text-slate-900">Monthly Accounting Statement</h2>
              <p className="text-xs text-slate-500">Summary of inflows, outflows, and net delta</p>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="month"
                value={summaryMonth}
                onChange={(e) => {
                  setSummaryMonth(e.target.value);
                  loadSummary(e.target.value);
                }}
                className="text-xs font-semibold rounded-lg border-slate-200 bg-slate-50 py-1.5 px-3 text-slate-700 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
              <Button
                size="sm"
                variant="outline"
                loading={loadingSummary}
                onClick={() => loadSummary(summaryMonth)}
              >
                Refresh
              </Button>
            </div>
          </div>

          {loadingSummary ? (
            <div className="p-12 text-center text-sm text-slate-500">
              <Clock className="w-8 h-8 animate-spin mx-auto text-brand-600 mb-2" />
              Compiling monthly overview...
            </div>
          ) : !summaryMetrics ? (
            <EmptyState
              title="No summary data available"
              description="Make some transactions to generate monthly analytical statements."
            />
          ) : (
            <div className="space-y-6">
              {/* Top Metric Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm space-y-1">
                  <span className="text-xs font-semibold text-slate-500 uppercase">Total Inflows</span>
                  <div className="text-xl font-bold text-emerald-600">
                    {formatPaiseToINR(summaryMetrics.total_deposits_paise || (summaryMetrics.total_deposits_inr * 100) || 0)}
                  </div>
                  <span className="text-[11px] text-slate-400">
                    {summaryMetrics.deposit_count || 0} deposits
                  </span>
                </div>
                <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm space-y-1">
                  <span className="text-xs font-semibold text-slate-500 uppercase">Withdrawals</span>
                  <div className="text-xl font-bold text-rose-600">
                    {formatPaiseToINR(summaryMetrics.total_withdrawals_paise || (summaryMetrics.total_withdrawals_inr * 100) || 0)}
                  </div>
                  <span className="text-[11px] text-slate-400">
                    {summaryMetrics.withdrawal_count || 0} withdrawals
                  </span>
                </div>
                <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm space-y-1">
                  <span className="text-xs font-semibold text-slate-500 uppercase">Transfers Sent</span>
                  <div className="text-xl font-bold text-indigo-600">
                    {formatPaiseToINR(summaryMetrics.total_transfers_paise || (summaryMetrics.total_transfers_inr * 100) || 0)}
                  </div>
                  <span className="text-[11px] text-slate-400">
                    {summaryMetrics.transfer_count || 0} transfers
                  </span>
                </div>
                <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm space-y-1">
                  <span className="text-xs font-semibold text-slate-500 uppercase">Net Monthly Delta</span>
                  <div className="text-xl font-bold text-slate-900">
                    {formatPaiseToINR(summaryMetrics.net_cash_flow_paise || (summaryMetrics.net_cash_flow_inr * 100) || 0)}
                  </div>
                  <Badge variant={summaryContent?.cash_flow_health || summaryMetrics.cash_flow_health || 'BALANCED'} size="sm">
                    {summaryContent?.cash_flow_health || summaryMetrics.cash_flow_health || 'BALANCED'}
                  </Badge>
                </div>
              </div>

              {/* Executive Overview & Observations */}
              <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm space-y-4">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-brand-600" />
                  <h3 className="font-semibold text-base text-slate-900">
                    Executive Analysis & Observations
                  </h3>
                </div>
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 text-sm text-slate-700 leading-relaxed">
                  {summaryContent?.overview || summaryData?.data?.executive_overview || 'Monthly ledger activity successfully compiled.'}
                </div>

                {summaryObservations.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="text-xs font-semibold text-slate-600 uppercase tracking-wider">
                      Key Financial Indicators
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {summaryObservations.map((obs, i) => (
                        <div
                          key={i}
                          className="p-3 rounded-xl bg-slate-50/70 border border-slate-100 text-xs text-slate-700 flex items-start gap-2.5"
                        >
                          <ChevronRight className="w-4 h-4 text-brand-600 flex-shrink-0 mt-0.5" />
                          <span>{obs}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: Spending Pattern Analysis */}
      {activeTab === 'spending' && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-base font-semibold text-slate-900">Spending Diagnostics</h2>
              <p className="text-xs text-slate-500">Identify outlier expenses and velocity</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 font-medium">Window:</span>
              {[30, 60, 90].map((d) => (
                <button
                  key={d}
                  onClick={() => {
                    setSpendingDays(d);
                    loadSpending(d);
                  }}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                    spendingDays === d
                      ? 'border-brand-600 bg-brand-50 text-brand-700'
                      : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300'
                  }`}
                >
                  {d} Days
                </button>
              ))}
            </div>
          </div>

          {loadingSpending ? (
            <div className="p-12 text-center text-sm text-slate-500">
              <Clock className="w-8 h-8 animate-spin mx-auto text-brand-600 mb-2" />
              Analyzing transaction velocity...
            </div>
          ) : !spendingMetrics ? (
            <EmptyState
              title="No spending data in this window"
              description="There are no outgoing debit or transfer transactions within this timeframe."
            />
          ) : (
            <div className="space-y-6">
              {/* Velocity Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm space-y-1">
                  <span className="text-xs font-semibold text-slate-500 uppercase">Total Outflows</span>
                  <div className="text-xl font-bold text-rose-600">
                    {formatPaiseToINR(spendingMetrics.total_spent_paise || (spendingMetrics.total_outflow_inr * 100) || 0)}
                  </div>
                  <span className="text-[11px] text-slate-400">
                    {spendingMetrics.transaction_count || 0} debit transactions
                  </span>
                </div>
                <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm space-y-1">
                  <span className="text-xs font-semibold text-slate-500 uppercase">Daily Burn Velocity</span>
                  <div className="text-xl font-bold text-slate-900">
                    {formatPaiseToINR(spendingMetrics.daily_spending_velocity_paise || (spendingMetrics.daily_velocity_inr * 100) || 0)}
                  </div>
                  <span className="text-[11px] text-slate-400">Per day average</span>
                </div>
                <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm space-y-1">
                  <span className="text-xs font-semibold text-slate-500 uppercase">Peak Outflow Day</span>
                  <div className="text-lg font-bold text-slate-900">
                    {spendingMetrics.peak_day?.date || spendingMetrics.peak_day || 'N/A'}
                  </div>
                  <span className="text-[11px] text-rose-600 font-medium">
                    Highest disbursement volume
                  </span>
                </div>
              </div>

              {/* AI Pattern Observation */}
              {spendingAnalysis?.spending_pattern_summary && (
                <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm space-y-2">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-brand-600" />
                    <h3 className="font-semibold text-sm text-slate-900">AI Pattern Observation</h3>
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    {spendingAnalysis.spending_pattern_summary}
                  </p>
                </div>
              )}

              {/* High Spending Outliers (>2.5x avg) */}
              <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-base text-slate-900">
                      High-Value Spending Outliers (&gt;2.5x Mean)
                    </h3>
                    <p className="text-xs text-slate-500">
                      Individual debits and transfers significantly exceeding your standard volume.
                    </p>
                  </div>
                  <Badge variant="SUSPICIOUS" size="sm">
                    {spendingOutliers.length} Outliers
                  </Badge>
                </div>

                {spendingOutliers.length === 0 ? (
                  <p className="text-xs text-slate-500 py-4">
                    No outlier transactions detected; your disbursements have remained steady.
                  </p>
                ) : (
                  <div className="divide-y divide-slate-100">
                    {spendingOutliers.map((tx, idx) => (
                      <div
                        key={tx.transaction_id || idx}
                        className="py-3 flex items-center justify-between text-xs"
                      >
                        <div>
                          <span className="font-semibold text-slate-900 block">
                            {tx.description || tx.type || 'Outflow Transaction'}
                          </span>
                          <span className="text-slate-400 font-mono">
                            {tx.date || formatDate(tx.timestamp)} {tx.transaction_id ? `• ID: ${tx.transaction_id?.slice(-8)}` : ''}
                          </span>
                        </div>
                        <div className="text-right">
                          <span className="font-bold text-sm text-rose-600">
                            {formatPaiseToINR(tx.amount_paise || (tx.amount_inr * 100) || 0)}
                          </span>
                          <Badge variant={tx.risk_level || 'NORMAL'} size="sm" className="ml-2">
                            {tx.risk_level || 'NORMAL'}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 4: Smart Savings Suggestions */}
      {activeTab === 'savings' && (
        <div className="space-y-6">
          {loadingSavings ? (
            <div className="p-12 text-center text-sm text-slate-500">
              <Clock className="w-8 h-8 animate-spin mx-auto text-brand-600 mb-2" />
              Generating customized savings targets...
            </div>
          ) : !savingsMetrics ? (
            <EmptyState
              title="No savings analysis available"
              description="Sufficient transaction records are needed to compute runway targets."
            />
          ) : (
            <div className="space-y-6">
              {/* Emergency Fund Card */}
              <div className="bg-gradient-to-br from-indigo-900 via-brand-900 to-slate-900 rounded-2xl p-6 sm:p-8 text-white shadow-lg space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-brand-200 uppercase tracking-wider flex items-center gap-1.5">
                    <ShieldAlert className="w-4 h-4 text-emerald-400" />
                    Emergency Liquidity Reserve
                  </span>
                  <Badge variant={savingsSuggestions?.savings_health_rating || savingsMetrics.cash_flow_health || 'BALANCED'} size="sm">
                    {savingsSuggestions?.savings_health_rating || savingsMetrics.cash_flow_health || 'BALANCED'}
                  </Badge>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 pt-2">
                  <div>
                    <span className="text-xs text-slate-300 block">Target Emergency Fund (3 Mo)</span>
                    <span className="text-2xl font-bold text-white">
                      {formatPaiseToINR(savingsMetrics.target_emergency_fund_paise || (savingsMetrics.emergency_fund_target_inr * 100) || 0)}
                    </span>
                  </div>
                  <div>
                    <span className="text-xs text-slate-300 block">Recommended Monthly Savings</span>
                    <span className="text-2xl font-bold text-emerald-400">
                      {formatPaiseToINR(savingsMetrics.recommended_monthly_savings_paise || (savingsSuggestions?.recommended_monthly_savings_inr * 100) || 0)}
                    </span>
                  </div>
                  <div>
                    <span className="text-xs text-slate-300 block">Current Cash Runway</span>
                    <span className="text-2xl font-bold text-amber-300">
                      {(savingsMetrics.coverage_months !== undefined
                        ? savingsMetrics.coverage_months
                        : savingsMetrics.current_runway_months !== undefined
                        ? savingsMetrics.current_runway_months
                        : 0
                      ).toFixed(1)} Months
                    </span>
                  </div>
                </div>
              </div>

              {/* Recommendations List */}
              <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm space-y-4">
                <div className="flex items-center gap-2">
                  <Lightbulb className="w-5 h-5 text-amber-500" />
                  <h3 className="font-semibold text-base text-slate-900">
                    Actionable Savings Recommendations
                  </h3>
                </div>

                <div className="space-y-3">
                  {savingsRecs.map((rec, i) => (
                    <div
                      key={i}
                      className="p-4 rounded-xl bg-slate-50 border border-slate-100 flex items-start gap-3"
                    >
                      <div className="w-6 h-6 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-xs flex-shrink-0 mt-0.5">
                        {i + 1}
                      </div>
                      <p className="text-xs text-slate-700 leading-relaxed font-medium">{rec}</p>
                    </div>
                  ))}
                </div>

                {/* Disclaimer */}
                <div className="pt-4 border-t border-slate-100 text-[11px] text-slate-400 italic">
                  Disclaimer: Recommendations are simulated based on historical ledger velocity. This does not constitute certified financial or investment advisory.
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AIAssistantPage;
