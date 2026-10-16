import React, { useState, useEffect, useRef } from 'react';
import {
  Send,
  Settings,
  Trash2,
  ChevronDown,
  ChevronRight,
  Key,
  X,
  Database,
  Code2
} from 'lucide-react';
import { sendChatMessage } from '../services/api';

export default function ChatbotPanel() {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      text: "Hello! I am Aegis Agent. Ask any question about students, courses, transcripts, graduation audits, or university records.",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [useLangChain, setUseLangChain] = useState(() => localStorage.getItem('use_langchain') === 'true');
  const [groqApiKey, setGroqApiKey] = useState(() => localStorage.getItem('groq_api_key') || '');
  const [selectedModel, setSelectedModel] = useState(() => localStorage.getItem('groq_model') || 'llama-3.3-70b-versatile');
  const [expandedJson, setExpandedJson] = useState({});

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const toggleLangChain = () => {
    setUseLangChain(prev => {
      const next = !prev;
      localStorage.setItem('use_langchain', String(next));
      return next;
    });
  };

  const handleSaveSettings = () => {
    localStorage.setItem('groq_api_key', groqApiKey.trim());
    localStorage.setItem('groq_model', selectedModel);
    setShowSettings(false);
  };

  const handleClearChat = () => {
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        text: "Chat cleared. What question would you like to ask?",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ]);
  };

  const toggleJson = (msgId) => {
    setExpandedJson(prev => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  // Format text to strip out ugly raw markdown asterisks and header hashes
  const cleanText = (raw) => {
    if (!raw) return '';
    return raw
      .replace(/\*{1,3}/g, '')
      .replace(/^#{1,6}\s*/gm, '')
      .trim();
  };

  const handleSend = async (e) => {
    if (e) e.preventDefault();
    const text = inputText.trim();
    if (!text || loading) return;

    const userMsgId = `user-${Date.now()}`;
    const userMsg = {
      id: userMsgId,
      role: 'user',
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setInputText('');
    setLoading(true);

    try {
      const response = await sendChatMessage(text, {
        groqApiKey: groqApiKey.trim(),
        model: selectedModel,
        useLangChain
      });

      const assistantMsg = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        text: cleanText(response.reply),
        status: response.status,
        api_call: response.api_call,
        raw_data: response.data,
        missing_fields: response.missing_fields,
        is_langchain: response.is_langchain || useLangChain,
        engine: response.engine,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages(prev => [...prev, assistantMsg]);
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: 'assistant',
          text: `Service connection error: ${err.message}. Please check if the backend is running.`,
          status: 'error',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full lg:w-2/5 h-full flex flex-col bg-white border border-gray-200 rounded-xl shadow-xs overflow-hidden">
      
      {/* Clean Minimal Header with LangChain ON/OFF Toggle */}
      <div className="px-4 py-3 border-b border-gray-200 bg-white flex items-center justify-between shrink-0">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-bold text-gray-900 tracking-tight">Aegis Agent</h3>
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            <span className="px-2 py-0.2 rounded text-[10px] font-semibold bg-orange-50 text-[#FF6C37] border border-orange-200 font-mono">
              Database Access Live
            </span>
          </div>
          <p className="text-[11px] text-gray-500 mt-0.5">
            Natural language interface for university operations
          </p>
        </div>

        <div className="flex items-center gap-1.5">
          {/* LangChain Toggle Button */}
          <button
            id="btn-langchain-toggle"
            type="button"
            onClick={toggleLangChain}
            className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold border transition-all shadow-2xs ${
              useLangChain
                ? 'bg-emerald-50 text-emerald-700 border-emerald-300 ring-1 ring-emerald-400'
                : 'bg-gray-100 text-gray-500 border-gray-300 hover:bg-gray-200'
            }`}
            title="Toggle LangChain System ON or OFF"
          >
            <span className={`w-1.5 h-1.5 rounded-full transition-colors ${useLangChain ? 'bg-emerald-500 animate-pulse' : 'bg-gray-400'}`} />
            <span className="font-mono text-[10px] font-bold">LangChain</span>
            <span className={`px-1 py-0.2 rounded text-[9px] font-mono font-extrabold ${useLangChain ? 'bg-emerald-600 text-white' : 'bg-gray-200 text-gray-700'}`}>
              {useLangChain ? 'ON' : 'OFF'}
            </span>
          </button>

          <button
            onClick={() => setShowSettings(!showSettings)}
            className={`p-1.5 rounded-md text-xs transition-colors ${
              showSettings ? 'bg-orange-50 text-[#FF6C37]' : 'text-gray-500 hover:text-gray-800 hover:bg-gray-100'
            }`}
            title="Model Settings"
          >
            <Settings className="w-4 h-4" />
          </button>

          <button
            onClick={handleClearChat}
            className="p-1.5 rounded-md text-gray-500 hover:text-red-600 hover:bg-gray-100 transition-colors"
            title="Clear Chat History"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Groq Settings Dropdown Tray */}
      {showSettings && (
        <div className="p-3 bg-gray-50 border-b border-gray-200 text-xs space-y-2.5 shrink-0 animate-fadeIn">
          <div className="flex items-center justify-between">
            <span className="font-bold text-gray-800 flex items-center gap-1.5 text-[11px]">
              <Key className="w-3 h-3 text-[#FF6C37]" />
              Inference Configuration
            </span>
            <button onClick={() => setShowSettings(false)} className="text-gray-400 hover:text-gray-600">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          <div>
            <label className="block text-[10px] font-mono text-gray-600 mb-0.5">
              Groq API Key (Optional if configured in environment):
            </label>
            <input
              type="password"
              placeholder="gsk_..."
              value={groqApiKey}
              onChange={(e) => setGroqApiKey(e.target.value)}
              className="w-full px-2.5 py-1 text-xs bg-white border border-gray-300 rounded font-mono focus:outline-none focus:border-[#FF6C37]"
            />
          </div>

          <div>
            <label className="block text-[10px] font-mono text-gray-600 mb-0.5">
              Model:
            </label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="w-full px-2 py-1 text-xs bg-white border border-gray-300 rounded font-mono text-gray-800 focus:outline-none focus:border-[#FF6C37]"
            >
              <option value="llama-3.3-70b-versatile">llama-3.3-70b-versatile</option>
              <option value="llama-3.1-8b-instant">llama-3.1-8b-instant</option>
              <option value="openai/gpt-oss-20b">openai/gpt-oss-20b</option>
            </select>
          </div>

          <div className="flex justify-end pt-1">
            <button
              onClick={handleSaveSettings}
              className="px-3 py-1 bg-[#FF6C37] hover:bg-[#E85B27] text-white rounded text-[11px] font-semibold"
            >
              Save Configuration
            </button>
          </div>
        </div>
      )}

      {/* Messages Stream (Fully Scrollable within container) */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-[#F9FAFB]/70">
        {messages.map((msg) => {
          const isUser = msg.role === 'user';
          return (
            <div
              key={msg.id}
              className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} animate-fadeIn`}
            >
              <div
                className={`max-w-[94%] rounded-xl p-3 text-xs leading-relaxed shadow-2xs ${
                  isUser
                    ? 'bg-[#FF6C37] text-white font-medium rounded-br-none'
                    : msg.status === 'error'
                    ? 'bg-red-50/70 border border-red-300 text-gray-900 rounded-bl-none shadow-xs'
                    : 'bg-white border border-gray-200 text-gray-800 rounded-bl-none'
                }`}
              >
                {/* Assistant Message Header Tag */}
                {!isUser && (
                  <div className="flex items-center justify-between gap-2 mb-1.5 pb-1 border-b border-gray-100">
                    <div className="flex items-center gap-1.5">
                      <span className="text-[10px] font-bold text-gray-600 uppercase tracking-wider">
                        Aegis Agent
                      </span>
                      {msg.is_langchain && (
                        <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-purple-50 text-purple-700 border border-purple-200 font-mono">
                          🦜 LangChain
                        </span>
                      )}
                    </div>
                    {msg.status === 'missing_info' && (
                      <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
                        Information Required
                      </span>
                    )}
                    {msg.status === 'unsupported' && (
                      <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-gray-100 text-gray-600 border border-gray-200">
                        Out of Scope
                      </span>
                    )}
                    {msg.status === 'error' && (
                      <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-red-100 text-red-700 border border-red-300 font-mono">
                        {msg.api_call?.attempts ? `Failed (${msg.api_call.attempts}/3 Attempts)` : 'Schema Drift Error'}
                      </span>
                    )}
                    {msg.status === 'success' && (
                      <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        Verified
                      </span>
                    )}
                  </div>
                )}

                {/* Clean Plain English Body (No markdown cracks / asterisks) */}
                <div className="whitespace-pre-wrap">{cleanText(msg.text)}</div>

                {/* API / SQL Execution Card */}
                {msg.api_call && (
                  <div className="mt-2.5 pt-2 border-t border-gray-100">
                    <div className={`p-2.5 rounded-lg border text-[11px] font-mono ${
                      msg.api_call.status_code >= 400
                        ? 'bg-red-50/80 border-red-200'
                        : 'bg-gray-50 border-gray-200'
                    }`}>
                      <div className="flex items-center justify-between gap-1 mb-1">
                        <div className="flex items-center gap-1.5 overflow-hidden">
                          <span className={`px-1.5 py-0.2 rounded text-[9px] font-bold ${
                            msg.api_call.status_code >= 400
                              ? 'bg-red-200 text-red-800 border border-red-300'
                              : msg.api_call.method === 'SQL' 
                              ? 'bg-blue-100 text-blue-700' 
                              : msg.api_call.method === 'POST' 
                              ? 'bg-orange-100 text-[#FF6C37]' 
                              : 'bg-emerald-100 text-emerald-700'
                          }`}>
                            {msg.api_call.method}
                          </span>
                          <span className="text-gray-800 font-semibold truncate text-[11px]">
                            {msg.api_call.path}
                          </span>
                        </div>
                        <span className={`font-bold text-[10px] shrink-0 ${
                          msg.api_call.status_code >= 400 ? 'text-red-700' : 'text-emerald-600'
                        }`}>
                          {msg.api_call.status_code >= 400 ? `HTTP ${msg.api_call.status_code} (${msg.api_call.attempts || 3} attempts)` : `${msg.api_call.latency_ms} ms`}
                        </span>
                      </div>

                      <div className="text-[10px] text-gray-500 truncate flex items-center gap-1">
                        <Database className="w-3 h-3 text-gray-400" />
                        <span>Source: {msg.api_call.endpoint_name}</span>
                      </div>

                      {/* Collapsible Raw JSON Data */}
                      {msg.raw_data && (
                        <div className="mt-1.5 pt-1.5 border-t border-gray-200/60">
                          <button
                            onClick={() => toggleJson(msg.id)}
                            className="flex items-center gap-1 text-[10px] font-semibold text-[#FF6C37] hover:underline cursor-pointer"
                          >
                            {expandedJson[msg.id] ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                            {expandedJson[msg.id] 
                              ? (msg.status === 'error' ? 'Hide Schema Drift Error' : 'Hide Raw Database Response') 
                              : (msg.status === 'error' ? 'View Schema Drift Error Payload' : 'View Raw Database Response')}
                          </button>

                          {expandedJson[msg.id] && (
                            <pre className="mt-1.5 p-2 bg-gray-900 text-amber-300 rounded text-[10px] overflow-x-auto max-h-40 whitespace-pre-wrap font-mono">
                              {JSON.stringify(msg.raw_data, null, 2)}
                            </pre>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}

              </div>

              <span className="text-[10px] text-gray-400 mt-0.5 px-1 font-mono">
                {msg.timestamp}
              </span>
            </div>
          );
        })}

        {/* Loading Indicator */}
        {loading && (
          <div className="flex items-start gap-2 animate-fadeIn">
            <div className="p-2.5 rounded-xl bg-white border border-gray-200 text-xs shadow-2xs flex items-center gap-2 text-gray-600">
              <span className="w-2 h-2 rounded-full bg-[#FF6C37] animate-ping" />
              <span>Querying university database...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area (Pinned to bottom, never requires scrolling outer page) */}
      <div className="p-3 border-t border-gray-200 bg-white shrink-0">
        <form onSubmit={handleSend} className="flex items-center gap-2">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Ask a question (e.g. Can student 1 graduate?)..."
            disabled={loading}
            className="flex-1 px-3 py-2 text-xs bg-gray-50 border border-gray-300 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:border-[#FF6C37] focus:bg-white focus:ring-1 focus:ring-[#FF6C37]"
          />

          <button
            type="submit"
            disabled={!inputText.trim() || loading}
            className="p-2 rounded-lg bg-[#FF6C37] hover:bg-[#E85B27] active:bg-[#D44C1A] text-white shadow-2xs transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            title="Send Query"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>

    </div>
  );
}
