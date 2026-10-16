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
import ExecutionConsole from './components/ExecutionConsole';
import { fetchHealth, fetchDatabaseOverview, fetchApiCatalog } from './services/api';

export default function App() {
  const [isDbModalOpen, setIsDbModalOpen] = useState(false);
  const [isApiModalOpen, setIsApiModalOpen] = useState(false);
  const [selectedEndpointId, setSelectedEndpointId] = useState(null);
  const [serverStatus, setServerStatus] = useState('checking');
  const [dbOverview, setDbOverview] = useState(null);
  const [apiCatalog, setApiCatalog] = useState(null);

  // Real-time execution console state
  const [executionData, setExecutionData] = useState(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [backendUptime, setBackendUptime] = useState(120);
  const [externalQuery, setExternalQuery] = useState(null);

  const openApiExplorer = (endpointId = null) => {
    setSelectedEndpointId(endpointId);
    setIsApiModalOpen(true);
  };

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const health = await fetchHealth();
        setServerStatus('online');
        if (health && health.uptime_seconds) {
          setBackendUptime(health.uptime_seconds);
        }
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

  const handleExecutionStart = (queryInfo) => {
    setIsExecuting(true);
    setExecutionData({
      query: queryInfo.query,
      engineMode: queryInfo.engineMode,
      timestamp: queryInfo.timestamp || Date.now(),
      status: 'running',
      apiCall: null,
      logs: [
        {
          elapsed_ms: 0.1,
          tag: 'INGRESS',
          level: 'info',
          message: `User query: "${queryInfo.query}"`
        },
        {
          elapsed_ms: 1.2,
          tag: 'ROUTER',
          level: 'dispatch',
          message: `Engine mode: ${queryInfo.engineMode === 'aegis' ? 'AegisRegistry Autonomous AST Healer' : 'LangChain Agent (Baseline)'}`
        }
      ],
      telemetry: {
        execution_time_ms: 0,
        tokens_used: 0,
        ast_time_ms: 0,
        healed: false,
        engine_mode: queryInfo.engineMode
      }
    });
  };

  const handleExecutionComplete = (response) => {
    setIsExecuting(false);
    setExecutionData(prev => ({
      ...prev,
      status: response.status === 'error' ? 'error' : 'completed',
      apiCall: response.api_call,
      logs: response.execution_logs || prev?.logs || [],
      telemetry: response.telemetry || {
        execution_time_ms: response.api_call?.latency_ms || 18.5,
        tokens_used: response.telemetry?.tokens_used || 84,
        ast_time_ms: response.healed_telemetry?.ast_diagnosis_ms || 0.8,
        healed: response.healed || false,
        status_code: response.api_call?.status_code || 200,
        engine_mode: response.engineMode || prev?.engineMode || 'aegis'
      }
    }));
  };

  const handleResetConsole = () => {
    setExecutionData(null);
    setIsExecuting(false);
  };

  const handleQuickRun = (queryText) => {
    setExternalQuery({ text: queryText, timestamp: Date.now() });
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
          
          {/* LEFT 3/5 COLUMN: LIVE REAL-TIME EXECUTION & TELEMETRY CONSOLE */}
          <ExecutionConsole
            executionData={executionData}
            isExecuting={isExecuting}
            backendUptime={backendUptime}
            onResetConsole={handleResetConsole}
            onQuickRun={handleQuickRun}
          />

          {/* RIGHT 2/5 COLUMN: GROQ AI CHATBOT PANEL */}
          <ChatbotPanel
            onExecutionStart={handleExecutionStart}
            onExecutionComplete={handleExecutionComplete}
            externalTriggerQuery={externalQuery}
          />

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
