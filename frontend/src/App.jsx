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
import aegisLogo from './assets/aegis_logo.png';
import aegisBrandText from './assets/aegis_brand_text.png';

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
      
      {/* Signature Orange Top Navigation Bar */}
      <header className="h-14 shrink-0 bg-[#FF6C37] border-b border-[#E85B27] px-6 flex items-center justify-between shadow-xs z-30">
        
        {/* Brand & Logo: Logo in White Circle + Name (Black 'Aegius' + White 'Registry') */}
        <div className="flex items-center gap-3">
          {/* Logo in White Circle */}
          <div className="w-9 h-9 rounded-full bg-white flex items-center justify-center p-1.5 shadow-xs shrink-0 overflow-hidden">
            <img src={aegisLogo} alt="Aegis Logo" className="w-full h-full object-contain" />
          </div>

          {/* Name: Transparent Background, Black 'Aegius' + White 'Registry' */}
          <div className="flex items-center">
            <img src={aegisBrandText} alt="AegiusRegistry" className="h-7 w-auto object-contain select-none" />
          </div>

          <span className="hidden xl:inline-block text-xs font-medium text-white/90 tracking-wide border-l border-white/25 pl-3">
            Autonomous Self-Healing Tool Interface Under API Schema Drift
          </span>
        </div>

        {/* Right Corner Action Buttons: API Catalog & Database (Attractive, Professional White Cards) */}
        <div className="flex items-center gap-2.5">
          <button
            id="btn-api-explorer"
            type="button"
            onClick={() => openApiExplorer(null)}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-white hover:bg-orange-50 active:bg-orange-100 text-gray-900 shadow-2xs hover:shadow-xs transition-all duration-150 cursor-pointer active:scale-95 select-none"
            title="Open API Catalog & Live Runner (15 Endpoints)"
          >
            <Code2 className="w-3.5 h-3.5 text-[#FF6C37]" />
            <span className="font-semibold text-gray-900">API Catalog</span>
            <span className="px-1.5 py-0.5 rounded-md bg-orange-100 text-[#FF6C37] font-mono text-[10px] font-bold">
              15 APIs
            </span>
          </button>

          <button
            id="btn-database-state-inspector"
            type="button"
            onClick={() => setIsDbModalOpen(true)}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-white hover:bg-orange-50 active:bg-orange-100 text-gray-900 shadow-2xs hover:shadow-xs transition-all duration-150 cursor-pointer active:scale-95 select-none"
            title="Inspect 31 University Database Tables"
          >
            <Database className="w-3.5 h-3.5 text-[#FF6C37]" />
            <span className="font-semibold text-gray-900">Database</span>
            <span className="px-1.5 py-0.5 rounded-md bg-orange-100 text-[#FF6C37] font-mono text-[10px] font-bold">
              {dbOverview ? `${dbOverview.total_tables} Tbls` : '31 Tbls'}
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
