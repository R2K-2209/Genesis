import React, { useState, useEffect } from 'react';
import {
  Database,
  Server,
  Cpu,
  Layers,
  ArrowRight,
  ShieldCheck,
  Zap,
  Activity,
  Code2,
  CheckCircle2,
  Table,
  Play,
  Send,
  ExternalLink,
  GraduationCap,
  Sparkles,
  GitBranch,
  BookOpen,
  DollarSign,
  Bot
} from 'lucide-react';
import DatabaseModal from './components/DatabaseModal';
import ApiExplorerModal from './components/ApiExplorerModal';
import ChatbotPanel from './components/ChatbotPanel';
import { fetchHealth, fetchDatabaseOverview, fetchApiCatalog } from './services/api';

export default function App() {
  const [isDbModalOpen, setIsDbModalOpen] = useState(false);
  const [isApiModalOpen, setIsApiModalOpen] = useState(false);
  const [selectedEndpointId, setSelectedEndpointId] = useState(null);
  const [serverStatus, setServerStatus] = useState('checking');
  const [dbOverview, setDbOverview] = useState(null);
  const [apiCatalog, setApiCatalog] = useState(null);
  const [testStudent, setTestStudent] = useState(null);
  const [loadingTest, setLoadingTest] = useState(false);

  const openApiExplorer = (endpointId = null) => {
    setSelectedEndpointId(endpointId);
    setIsApiModalOpen(true);
  };

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const health = await fetchHealth();
        setServerStatus('online');
        const [overview, catalog] = await Promise.all([
          fetchDatabaseOverview(),
          fetchApiCatalog().catch(() => null)
        ]);
        setDbOverview(overview);
        setApiCatalog(catalog);
      } catch (err) {
        setServerStatus('offline');
      }
    };
    checkBackend();
    const interval = setInterval(checkBackend, 10000);
    return () => clearInterval(interval);
  }, []);

  const runSampleApiQuery = async (studentId = 1) => {
    try {
      setLoadingTest(true);
      const res = await fetch(`http://localhost:8000/api/v1/students/${studentId}/graduation-eligibility`);
      const data = await res.json();
      setTestStudent(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingTest(false);
    }
  };

  return (
    <div className="h-screen w-screen overflow-hidden bg-[#F9FAFB] text-gray-900 flex flex-col font-sans selection:bg-orange-500 selection:text-white">
      
      {/* Postman-Style White Top Navigation Bar */}
      <header className="h-14 shrink-0 bg-white border-b border-gray-200 px-6 flex items-center justify-between shadow-xs z-30">
        
        {/* Brand & Title */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-[#FF6C37] flex items-center justify-center text-white shadow-sm font-bold text-lg">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-base font-bold text-gray-900 tracking-tight">AegisRegistry</span>
              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-orange-50 text-[#FF6C37] border border-orange-200 font-mono">
                PS 01
              </span>
            </div>
            <p className="text-[11px] text-gray-500">
              Autonomous Self-Healing Tool Interface Under API Schema Drift
            </p>
          </div>
        </div>

        {/* Center: System Status Indicators */}
        <div className="hidden md:flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1 rounded-md bg-gray-50 border border-gray-200 text-xs">
            <span className={`w-2 h-2 rounded-full ${serverStatus === 'online' ? 'bg-emerald-500' : 'bg-red-500'}`} />
            <span className="text-gray-500">FastAPI:</span>
            <span className={`font-semibold ${serverStatus === 'online' ? 'text-emerald-600' : 'text-red-600'}`}>
              {serverStatus === 'online' ? 'Online (8000)' : 'Offline'}
            </span>
          </div>

          <div className="flex items-center gap-2 px-3 py-1 rounded-md bg-gray-50 border border-gray-200 text-xs">
            <Database className="w-3.5 h-3.5 text-[#FF6C37]" />
            <span className="text-gray-500">Database:</span>
            <span className="text-gray-800 font-medium">SQLite 3 (university.db)</span>
          </div>

          <div className="flex items-center gap-2 px-3 py-1 rounded-md bg-gray-50 border border-gray-200 text-xs">
            <Cpu className="w-3.5 h-3.5 text-orange-600" />
            <span className="text-gray-500">Agent:</span>
            <span className="text-gray-800 font-medium">Aegis Agent (Groq / SQLite)</span>
          </div>
        </div>

        {/* Right Top Corner Buttons: API Explorer + Database State */}
        <div className="flex items-center gap-2.5">
          <button
            id="btn-api-explorer"
            type="button"
            onClick={() => openApiExplorer(null)}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold bg-white hover:bg-gray-100 active:bg-gray-200 text-gray-800 border border-gray-300 shadow-2xs transition-all cursor-pointer hover:border-gray-400 active:scale-95 select-none"
            title="Open API Catalog & Live Runner (15 Endpoints)"
          >
            <Code2 className="w-4 h-4 text-[#FF6C37]" />
            <span className="font-semibold text-gray-800">API Explorer</span>
            <span className="px-1.5 py-0.2 rounded bg-orange-100 text-[#FF6C37] font-mono text-[10px] font-bold">
              15 APIs
            </span>
          </button>

          <button
            id="btn-database-state-inspector"
            type="button"
            onClick={() => setIsDbModalOpen(true)}
            className="group relative flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold bg-[#FF6C37] hover:bg-[#E85B27] active:bg-[#D44C1A] text-white shadow-sm transition-all hover:shadow cursor-pointer active:scale-95 select-none"
            title="Inspect 30 University Database Tables"
          >
            <Database className="w-4 h-4 text-white" />
            <div className="text-left">
              <span className="leading-tight block font-bold">Database State</span>
            </div>
            <span className="px-1.5 py-0.2 rounded bg-white/20 text-white font-mono text-[10px] ml-0.5">
              {dbOverview ? `${dbOverview.total_tables} Tbls` : '30 Tbls'}
            </span>
          </button>
        </div>

      </header>

      {/* Main Content Area: Split 3/5 Left vs 2/5 Right, strict viewport fit */}
      <main className="flex-1 overflow-hidden p-4 max-w-[1700px] mx-auto w-full">
        <div className="h-full flex flex-col lg:flex-row gap-4 items-stretch">
          
          {/* LEFT 3/5 COLUMN: Scrollable System Overview, APIs, and Live Testbed */}
          <div className="w-full lg:w-3/5 h-full overflow-y-auto pr-2 space-y-4">
            
            {/* Hero Card */}
            <div className="relative overflow-hidden rounded-xl border border-gray-200 bg-white p-5 shadow-xs">
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-[#FF6C37] text-xs font-bold uppercase tracking-wider">
                  <Zap className="w-4 h-4" />
                  Live University API Testbed & Aegis Agent
                </div>
                <h1 className="text-xl sm:text-2xl font-extrabold text-gray-900 tracking-tight">
                  Autonomous Tool Interface & Natural Language Engine
                </h1>
                <p className="text-xs text-gray-600 leading-relaxed">
                  Ask in plain English in the Aegis Agent on the right to trigger multi-table API queries against our SQLite database. Inspect any table with <strong className="text-gray-900 font-semibold">Database State</strong> or test endpoints in <strong className="text-gray-900 font-semibold">API Explorer</strong>.
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-2.5 mt-4 pt-3 border-t border-gray-100">
                <button
                  id="btn-hero-api-explorer"
                  type="button"
                  onClick={() => openApiExplorer(null)}
                  className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-[#FF6C37] hover:bg-[#E85B27] active:bg-[#D44C1A] text-white shadow-xs transition-all cursor-pointer active:scale-95 select-none"
                  title="Open API Catalog & Live Runner"
                >
                  <Code2 className="w-3.5 h-3.5" />
                  <span>Open API Explorer (15 Endpoints)</span>
                  <ArrowRight className="w-3 h-3 ml-1" />
                </button>

                <button
                  onClick={() => runSampleApiQuery(1)}
                  disabled={loadingTest}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-white hover:bg-gray-50 text-gray-700 border border-gray-300 shadow-xs transition-colors"
                >
                  <Play className={`w-3.5 h-3.5 text-[#FF6C37] ${loadingTest ? 'animate-spin' : ''}`} />
                  Run Graduation Audit (Student #1)
                </button>
              </div>
            </div>

            {/* Metrics Overview */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
              <div
                onClick={() => setIsDbModalOpen(true)}
                className="p-3.5 rounded-xl border border-gray-200 bg-white hover:border-orange-300 hover:shadow-xs transition-all flex items-center justify-between cursor-pointer select-none group"
                title="Click to inspect University Database State"
              >
                <div>
                  <p className="text-[11px] text-gray-500 font-medium group-hover:text-[#FF6C37] transition-colors">Relational Tables</p>
                  <h3 className="text-xl font-bold text-gray-900 mt-0.5 font-mono">
                    {dbOverview ? dbOverview.total_tables : 30} Tables
                  </h3>
                  <span className="text-[10px] text-gray-400 font-mono">
                    {dbOverview ? dbOverview.total_records.toLocaleString() : '6,962'} rows
                  </span>
                </div>
                <div className="p-2.5 bg-orange-50 text-[#FF6C37] rounded-lg border border-orange-100 group-hover:scale-105 transition-transform">
                  <Table className="w-4 h-4" />
                </div>
              </div>

              <div
                id="card-metric-api-catalog"
                onClick={() => openApiExplorer(null)}
                className="p-3.5 rounded-xl border border-gray-200 bg-white hover:border-blue-300 hover:shadow-xs transition-all flex items-center justify-between cursor-pointer select-none group"
                title="Click to open API Explorer"
              >
                <div>
                  <p className="text-[11px] text-gray-500 font-medium group-hover:text-blue-600 transition-colors">API Catalog</p>
                  <h3 className="text-xl font-bold text-gray-900 mt-0.5 font-mono">15 Endpoints</h3>
                  <span className="text-[10px] text-gray-400 font-mono">Simple • Med • Complex</span>
                </div>
                <div className="p-2.5 bg-blue-50 text-blue-600 rounded-lg border border-blue-100 group-hover:scale-105 transition-transform">
                  <Layers className="w-4 h-4" />
                </div>
              </div>

              <div className="p-3.5 rounded-xl border border-gray-200 bg-white shadow-xs flex items-center justify-between">
                <div>
                  <p className="text-[11px] text-gray-500 font-medium">NL Interface</p>
                  <h3 className="text-base font-bold text-emerald-600 mt-0.5">Aegis Agent</h3>
                  <span className="text-[10px] text-gray-400 font-mono">SQLite + Groq</span>
                </div>
                <div className="p-2.5 bg-emerald-50 text-emerald-600 rounded-lg border border-emerald-100">
                  <Sparkles className="w-4 h-4" />
                </div>
              </div>
            </div>

            {/* Live Complex API Response Sample (If Triggered) */}
            {testStudent && (
              <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-xs space-y-2.5 animate-fadeIn">
                <div className="flex items-center justify-between pb-2 border-b border-gray-100">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-purple-100 text-purple-700">
                      GET
                    </span>
                    <span className="text-xs font-mono text-gray-800 font-semibold truncate max-w-[280px]">
                      /api/v1/students/1/graduation-eligibility
                    </span>
                  </div>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                    testStudent.graduation_approved
                      ? 'bg-emerald-100 text-emerald-700 border border-emerald-200'
                      : 'bg-amber-100 text-amber-800 border border-amber-200'
                  }`}>
                    {testStudent.eligibility_verdict}
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 text-xs">
                  {testStudent.audit_criteria?.map((crit, idx) => (
                    <div key={idx} className="p-2.5 bg-gray-50 rounded-lg border border-gray-200">
                      <div className="flex items-center justify-between mb-0.5">
                        <span className="text-gray-500 text-[10px]">{crit.criterion}</span>
                        <span className={`px-1 py-0.2 rounded font-mono text-[9px] font-bold ${
                          crit.passed ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
                        }`}>
                          {crit.status}
                        </span>
                      </div>
                      <span className="font-bold text-gray-900 block text-xs">{crit.value}</span>
                    </div>
                  ))}
                </div>

                <div className="p-2.5 bg-gray-50 rounded-lg border border-gray-200 text-xs">
                  <span className="font-bold text-gray-700 block mb-0.5 text-[11px]">Audit Findings & Action Items:</span>
                  <ul className="list-disc list-inside space-y-0.5 text-gray-600 text-[11px]">
                    {testStudent.action_items?.map((act, i) => (
                      <li key={i}>{act}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {/* Featured APIs Across 30 Tables */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-bold text-gray-900 tracking-tight">Available Relational Endpoints</h2>
                <button
                  type="button"
                  onClick={() => openApiExplorer(null)}
                  className="text-xs font-semibold text-[#FF6C37] hover:underline cursor-pointer flex items-center gap-1 select-none"
                >
                  View all 15 APIs →
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div
                  onClick={() => openApiExplorer('api_courses_catalog')}
                  className="p-3.5 rounded-xl border border-gray-200 bg-white hover:border-emerald-300 hover:shadow-xs transition-all space-y-2 cursor-pointer select-none group"
                  title="Click to test in API Explorer"
                >
                  <div className="flex items-center justify-between">
                    <span className="px-1.5 py-0.2 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                      🟢 Simple
                    </span>
                    <span className="text-[10px] text-gray-400 font-mono">1 Table</span>
                  </div>
                  <h3 className="text-xs font-bold text-gray-900 group-hover:text-emerald-700 transition-colors">Course Catalog</h3>
                  <p className="text-[11px] text-gray-500 font-mono">GET /api/v1/courses/catalog</p>
                  <p className="text-[11px] text-gray-600">
                    Query courses by code, title, and minimum credits.
                  </p>
                </div>

                <div
                  onClick={() => openApiExplorer('api_student_finance_ledger')}
                  className="p-3.5 rounded-xl border border-gray-200 bg-white hover:border-blue-300 hover:shadow-xs transition-all space-y-2 cursor-pointer select-none group"
                  title="Click to test in API Explorer"
                >
                  <div className="flex items-center justify-between">
                    <span className="px-1.5 py-0.2 rounded text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200">
                      🟡 Medium
                    </span>
                    <span className="text-[10px] text-gray-400 font-mono">4 Tables</span>
                  </div>
                  <h3 className="text-xs font-bold text-gray-900 group-hover:text-blue-700 transition-colors">Tuition & Fee Ledger</h3>
                  <p className="text-[11px] text-gray-500 font-mono">GET /api/v1/finance/student/{'{id}'}/ledger</p>
                  <p className="text-[11px] text-gray-600">
                    Reconciles invoices, fee categories, and recorded payments.
                  </p>
                </div>

                <div
                  onClick={() => openApiExplorer('api_student_transcript_audit')}
                  className="p-3.5 rounded-xl border border-gray-200 bg-white hover:border-purple-300 hover:shadow-xs transition-all space-y-2 cursor-pointer select-none group"
                  title="Click to test in API Explorer"
                >
                  <div className="flex items-center justify-between">
                    <span className="px-1.5 py-0.2 rounded text-[10px] font-bold bg-purple-50 text-purple-700 border border-purple-200">
                      🔴 Complex
                    </span>
                    <span className="text-[10px] text-gray-400 font-mono">6 Tables</span>
                  </div>
                  <h3 className="text-xs font-bold text-gray-900 group-hover:text-purple-700 transition-colors">Official Transcript & CGPA</h3>
                  <p className="text-[11px] text-gray-500 font-mono">GET /api/v1/students/{'{id}'}/transcript-audit</p>
                  <p className="text-[11px] text-gray-600">
                    Semester term breakdown, weighted CGPA arithmetic & honors.
                  </p>
                </div>
              </div>
            </div>

          </div>

          {/* RIGHT 2/5 COLUMN: GROQ AI CHATBOT PANEL */}
          <ChatbotPanel />

        </div>
      </main>

      {/* Database State Inspector Modal */}
      <DatabaseModal
        isOpen={isDbModalOpen}
        onClose={() => setIsDbModalOpen(false)}
      />

      {/* API Explorer Modal */}
      <ApiExplorerModal
        isOpen={isApiModalOpen}
        onClose={() => setIsApiModalOpen(false)}
        initialCatalog={apiCatalog}
        targetEndpointId={selectedEndpointId}
      />

    </div>
  );
}
