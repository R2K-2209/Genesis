import React, { useState, useEffect } from 'react';
import {
  Code2,
  Search,
  Send,
  X,
  ExternalLink,
  Layers,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Copy,
  Clock,
  Sparkles,
  RefreshCw,
  RotateCcw,
  Zap,
  Table
} from 'lucide-react';
import { fetchApiCatalog, executeApiEndpoint, updateDriftState } from '../services/api';

export default function ApiExplorerModal({ isOpen, onClose, initialCatalog = null, targetEndpointId = null }) {
  const [catalog, setCatalog] = useState(initialCatalog);
  const [loadingCatalog, setLoadingCatalog] = useState(false);
  const [selectedApi, setSelectedApi] = useState(null);
  const [filterComplexity, setFilterComplexity] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  
  // Execution state
  const [params, setParams] = useState({});
  const [requestBody, setRequestBody] = useState('');
  const [executing, setExecuting] = useState(false);
  const [responseResult, setResponseResult] = useState(null);
  const [copied, setCopied] = useState(false);

  // Schema Drift / Broken API State
  const [activeDriftMode, setActiveDriftMode] = useState('healthy');
  const [customPath, setCustomPath] = useState(null);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  useEffect(() => {
    if (isOpen) {
      if (initialCatalog && initialCatalog.endpoints) {
        setCatalog(initialCatalog);
        if (targetEndpointId) {
          const target = initialCatalog.endpoints.find(e => e.id === targetEndpointId);
          if (target) selectEndpoint(target);
          else if (!selectedApi) selectEndpoint(initialCatalog.endpoints[0]);
        } else if (!selectedApi) {
          selectEndpoint(initialCatalog.endpoints[0]);
        }
      } else {
        loadCatalog();
      }
    }
  }, [isOpen, initialCatalog, targetEndpointId]);

  const loadCatalog = async () => {
    try {
      setLoadingCatalog(true);
      const data = await fetchApiCatalog();
      setCatalog(data);
      if (data.endpoints && data.endpoints.length > 0) {
        if (targetEndpointId) {
          const target = data.endpoints.find(e => e.id === targetEndpointId);
          if (target) selectEndpoint(target);
          else if (!selectedApi) selectEndpoint(data.endpoints[0]);
        } else if (!selectedApi) {
          selectEndpoint(data.endpoints[0]);
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingCatalog(false);
    }
  };

  const getDriftOptionsForApi = (endpoint) => {
    if (!endpoint) return [];
    return [
      {
        id: 'healthy',
        label: '🟢 Healthy / Standard Schema (Default)',
        badge: 'Healthy',
        badgeColor: 'bg-emerald-50 text-emerald-700 border-emerald-200',
        description: 'Official API contract v1 with expected parameters and valid types.'
      },
      {
        id: 'param_renamed',
        label: '⚡ Drift 1: Parameter Renamed',
        badge: 'Renamed',
        badgeColor: 'bg-amber-50 text-amber-700 border-amber-200',
        description: 'Simulates field rename (e.g. status -> student_status, search -> keyword, student_id -> candidate_id).'
      },
      {
        id: 'type_mutated',
        label: '⚡ Drift 2: Data Type Mutation (Type Mismatch)',
        badge: 'Type Cast',
        badgeColor: 'bg-purple-50 text-purple-700 border-purple-200',
        description: 'Passes invalid type (e.g. string UUID where integer ID expected), triggering 422 Unprocessable Entity.'
      },
      {
        id: 'nested_wrapped',
        label: '⚡ Drift 3: Nested Object Required',
        badge: 'Nesting',
        badgeColor: 'bg-blue-50 text-blue-700 border-blue-200',
        description: 'Wraps query or body parameters inside a nested filter structure (e.g. filter[param]=val).'
      },
      {
        id: 'missing_required',
        label: '⚡ Drift 4: Missing Mandatory Field',
        badge: 'Missing Field',
        badgeColor: 'bg-red-50 text-red-700 border-red-200',
        description: 'Omits primary required path/query identifier to test endpoint schema validation failure.'
      },
      {
        id: 'route_deprecated',
        label: '⚡ Drift 5: Route Migration (/api/v2 path)',
        badge: 'Route Drift',
        badgeColor: 'bg-rose-50 text-rose-700 border-rose-200',
        description: 'Simulates endpoint path migration drift to /api/v2/, triggering 404 Route Not Found.'
      }
    ];
  };

  const selectEndpoint = (endpoint) => {
    setSelectedApi(endpoint);
    setActiveDriftMode('healthy');
    setCustomPath(null);
    setParams(endpoint.default_params ? { ...endpoint.default_params } : {});
    if (endpoint.method === 'POST') {
      setRequestBody(JSON.stringify(endpoint.default_params, null, 2));
    } else {
      setRequestBody('');
    }
    setResponseResult(null);
  };

  const applyDriftMode = (modeId) => {
    if (!selectedApi) return;
    setActiveDriftMode(modeId);
    setResponseResult(null);

    const baseParams = selectedApi.default_params ? { ...selectedApi.default_params } : {};

    if (modeId === 'healthy') {
      setCustomPath(null);
      setParams(baseParams);
      if (selectedApi.method === 'POST') {
        setRequestBody(JSON.stringify(baseParams, null, 2));
      } else {
        setRequestBody('');
      }
      updateDriftState(selectedApi.id, 'healthy').catch(console.error);
      return;
    }

    let mutatedParams = {};
    let targetPath = null;

    if (modeId === 'param_renamed') {
      const mutated = {};
      Object.entries(baseParams).forEach(([k, v]) => {
        if (k === 'status') mutated['student_status'] = v;
        else if (k === 'search') mutated['keyword'] = v;
        else if (k === 'query') mutated['title_or_author'] = v;
        else if (k === 'student_id') mutated['candidate_id'] = v;
        else if (k === 'course_id') mutated['class_id'] = v;
        else if (k === 'card_id') mutated['borrower_card_no'] = v;
        else if (k === 'invoice_id') mutated['bill_id'] = v;
        else if (k === 'amount') mutated['payment_value'] = v;
        else mutated[`drift_${k}`] = v;
      });
      mutatedParams = mutated;
      setCustomPath(null);
      setParams(mutated);
      if (selectedApi.method === 'POST') {
        setRequestBody(JSON.stringify(mutated, null, 2));
      }
    } else if (modeId === 'type_mutated') {
      const mutated = {};
      Object.entries(baseParams).forEach(([k, v]) => {
        if (typeof v === 'number' || k.endsWith('_id') || k === 'page' || k === 'limit' || k === 'min_credits') {
          mutated[k] = `UUID_ERR_${v}_ALPHA`;
        } else {
          mutated[k] = v;
        }
      });
      mutatedParams = mutated;
      setCustomPath(null);
      setParams(mutated);
      if (selectedApi.method === 'POST') {
        setRequestBody(JSON.stringify(mutated, null, 2));
      }
    } else if (modeId === 'nested_wrapped') {
      const mutated = {};
      Object.entries(baseParams).forEach(([k, v]) => {
        mutated[`filter[${k}]`] = v;
      });
      mutatedParams = mutated;
      setCustomPath(null);
      setParams(mutated);
      if (selectedApi.method === 'POST') {
        setRequestBody(JSON.stringify({ filter: baseParams }, null, 2));
      }
    } else if (modeId === 'missing_required') {
      mutatedParams = {};
      setCustomPath(null);
      setParams({});
      if (selectedApi.method === 'POST') {
        setRequestBody(JSON.stringify({}, null, 2));
      }
    } else if (modeId === 'route_deprecated') {
      mutatedParams = baseParams;
      targetPath = selectedApi.path.replace('/api/v1/', '/api/v2/');
      setParams(baseParams);
      setCustomPath(targetPath);
      if (selectedApi.method === 'POST') {
        setRequestBody(JSON.stringify(baseParams, null, 2));
      }
    }

    // Sync drift state with backend
    updateDriftState(selectedApi.id, modeId, mutatedParams, targetPath).catch(console.error);
  };

  const handleResetToHealthy = () => {
    applyDriftMode('healthy');
  };

  const handleSend = async () => {
    if (!selectedApi) return;
    try {
      setExecuting(true);
      setResponseResult(null);
      let bodyData = null;
      if (selectedApi.method === 'POST' && requestBody.trim()) {
        try {
          bodyData = JSON.parse(requestBody);
        } catch (e) {
          alert('Invalid JSON in Request Body!');
          setExecuting(false);
          return;
        }
      }
      const activePath = customPath || selectedApi.path;
      const result = await executeApiEndpoint(selectedApi.method, activePath, params, bodyData);
      setResponseResult(result);
    } catch (err) {
      setResponseResult({
        ok: false,
        status: 500,
        statusText: 'Client Error',
        latency: 0,
        data: { error: err.message }
      });
    } finally {
      setExecuting(false);
    }
  };

  const copyResponse = () => {
    if (!responseResult || !responseResult.data) return;
    navigator.clipboard.writeText(JSON.stringify(responseResult.data, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getResolvedPath = () => {
    if (!selectedApi) return '';
    let p = customPath || selectedApi.path;
    Object.entries(params).forEach(([k, v]) => {
      const placeholder = `{${k}}`;
      if (p.includes(placeholder)) {
        p = p.replace(placeholder, v !== '' && v !== undefined ? v : placeholder);
      }
    });
    return p;
  };

  if (!isOpen) return null;

  const endpoints = catalog?.endpoints || [];
  const filteredEndpoints = endpoints.filter(ep => {
    const matchesComplexity = filterComplexity === 'All' || ep.complexity === filterComplexity;
    const matchesSearch = ep.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          ep.path.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          ep.tables.some(t => t.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesComplexity && matchesSearch;
  });

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/50 backdrop-blur-xs p-4 sm:p-6 animate-fadeIn"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="relative w-full h-[94vh] max-w-7xl bg-white border border-gray-200 rounded-xl shadow-2xl flex flex-col overflow-hidden">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-3.5 border-b border-gray-200 bg-white">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-orange-50 border border-orange-200 flex items-center justify-center text-[#FF6C37]">
              <Code2 className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h2 className="text-base font-bold text-gray-900 tracking-tight">University API Catalog & Live Runner</h2>
                <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-orange-50 text-[#FF6C37] border border-orange-200 font-mono">
                  15 Multi-Table Endpoints
                </span>
                <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-gray-100 text-gray-700 border border-gray-200">
                  FastAPI Server
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-0.5">
                Ranging from Simple single-table lookups to Complex relational audits across 30 tables
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold bg-white hover:bg-gray-50 text-gray-700 transition-colors border border-gray-300 shadow-2xs cursor-pointer"
            >
              <ExternalLink className="w-3.5 h-3.5 text-[#FF6C37]" />
              Swagger Docs
            </a>

            <button
              onClick={loadCatalog}
              className="p-1.5 rounded-md text-gray-500 hover:text-gray-800 hover:bg-gray-100 transition-colors cursor-pointer"
              title="Refresh Catalog"
            >
              <RefreshCw className={`w-4 h-4 ${loadingCatalog ? 'animate-spin' : ''}`} />
            </button>

            <button
              id="btn-close-api-explorer"
              type="button"
              onClick={onClose}
              className="p-1.5 rounded-md text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors ml-1 cursor-pointer"
              title="Close modal (Esc)"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Main Content Area: Split Sidebar & Runner */}
        <div className="flex flex-1 overflow-hidden">
          
          {/* Left Sidebar: Filter Tabs & Endpoint List */}
          <div className="w-80 border-r border-gray-200 bg-[#F9FAFB] flex flex-col">
            
            {/* Search Box */}
            <div className="p-3 border-b border-gray-200 bg-white">
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search APIs or tables..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-8 pr-3 py-1.5 text-xs bg-white border border-gray-300 rounded-md text-gray-800 placeholder-gray-400 focus:outline-none focus:border-[#FF6C37] focus:ring-1 focus:ring-[#FF6C37]"
                />
              </div>

              {/* Complexity Tabs */}
              <div className="flex items-center gap-1 mt-2">
                {['All', 'Simple', 'Medium', 'Complex'].map(tier => (
                  <button
                    key={tier}
                    onClick={() => setFilterComplexity(tier)}
                    className={`flex-1 py-1 text-[11px] font-semibold rounded-md transition-colors ${
                      filterComplexity === tier
                        ? 'bg-[#FF6C37] text-white shadow-2xs'
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    }`}
                  >
                    {tier}
                  </button>
                ))}
              </div>
            </div>

            {/* Endpoints List */}
            <div className="flex-1 overflow-y-auto p-2 space-y-1">
              {filteredEndpoints.map(ep => {
                const isSelected = selectedApi?.id === ep.id;
                return (
                  <button
                    key={ep.id}
                    onClick={() => selectEndpoint(ep)}
                    className={`w-full text-left p-2.5 rounded-lg border transition-all ${
                      isSelected
                        ? 'bg-orange-50 border-orange-300 shadow-2xs'
                        : 'bg-white hover:bg-gray-100 border-gray-200'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <div className="flex items-center gap-1.5">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold ${
                          ep.method === 'POST' ? 'bg-orange-100 text-[#FF6C37]' : 'bg-emerald-100 text-emerald-700'
                        }`}>
                          {ep.method}
                        </span>
                        <span className={`text-[10px] font-semibold px-1.5 py-0.2 rounded border ${
                          ep.complexity === 'Simple'
                            ? 'bg-gray-50 text-gray-600 border-gray-200'
                            : ep.complexity === 'Medium'
                            ? 'bg-blue-50 text-blue-700 border-blue-200'
                            : 'bg-purple-50 text-purple-700 border-purple-200'
                        }`}>
                          {ep.complexity}
                        </span>
                      </div>
                      <span className="text-[10px] text-gray-400 font-mono">
                        {ep.tables.length} {ep.tables.length === 1 ? 'tbl' : 'tbls'}
                      </span>
                    </div>

                    <div className="text-xs font-bold text-gray-900 truncate">
                      {ep.name}
                    </div>
                    <div className="text-[11px] text-gray-500 font-mono truncate mt-0.5">
                      {ep.path}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Right Runner & Inspector Panel */}
          {selectedApi ? (
            <div className="flex-1 flex flex-col bg-white overflow-hidden">
              
              {/* URL & Send Bar with Schema Drift / Break API Dropdown and Reset Button */}
              <div className="p-4 border-b border-gray-200 bg-gray-50/50 flex flex-col gap-3">
                <div className="flex flex-wrap items-center gap-2.5">
                  <span className={`px-2.5 py-1.5 rounded-md text-xs font-mono font-extrabold shadow-2xs shrink-0 ${
                    selectedApi.method === 'POST'
                      ? 'bg-orange-100 text-[#FF6C37] border border-orange-200'
                      : 'bg-emerald-100 text-emerald-700 border border-emerald-200'
                  }`}>
                    {selectedApi.method}
                  </span>

                  {/* Schema Drift Selector Dropdown (Right beside GET tag) */}
                  <div className="flex items-center gap-1.5 shrink-0">
                    <div className="relative">
                      <select
                        id="select-api-drift-version"
                        value={activeDriftMode}
                        onChange={(e) => applyDriftMode(e.target.value)}
                        className={`pl-2.5 pr-8 py-1.5 text-xs font-semibold rounded-md border shadow-2xs focus:outline-none transition-all cursor-pointer ${
                          activeDriftMode === 'healthy'
                            ? 'bg-white text-gray-800 border-gray-300 hover:border-gray-400'
                            : 'bg-amber-50 text-amber-900 border-amber-400 ring-1 ring-amber-400 font-bold'
                        }`}
                        title="Simulate Schema Drift / Break API Contract"
                      >
                        {getDriftOptionsForApi(selectedApi).map(opt => (
                          <option key={opt.id} value={opt.id}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Reset Button (Reverts to healthy original query) */}
                    <button
                      id="btn-reset-api-schema"
                      type="button"
                      onClick={handleResetToHealthy}
                      disabled={activeDriftMode === 'healthy'}
                      className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-semibold rounded-md border border-gray-300 bg-white hover:bg-gray-100 active:bg-gray-200 text-gray-700 disabled:opacity-40 disabled:cursor-not-allowed shadow-2xs transition-colors shrink-0"
                      title="Reset and auto-select standard healthy query"
                    >
                      <RotateCcw className="w-3.5 h-3.5 text-gray-500" />
                      <span>Reset</span>
                    </button>
                  </div>

                  {/* URL Display Bar */}
                  <div className="flex-1 min-w-[220px] flex items-center px-3 py-1.5 bg-white border border-gray-300 rounded-md font-mono text-xs text-gray-800 shadow-inner overflow-hidden">
                    <span className="text-gray-400 mr-1 shrink-0">http://localhost:8000</span>
                    <span className={`font-semibold truncate ${activeDriftMode !== 'healthy' ? 'text-amber-700 underline decoration-amber-400' : 'text-gray-900'}`}>
                      {getResolvedPath()}
                    </span>
                  </div>

                  <button
                    onClick={handleSend}
                    disabled={executing}
                    className="flex items-center gap-2 px-5 py-2 rounded-md text-xs font-bold bg-[#FF6C37] hover:bg-[#E85B27] active:bg-[#D44C1A] text-white shadow-sm transition-all disabled:opacity-50 shrink-0"
                  >
                    <Send className={`w-3.5 h-3.5 ${executing ? 'animate-spin' : ''}`} />
                    {executing ? 'Executing...' : 'Send Request'}
                  </button>
                </div>

                {/* API Metadata Header */}
                <div className="flex flex-wrap items-center justify-between gap-2 pt-1 text-xs">
                  <div>
                    <h3 className="text-sm font-bold text-gray-900">{selectedApi.name}</h3>
                    <p className="text-xs text-gray-600 mt-0.5">{selectedApi.description}</p>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-[11px] text-gray-500 font-medium">Tables Used:</span>
                    {selectedApi.tables.map(tbl => (
                      <span key={tbl} className="px-2 py-0.5 bg-white border border-gray-200 rounded text-[10px] font-mono text-gray-700">
                        {tbl}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Lower Section: Parameters + Live Response View */}
              <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 overflow-hidden divide-y lg:divide-y-0 lg:divide-x divide-gray-200">
                
                {/* Parameters & Request Configuration */}
                <div className="flex flex-col p-4 overflow-y-auto space-y-4">
                  
                  {/* Schema Drift Active Alert Banner */}
                  {activeDriftMode !== 'healthy' && (
                    <div className="p-3 rounded-lg bg-amber-50 border border-amber-300 text-xs flex items-start justify-between gap-2 text-amber-900 animate-fadeIn">
                      <div className="flex items-start gap-2">
                        <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                        <div>
                          <div className="font-bold flex items-center gap-1.5">
                            <span>Schema Drift Injected:</span>
                            <span className="font-mono text-[10px] px-1.5 py-0.2 bg-amber-200 text-amber-900 rounded font-bold">
                              {activeDriftMode.toUpperCase()}
                            </span>
                          </div>
                          <p className="text-[11px] text-amber-800 mt-0.5">
                            {getDriftOptionsForApi(selectedApi).find(o => o.id === activeDriftMode)?.description}
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={handleResetToHealthy}
                        className="px-2 py-0.5 bg-white hover:bg-amber-100 border border-amber-300 text-amber-900 rounded text-[10px] font-semibold shrink-0"
                      >
                        Reset Schema
                      </button>
                    </div>
                  )}

                  <div className="flex items-center justify-between pb-2 border-b border-gray-100">
                    <h4 className="text-xs font-bold text-gray-900 uppercase tracking-wider">
                      Request Parameters
                    </h4>
                    <span className="text-[11px] text-gray-500 font-mono">
                      {Object.keys(params).length} parameter(s)
                    </span>
                  </div>

                  {selectedApi.method === 'GET' && Object.keys(params).length > 0 ? (
                    <div className="space-y-3">
                      {Object.entries(params).map(([key, val]) => (
                        <div key={key}>
                          <label className="block text-[11px] font-mono font-semibold text-gray-700 mb-1">
                            {key} {selectedApi.path.includes(`{${key}}`) && <span className="text-[#FF6C37]">*Path</span>}
                          </label>
                          <input
                            type="text"
                            value={val ?? ''}
                            onChange={(e) => setParams({ ...params, [key]: e.target.value })}
                            className="w-full px-3 py-1.5 text-xs bg-white border border-gray-300 rounded-md text-gray-800 font-mono focus:outline-none focus:border-[#FF6C37] focus:ring-1 focus:ring-[#FF6C37]"
                          />
                        </div>
                      ))}
                    </div>
                  ) : selectedApi.method === 'POST' ? (
                    <div className="flex-1 flex flex-col">
                      <label className="block text-[11px] font-mono font-semibold text-gray-700 mb-1">
                        JSON Request Body:
                      </label>
                      <textarea
                        rows={8}
                        value={requestBody}
                        onChange={(e) => setRequestBody(e.target.value)}
                        className="w-full p-3 text-xs bg-gray-50 border border-gray-300 rounded-md font-mono text-gray-800 focus:outline-none focus:border-[#FF6C37] focus:bg-white resize-none"
                      />
                    </div>
                  ) : (
                    <div className="p-4 rounded-md bg-gray-50 border border-gray-200 text-xs text-gray-500 text-center">
                      This endpoint requires no parameters. Click "Send Request" to execute.
                    </div>
                  )}

                  <div className="p-3 bg-orange-50/70 border border-orange-200 rounded-lg text-xs text-orange-950">
                    <span className="font-semibold text-[#FF6C37] block mb-0.5">Relational Intelligence:</span>
                    This endpoint queries SQLite 3 with full integrity and returns live calculated fields across the database.
                  </div>
                </div>

                {/* Live Response Panel */}
                <div className="flex flex-col bg-gray-50/30 overflow-hidden">
                  
                  {/* Response Status Bar */}
                  <div className="p-3 border-b border-gray-200 bg-white flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <h4 className="text-xs font-bold text-gray-900 uppercase tracking-wider">Response</h4>
                      {responseResult && (
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 rounded text-[11px] font-mono font-bold ${
                            responseResult.ok
                              ? 'bg-emerald-100 text-emerald-700 border border-emerald-200'
                              : 'bg-red-100 text-red-700 border border-red-200'
                          }`}>
                            {responseResult.status} {responseResult.statusText}
                          </span>
                          <span className="flex items-center gap-1 text-[11px] text-gray-500 font-mono">
                            <Clock className="w-3 h-3" />
                            {responseResult.latency} ms
                          </span>
                        </div>
                      )}
                    </div>

                    {responseResult?.data && (
                      <button
                        onClick={copyResponse}
                        className="flex items-center gap-1 px-2.5 py-1 text-[11px] font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded border border-gray-200 transition-colors"
                      >
                        <Copy className="w-3 h-3 text-[#FF6C37]" />
                        {copied ? 'Copied!' : 'Copy JSON'}
                      </button>
                    )}
                  </div>

                  {/* Response Body Viewer */}
                  <div className="flex-1 p-3 overflow-auto bg-gray-900 text-emerald-400 font-mono text-xs">
                    {executing ? (
                      <div className="flex items-center justify-center h-full text-gray-400 gap-2">
                        <RefreshCw className="w-4 h-4 animate-spin text-[#FF6C37]" />
                        Executing query against SQLite database...
                      </div>
                    ) : responseResult ? (
                      <pre className="whitespace-pre-wrap">
                        {JSON.stringify(responseResult.data, null, 2)}
                      </pre>
                    ) : (
                      <div className="flex flex-col items-center justify-center h-full text-gray-500">
                        <Send className="w-6 h-6 text-gray-600 mb-2" />
                        <p>Click "Send Request" to execute this API live.</p>
                      </div>
                    )}
                  </div>

                </div>

              </div>
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-400 text-xs">
              Select an API from the catalog list on the left
            </div>
          )}

        </div>

      </div>
    </div>
  );
}
