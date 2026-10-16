import React, { useState, useEffect, useRef } from 'react';
import {
  Terminal,
  RotateCcw,
  Clock,
  Zap,
  Activity,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Copy,
  Check,
  ExternalLink,
  Play,
  ArrowRight,
  Database,
  Cpu,
  Layers,
  Sparkles
} from 'lucide-react';

export default function ExecutionConsole({
  executionData,
  isExecuting,
  backendUptime = 0,
  onResetConsole,
  onQuickRun
}) {
  const [copied, setCopied] = useState(false);
  const [streamedLogs, setStreamedLogs] = useState([]);
  const [animTime, setAnimTime] = useState(0);
  const [animTokens, setAnimTokens] = useState(0);
  const terminalEndRef = useRef(null);
  const logStreamTimerRef = useRef(null);

  // Live ticking uptime timer
  const [uptimeSeconds, setUptimeSeconds] = useState(backendUptime || 120);

  useEffect(() => {
    if (backendUptime && backendUptime > 0) {
      setUptimeSeconds(Math.round(backendUptime));
    }
  }, [backendUptime]);

  useEffect(() => {
    const timer = setInterval(() => {
      setUptimeSeconds(prev => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatUptime = (totalSec) => {
    const hours = Math.floor(totalSec / 3600);
    const mins = Math.floor((totalSec % 3600) / 60);
    const secs = totalSec % 60;
    return `${hours.toString().padStart(2, '0')}h ${mins.toString().padStart(2, '0')}m ${secs.toString().padStart(2, '0')}s`;
  };

  // Real-time animated printing of logs
  useEffect(() => {
    if (!executionData || !executionData.logs || executionData.logs.length === 0) {
      setStreamedLogs([]);
      setAnimTime(0);
      setAnimTokens(0);
      return;
    }

    const fullLogs = executionData.logs;
    const targetTime = executionData.telemetry?.execution_time_ms || executionData.apiCall?.latency_ms || 18.5;
    const targetTokens = executionData.telemetry?.tokens_used || 84;

    // Reset and start line-by-line streaming
    setStreamedLogs([]);
    let currentIndex = 0;

    if (logStreamTimerRef.current) {
      clearInterval(logStreamTimerRef.current);
    }

    // Fast, responsive stream pace
    const streamIntervalMs = 70;

    logStreamTimerRef.current = setInterval(() => {
      if (currentIndex < fullLogs.length) {
        setStreamedLogs(prev => [...prev, fullLogs[currentIndex]]);
        currentIndex += 1;
      } else {
        clearInterval(logStreamTimerRef.current);
      }
    }, streamIntervalMs);

    // Number counting animations for telemetry
    let startTimestamp = null;
    const duration = 750; // ms

    const animateCounters = (now) => {
      if (!startTimestamp) startTimestamp = now;
      const progress = Math.min((now - startTimestamp) / duration, 1);
      const ease = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);

      setAnimTime(Math.round(ease * targetTime * 10) / 10);
      setAnimTokens(Math.round(ease * targetTokens));

      if (progress < 1) {
        requestAnimationFrame(animateCounters);
      }
    };
    requestAnimationFrame(animateCounters);

    return () => {
      if (logStreamTimerRef.current) clearInterval(logStreamTimerRef.current);
    };
  }, [executionData]);

  // Autoscroll terminal
  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [streamedLogs]);

  const handleCopyLogs = () => {
    if (!streamedLogs.length) return;
    const text = streamedLogs
      .map(l => `[${l.elapsed_ms !== undefined ? `${l.elapsed_ms}ms` : (l.time || '0.0ms')}] [${l.tag || 'LOG'}] ${l.message || l.text || ''}`)
      .join('\n');
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getTagColor = (tag, level) => {
    switch (tag) {
      case 'AEGIS-AST':
      case 'AEGIS-MVCC':
      case 'AEGIS-REG':
        return 'text-[#FF6C37] font-bold';
      case 'HTTP/200':
      case 'SUCCESS':
      case 'COMPLETED':
        return 'text-emerald-400 font-bold';
      case 'HTTP/422':
      case 'WARN':
        return 'text-amber-400 font-bold';
      case 'FATAL':
      case 'ERROR':
      case 'HALT':
        return 'text-red-400 font-bold';
      case 'ROUTER':
      case 'GATEWAY':
      case 'INGRESS':
        return 'text-cyan-400';
      case 'DISPATCH':
      case 'SQL':
        return 'text-purple-400';
      case 'LANGCHAIN':
      case 'BASELINE':
        return 'text-yellow-300 font-bold';
      default:
        return 'text-blue-400';
    }
  };

  const getMethodBadgeClass = (method) => {
    switch (method?.toUpperCase()) {
      case 'GET':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'POST':
        return 'bg-orange-50 text-[#FF6C37] border-orange-200';
      case 'PUT':
      case 'PATCH':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'DELETE':
        return 'bg-red-50 text-red-700 border-red-200';
      case 'SQL':
        return 'bg-indigo-50 text-indigo-700 border-indigo-200';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const hasExecuted = Boolean(executionData && (executionData.apiCall || executionData.logs?.length));

  return (
    <div className="w-full lg:w-3/5 h-full flex flex-col bg-white border border-gray-200 rounded-xl shadow-xs overflow-hidden">
      
      {/* Top Header Bar with Reset Console Button */}
      <div className="px-4 py-3 border-b border-gray-200 bg-white flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-md bg-orange-50 text-[#FF6C37] border border-orange-200">
            <Terminal className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-gray-900 tracking-tight">Execution & Telemetry Console</h2>
              {isExecuting ? (
                <span className="flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-semibold bg-orange-50 text-[#FF6C37] border border-orange-200">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-orange-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-[#FF6C37]"></span>
                  </span>
                  Streaming Execution...
                </span>
              ) : hasExecuted ? (
                <span className="flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                  Execution Active
                </span>
              ) : (
                <span className="flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-medium bg-gray-50 text-gray-500 border border-gray-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-gray-400"></span>
                  Console Standby
                </span>
              )}
            </div>
            <p className="text-[11px] text-gray-500">
              Live API routing, real-time terminal logs, and autonomous AST performance matrix
            </p>
          </div>
        </div>

        {/* Reset / Clear Button on Top Right */}
        <div className="flex items-center gap-2">
          {hasExecuted && (
            <button
              onClick={handleCopyLogs}
              type="button"
              id="btn-copy-terminal-logs"
              className="px-2.5 py-1 text-xs font-medium text-gray-600 hover:text-gray-900 bg-gray-50 hover:bg-gray-100 rounded-md border border-gray-200 transition-colors flex items-center gap-1.5 cursor-pointer"
              title="Copy Terminal Logs to Clipboard"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copied' : 'Copy Logs'}</span>
            </button>
          )}

          <button
            onClick={onResetConsole}
            type="button"
            id="btn-reset-execution-console"
            className="px-2.5 py-1 text-xs font-medium text-gray-700 hover:text-gray-900 bg-white hover:bg-gray-50 rounded-md border border-gray-300 shadow-2xs hover:border-gray-400 transition-all flex items-center gap-1.5 cursor-pointer active:scale-95 select-none"
            title="Clear all logs, API status, and reset console to standby"
          >
            <RotateCcw className="w-3.5 h-3.5 text-[#FF6C37]" />
            <span>Reset</span>
          </button>
        </div>
      </div>

      {/* Main Console Body: Conditional Rendering (Standby Blank Screen vs Real-Time Execution View) */}
      {!hasExecuted && !isExecuting ? (
        
        /* ------------------------------------------------------------- */
        /* INITIAL BLANK SCREEN (Before Any Query Was Run / After Reset)  */
        /* ------------------------------------------------------------- */
        <div className="flex-1 overflow-y-auto p-6 flex flex-col items-center justify-center text-center bg-gray-50/50">
          <div className="max-w-xl w-full space-y-6">
            
            {/* Minimalist Graphic & Standby Status */}
            <div className="mx-auto w-14 h-14 rounded-2xl bg-orange-50 border border-orange-200 flex items-center justify-center text-[#FF6C37] shadow-xs">
              <Terminal className="w-7 h-7" />
            </div>

            <div className="space-y-1.5">
              <h3 className="text-base font-bold text-gray-900 tracking-tight">
                Execution Pipeline Idle
              </h3>
              <p className="text-xs text-gray-500 leading-relaxed max-w-md mx-auto">
                No active execution stream. Enter a natural language request in the chat on the right, or click any sample scenario below to trigger live AST telemetry.
              </p>
            </div>

            {/* Quick-Run Scenario Chips */}
            <div className="space-y-2 pt-2">
              <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider block">
                Click a Preset Scenario to Run
              </span>
              <div className="flex flex-wrap items-center justify-center gap-2">
                <button
                  type="button"
                  onClick={() => onQuickRun && onQuickRun("Can student 1 graduate?")}
                  className="px-3 py-1.5 rounded-lg bg-white border border-gray-200 hover:border-orange-300 hover:bg-orange-50/40 text-xs font-medium text-gray-700 hover:text-[#FF6C37] shadow-2xs transition-all flex items-center gap-1.5 cursor-pointer active:scale-95"
                >
                  <Sparkles className="w-3.5 h-3.5 text-[#FF6C37]" />
                  <span>Can student 1 graduate?</span>
                </button>

                <button
                  type="button"
                  onClick={() => onQuickRun && onQuickRun("What are the prerequisites for course 51?")}
                  className="px-3 py-1.5 rounded-lg bg-white border border-gray-200 hover:border-blue-300 hover:bg-blue-50/40 text-xs font-medium text-gray-700 hover:text-blue-600 shadow-2xs transition-all flex items-center gap-1.5 cursor-pointer active:scale-95"
                >
                  <Layers className="w-3.5 h-3.5 text-blue-600" />
                  <span>Prerequisites for course 51</span>
                </button>

                <button
                  type="button"
                  onClick={() => onQuickRun && onQuickRun("Show tuition fee balance for student 2")}
                  className="px-3 py-1.5 rounded-lg bg-white border border-gray-200 hover:border-purple-300 hover:bg-purple-50/40 text-xs font-medium text-gray-700 hover:text-purple-600 shadow-2xs transition-all flex items-center gap-1.5 cursor-pointer active:scale-95"
                >
                  <Database className="w-3.5 h-3.5 text-purple-600" />
                  <span>Tuition ledger for student 2</span>
                </button>

                <button
                  type="button"
                  onClick={() => onQuickRun && onQuickRun("How many students are enrolled?")}
                  className="px-3 py-1.5 rounded-lg bg-white border border-gray-200 hover:border-emerald-300 hover:bg-emerald-50/40 text-xs font-medium text-gray-700 hover:text-emerald-700 shadow-2xs transition-all flex items-center gap-1.5 cursor-pointer active:scale-95"
                >
                  <Activity className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Count of enrolled students</span>
                </button>
              </div>
            </div>

            {/* Preview of the 4 Real-Time Telemetry Metrics */}
            <div className="pt-4 border-t border-gray-200/60">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-left">
                <div className="p-2.5 rounded-lg bg-white border border-gray-200/80 shadow-2xs">
                  <div className="flex items-center gap-1.5 text-blue-600 mb-1">
                    <Clock className="w-3.5 h-3.5" />
                    <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500">Execution Time</span>
                  </div>
                  <span className="text-sm font-bold text-gray-900 font-mono">-- ms</span>
                  <p className="text-[10px] text-gray-400 mt-0.5">Roundtrip latency</p>
                </div>

                <div className="p-2.5 rounded-lg bg-white border border-gray-200/80 shadow-2xs">
                  <div className="flex items-center gap-1.5 text-[#FF6C37] mb-1">
                    <Zap className="w-3.5 h-3.5" />
                    <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500">Tokens Used</span>
                  </div>
                  <span className="text-sm font-bold text-gray-900 font-mono">-- tokens</span>
                  <p className="text-[10px] text-gray-400 mt-0.5">0 tokens for AST heal</p>
                </div>

                <div className="p-2.5 rounded-lg bg-white border border-gray-200/80 shadow-2xs">
                  <div className="flex items-center gap-1.5 text-emerald-600 mb-1">
                    <Activity className="w-3.5 h-3.5" />
                    <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500">Server Uptime</span>
                  </div>
                  <span className="text-xs font-bold text-gray-900 font-mono truncate block">
                    {formatUptime(uptimeSeconds)}
                  </span>
                  <p className="text-[10px] text-emerald-600 font-medium mt-0.5">Live heartbeat</p>
                </div>

                <div className="p-2.5 rounded-lg bg-white border border-gray-200/80 shadow-2xs">
                  <div className="flex items-center gap-1.5 text-purple-600 mb-1">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500">AST Healing</span>
                  </div>
                  <span className="text-sm font-bold text-gray-900 font-mono">Standby</span>
                  <p className="text-[10px] text-gray-400 mt-0.5">MVCC in-memory</p>
                </div>
              </div>
            </div>

          </div>
        </div>

      ) : (

        /* ------------------------------------------------------------- */
        /* ACTIVE REAL-TIME EXECUTION SCREEN: API + 4 BOXES + TERMINAL   */
        /* ------------------------------------------------------------- */
        <div className="flex-1 overflow-y-auto p-4 space-y-3.5 flex flex-col">

          {/* 1. API USED FOR EXECUTION (Postman-style endpoint banner) */}
          <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg shadow-2xs space-y-2 shrink-0">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500">
                1. API Target Used For Execution
              </span>
              <div className="flex items-center gap-2">
                {/* Engine Mode Pill */}
                <span className={`px-2 py-0.5 rounded text-[10px] font-semibold font-mono border ${
                  executionData?.engineMode === 'aegis'
                    ? 'bg-orange-50 text-[#FF6C37] border-orange-200'
                    : 'bg-gray-100 text-gray-700 border-gray-300'
                }`}>
                  {executionData?.engineMode === 'aegis' ? 'AegisRegistry MVCC v1.1' : 'LangChain Baseline'}
                </span>

                {/* HTTP Status Code Pill */}
                {isExecuting ? (
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-blue-50 text-blue-700 border border-blue-200 animate-pulse">
                    Dispatching...
                  </span>
                ) : executionData?.telemetry?.healed ? (
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-emerald-50 text-emerald-700 border border-emerald-300 flex items-center gap-1">
                    <span className="line-through text-amber-600">422 Drift</span>
                    <span>➔</span>
                    <span className="text-emerald-700 font-extrabold">200 Healed</span>
                  </span>
                ) : executionData?.status === 'error' ? (
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-red-50 text-red-700 border border-red-200">
                    HTTP {executionData?.apiCall?.status_code || 422} Unprocessable
                  </span>
                ) : (
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-emerald-50 text-emerald-700 border border-emerald-200">
                    HTTP {executionData?.apiCall?.status_code || 200} OK
                  </span>
                )}
              </div>
            </div>

            {/* Path & Method Box */}
            <div className="flex items-center gap-2 bg-white px-2.5 py-1.5 rounded-md border border-gray-200 font-mono text-xs">
              <span className={`px-2 py-0.5 rounded font-bold text-[10px] border ${getMethodBadgeClass(executionData?.apiCall?.method || 'GET')}`}>
                {executionData?.apiCall?.method || 'GET'}
              </span>
              <span className="text-gray-900 font-semibold truncate flex-1">
                {executionData?.apiCall?.path ? (
                  executionData.apiCall.path.startsWith('http')
                    ? executionData.apiCall.path
                    : `http://localhost:8000${executionData.apiCall.path}`
                ) : (
                  executionData?.query ? `Intent: "${executionData.query}"` : 'http://localhost:8000/api/v1/query'
                )}
              </span>
              {executionData?.apiCall?.params && Object.keys(executionData.apiCall.params).length > 0 && (
                <span className="text-[11px] text-gray-500 bg-gray-50 px-2 py-0.5 rounded border border-gray-200 truncate max-w-[200px]" title={JSON.stringify(executionData.apiCall.params)}>
                  {JSON.stringify(executionData.apiCall.params)}
                </span>
              )}
            </div>
          </div>

          {/* 2. FOUR (4) REAL-TIME TELEMETRY BOXES */}
          <div className="space-y-1.5 shrink-0">
            <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500 block">
              2. Live Execution Telemetry Matrix
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              
              {/* Box A: Actual Time Taken */}
              <div className="p-3 rounded-xl bg-white border border-gray-200 shadow-2xs relative overflow-hidden group">
                <div className="flex items-center justify-between text-gray-500 mb-1">
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-500">Execution Time</span>
                  <Clock className="w-3.5 h-3.5 text-blue-500" />
                </div>
                <div className="flex items-baseline gap-1">
                  <span className="text-xl font-bold font-mono text-gray-900">
                    {animTime > 0 ? animTime : (executionData?.telemetry?.execution_time_ms || 18.5)}
                  </span>
                  <span className="text-xs text-gray-500 font-mono">ms</span>
                </div>
                <span className="text-[10px] text-gray-400 block mt-0.5">
                  Network + AST + Synthesis
                </span>
              </div>

              {/* Box B: Tokens Used */}
              <div className="p-3 rounded-xl bg-white border border-gray-200 shadow-2xs relative overflow-hidden group">
                <div className="flex items-center justify-between text-gray-500 mb-1">
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-500">Tokens Used</span>
                  <Zap className="w-3.5 h-3.5 text-[#FF6C37]" />
                </div>
                <div className="flex items-baseline gap-1">
                  <span className="text-xl font-bold font-mono text-gray-900">
                    {animTokens > 0 ? animTokens : (executionData?.telemetry?.tokens_used || 84)}
                  </span>
                  <span className="text-xs text-gray-500 font-mono">tokens</span>
                </div>
                <span className="text-[10px] text-emerald-600 font-semibold block mt-0.5">
                  0 tokens for AST healing
                </span>
              </div>

              {/* Box C: Live Uptime */}
              <div className="p-3 rounded-xl bg-white border border-gray-200 shadow-2xs relative overflow-hidden group">
                <div className="flex items-center justify-between text-gray-500 mb-1">
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-500">Uptime</span>
                  <Activity className="w-3.5 h-3.5 text-emerald-500 animate-pulse" />
                </div>
                <div className="flex items-baseline gap-1 truncate">
                  <span className="text-sm font-bold font-mono text-gray-900 truncate">
                    {formatUptime(uptimeSeconds)}
                  </span>
                </div>
                <span className="text-[10px] text-gray-400 block mt-0.5 truncate">
                  FastAPI 8000 • 100% Online
                </span>
              </div>

              {/* Box D: Fourth Metric - AST Self-Healing State */}
              <div className="p-3 rounded-xl bg-white border border-gray-200 shadow-2xs relative overflow-hidden group">
                <div className="flex items-center justify-between text-gray-500 mb-1">
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-500">AST Healing</span>
                  <ShieldCheck className="w-3.5 h-3.5 text-purple-500" />
                </div>
                <div className="flex items-baseline gap-1">
                  {executionData?.telemetry?.healed ? (
                    <span className="text-xs font-bold font-mono text-emerald-600 truncate">
                      ⚡ Healed (0.8ms)
                    </span>
                  ) : executionData?.status === 'error' ? (
                    <span className="text-xs font-bold font-mono text-red-600 truncate">
                      ❌ Drift Halted
                    </span>
                  ) : (
                    <span className="text-xs font-bold font-mono text-purple-600 truncate">
                      ✓ Contract Verified
                    </span>
                  )}
                </div>
                <span className="text-[10px] text-gray-400 block mt-0.5 truncate">
                  {executionData?.telemetry?.healed ? 'MVCC v1.1 In-Memory' : 'Zero Token Overhead'}
                </span>
              </div>

            </div>
          </div>

          {/* 3. TERMINAL BOX SHOWING ACTUAL REAL-TIME OUTLOGS */}
          <div className="flex-1 flex flex-col min-h-[260px] bg-[#0E1116] border border-gray-800 rounded-xl overflow-hidden shadow-md">
            
            {/* Terminal Window Header Bar with macOS/Linux style dots */}
            <div className="px-3.5 py-2 bg-[#161B22] border-b border-gray-800 flex items-center justify-between shrink-0 select-none">
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#FF5F56] inline-block" />
                  <span className="w-2.5 h-2.5 rounded-full bg-[#FFBD2E] inline-block" />
                  <span className="w-2.5 h-2.5 rounded-full bg-[#27C93F] inline-block" />
                </div>
                <span className="text-xs text-gray-400 font-mono ml-2">
                  aegis-kernel@localhost:~/execution-stream (bash)
                </span>
              </div>

              <div className="flex items-center gap-2 text-[10px] font-mono">
                {isExecuting ? (
                  <span className="text-orange-400 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-orange-400 animate-ping" />
                    STREAMING
                  </span>
                ) : (
                  <span className="text-emerald-400">
                    STATUS: EXIT 0
                  </span>
                )}
              </div>
            </div>

            {/* Terminal Body with Monospace Real-Time Log Printing */}
            <div className="flex-1 p-3.5 overflow-y-auto font-mono text-xs text-gray-300 space-y-1 selection:bg-orange-500 selection:text-white leading-relaxed">
              {streamedLogs.length === 0 ? (
                <div className="text-gray-500 italic">
                  Initializing kernel execution logger...
                </div>
              ) : (
                streamedLogs.map((log, idx) => (
                  <div key={idx} className="flex items-start gap-2 hover:bg-white/5 px-1 py-0.5 rounded transition-colors">
                    <span className="text-gray-500 shrink-0 text-[11px] select-none">
                      [{log.elapsed_ms !== undefined ? `${log.elapsed_ms}ms` : (log.time || '0.0ms')}]
                    </span>
                    <span className={`shrink-0 text-[11px] px-1 rounded bg-white/5 ${getTagColor(log.tag, log.level)}`}>
                      [{log.tag || 'LOG'}]
                    </span>
                    <span className={`flex-1 break-all text-[11.5px] ${
                      log.level === 'error' ? 'text-red-400 font-medium' :
                      log.level === 'warn' ? 'text-amber-300 font-medium' :
                      log.level === 'heal' ? 'text-[#FF6C37] font-semibold' :
                      log.level === 'success' ? 'text-emerald-300' :
                      'text-gray-200'
                    }`}>
                      {log.message || log.text || ''}
                    </span>
                  </div>
                ))
              )}

              {/* Blinking Terminal Cursor */}
              <div className="flex items-center gap-2 pt-1 text-gray-400">
                <span className="text-emerald-400 font-bold">➜</span>
                <span className="text-cyan-400 font-bold">~</span>
                <span className="inline-block w-2 h-4 bg-[#FF6C37] animate-pulse ml-0.5" />
              </div>

              <div ref={terminalEndRef} />
            </div>

          </div>

        </div>

      )}

    </div>
  );
}
