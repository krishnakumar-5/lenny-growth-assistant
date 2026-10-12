import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { ModelSelector } from './components/ModelSelector';
import { ChatMessage } from './components/ChatMessage';
import { SuggestedPrompts } from './components/SuggestedPrompts';
import { KnowledgeExplorer } from './components/KnowledgeExplorer';
import { CitationInspector } from './components/CitationInspector';
import { Ship30Generator } from './components/Ship30Generator';
import { ArtifactViewer } from './components/ArtifactViewer';
import { ContextPanel } from './components/ContextPanel';
import {
  checkHealth,
  sendChatMessage,
  listSessions,
  getSession,
  deleteSession,
  renameSession,
  ApiError,
} from './services/api';
import {
  ChatMessageItem,
  HealthResponse,
  SourceCitation,
  Ship30Response,
  SessionSummary,
} from './types/api';
import {
  Send,
  Loader2,
  Sparkles,
  SlidersHorizontal,
  ChevronDown,
  ChevronUp,
  PanelRight,
  Plus,
  ShieldCheck,
} from 'lucide-react';

const LOCAL_STORAGE_ACTIVE_SESSION_KEY = 'lenny_growth_active_session_id';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'chat' | 'knowledge' | 'ship30'>('chat');
  const [activeArtifact, setActiveArtifact] = useState<Ship30Response | null>(null);
  const [latestArtifact, setLatestArtifact] = useState<Ship30Response | null>(null);
  const [messages, setMessages] = useState<ChatMessageItem[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionTitle, setSessionTitle] = useState<string>('New Growth Consultation');

  // Session History State
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [loadingSessions, setLoadingSessions] = useState<boolean>(true);
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(true);
  const [contextOpen, setContextOpen] = useState<boolean>(false);
  const [showModelSettings, setShowModelSettings] = useState<boolean>(false);

  // Active turn citations for context panel
  const [activeSources, setActiveSources] = useState<SourceCitation[]>([]);

  // Inference Settings
  const [provider, setProvider] = useState('ollama');
  const [model, setModel] = useState('qwen2.5:3b');
  const [agentFramework, setAgentFramework] = useState('anthropic_tool_agent');

  // System Health
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);

  // Citation Inspector Modal
  const [selectedCitation, setSelectedCitation] = useState<SourceCitation | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // Initial Health Probe
  useEffect(() => {
    let isMounted = true;
    const fetchHealth = async () => {
      try {
        const h = await checkHealth();
        if (isMounted) setHealth(h);
      } catch (err) {
        if (isMounted) setHealth(null);
      } finally {
        if (isMounted) setHealthLoading(false);
      }
    };
    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  // Fetch Session History on Startup
  const refreshSessions = useCallback(async () => {
    try {
      setLoadingSessions(true);
      const sessionList = await listSessions();
      setSessions(sessionList);
      return sessionList;
    } catch (err) {
      console.warn('Failed to load sessions:', err);
      return [];
    } finally {
      setLoadingSessions(false);
    }
  }, []);

  // Load active session from localStorage or latest
  useEffect(() => {
    let isMounted = true;
    const initSessions = async () => {
      const list = await refreshSessions();
      if (!isMounted) return;

      const savedId = localStorage.getItem(LOCAL_STORAGE_ACTIVE_SESSION_KEY);
      const targetId = savedId && list.some((s) => s.id === savedId)
        ? savedId
        : list.length > 0
        ? list[0].id
        : null;

      if (targetId) {
        try {
          const detail = await getSession(targetId);
          if (!isMounted) return;
          setSessionId(detail.id);
          setSessionTitle(detail.title);
          const loadedMsgs: ChatMessageItem[] = detail.messages.map((m) => ({
            id: m.id,
            role: m.role,
            content: m.content,
            timestamp: new Date(m.created_at),
          }));
          setMessages(loadedMsgs);
        } catch (err) {
          console.warn('Could not restore session:', err);
        }
      }
    };

    initSessions();
    return () => {
      isMounted = false;
    };
  }, [refreshSessions]);

  // Select an existing session
  const handleSelectSession = async (targetSessionId: string) => {
    if (loading) return;
    try {
      setLoading(true);
      const detail = await getSession(targetSessionId);
      setSessionId(detail.id);
      setSessionTitle(detail.title);
      localStorage.setItem(LOCAL_STORAGE_ACTIVE_SESSION_KEY, detail.id);

      const loadedMsgs: ChatMessageItem[] = detail.messages.map((m) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        timestamp: new Date(m.created_at),
      }));
      setMessages(loadedMsgs);
      setActiveSources([]);
      setActiveTab('chat');
    } catch (err) {
      console.error('Failed to load session:', err);
    } finally {
      setLoading(false);
    }
  };

  // Start fresh chat session
  const handleNewChat = () => {
    if (loading) return;
    setSessionId(null);
    setSessionTitle('New Growth Consultation');
    setMessages([]);
    setActiveSources([]);
    localStorage.removeItem(LOCAL_STORAGE_ACTIVE_SESSION_KEY);
    setActiveTab('chat');
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  // Delete a session
  const handleDeleteSession = async (targetSessionId: string) => {
    try {
      await deleteSession(targetSessionId);
      setSessions((prev) => prev.filter((s) => s.id !== targetSessionId));
      if (sessionId === targetSessionId) {
        handleNewChat();
      }
    } catch (err) {
      console.error('Failed to delete session:', err);
    }
  };

  // Rename a session
  const handleRenameSession = async (targetSessionId: string, newTitle: string) => {
    try {
      await renameSession(targetSessionId, newTitle);
      setSessions((prev) =>
        prev.map((s) => (s.id === targetSessionId ? { ...s, title: newTitle } : s))
      );
      if (sessionId === targetSessionId) {
        setSessionTitle(newTitle);
      }
    } catch (err) {
      console.error('Failed to rename session:', err);
    }
  };

  // Send Chat Message
  const handleSendMessage = async (customText?: string) => {
    const textToSend = customText || inputMessage;
    if (!textToSend.trim() || loading) return;

    const userMessageItem: ChatMessageItem = {
      id: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
      role: 'user',
      content: textToSend.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessageItem]);
    if (!customText) setInputMessage('');
    setLoading(true);

    try {
      const response = await sendChatMessage({
        message: userMessageItem.content,
        session_id: sessionId || undefined,
        provider,
        model,
        agent_framework: agentFramework,
      });

      setSessionId(response.session_id);
      localStorage.setItem(LOCAL_STORAGE_ACTIVE_SESSION_KEY, response.session_id);

      if (response.sources && response.sources.length > 0) {
        setActiveSources(response.sources);
      }

      const assistantMessageItem: ChatMessageItem = {
        id: crypto.randomUUID ? crypto.randomUUID() : String(Date.now() + 1),
        role: 'assistant',
        content: response.message,
        timestamp: new Date(),
        provider: response.provider,
        model: response.model,
        agent_framework: response.agent_framework,
        sources: response.sources,
        insufficient_evidence: response.insufficient_evidence,
      };

      setMessages((prev) => [...prev, assistantMessageItem]);

      // Refresh sessions to sync titles & timestamps
      const updatedList = await refreshSessions();
      const current = updatedList.find((s) => s.id === response.session_id);
      if (current) {
        setSessionTitle(current.title);
      }
    } catch (err: any) {
      let errorText =
        err.detail ||
        err.message ||
        'An unexpected error occurred while communicating with the assistant.';

      if (err instanceof ApiError) {
        if (err.status === 503) {
          errorText = `Service Unavailable (503): ${err.detail}\n\nTip: For local offline inference, verify that Ollama daemon is running ('ollama serve') or switch Provider to Anthropic in the Inference Settings toolbar above.`;
        } else if (err.status === 504) {
          errorText = `Gateway Timeout (504): The LLM provider or agent runtime timed out while generating a response.`;
        } else if (err.status === 502) {
          errorText = `Bad Gateway (502): ${err.detail}`;
        }
      }

      const errorMessageItem: ChatMessageItem = {
        id: crypto.randomUUID ? crypto.randomUUID() : String(Date.now() + 1),
        role: 'assistant',
        content: errorText,
        timestamp: new Date(),
        isError: true,
      };

      setMessages((prev) => [...prev, errorMessageItem]);
    } finally {
      setLoading(false);
    }
  };

  // Retry turn handler
  const handleRetry = (contentToRetry?: string) => {
    if (contentToRetry) {
      handleSendMessage(contentToRetry);
    } else {
      // Find the last user message
      const lastUser = [...messages].reverse().find((m) => m.role === 'user');
      if (lastUser) {
        handleSendMessage(lastUser.content);
      }
    }
  };

  return (
    <div className="h-screen h-[100dvh] flex flex-col bg-dark-950 text-slate-100 selection:bg-amber-500/30 selection:text-amber-200 overflow-hidden w-full">
      {/* Top Navigation Bar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        health={health}
        healthLoading={healthLoading}
        sessionId={sessionId}
        onResetSession={handleNewChat}
        onToggleSidebar={() => setSidebarOpen((prev) => !prev)}
        onToggleContext={() => setContextOpen((prev) => !prev)}
        isContextOpen={contextOpen}
      />

      {/* Main Workspace Body */}
      <div className="flex-1 min-h-0 flex overflow-hidden relative w-full">
        {/* Left Persistent / Collapsible Navigation Sidebar */}
        <Sidebar
          sessions={sessions}
          activeSessionId={sessionId}
          onSelectSession={handleSelectSession}
          onNewChat={handleNewChat}
          onDeleteSession={handleDeleteSession}
          onRenameSession={handleRenameSession}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          isOpen={sidebarOpen}
          onToggleOpen={() => setSidebarOpen((prev) => !prev)}
          provider={provider}
          model={model}
          databaseStatus={health?.database === 'available' ? 'PostgreSQL' : 'SQLite'}
          loadingSessions={loadingSessions}
        />

        {/* Center Primary Workspace */}
        <main className="flex-1 min-h-0 flex flex-col min-w-0 overflow-hidden relative">
          {activeTab === 'chat' ? (
            <div className="flex-1 min-h-0 flex flex-col max-w-5xl w-full mx-auto px-3 sm:px-6 py-4 overflow-hidden">
              {/* Conversation Header & Toolbar */}
              <div className="flex items-center justify-between pb-3 mb-3 border-b border-white/[0.08] flex-shrink-0">
                <div className="flex items-center space-x-3 min-w-0">
                  <div className="w-8 h-8 rounded-xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-400 flex-shrink-0">
                    <Sparkles className="w-4 h-4" />
                  </div>
                  <div className="min-w-0">
                    <h2 className="text-sm font-bold text-slate-100 truncate tracking-tight">
                      {sessionTitle}
                    </h2>
                    <div className="flex items-center space-x-2 text-[11px] text-slate-400">
                      <span className="flex items-center text-emerald-400 font-medium">
                        <ShieldCheck className="w-3 h-3 mr-1" />
                        Grounded RAG
                      </span>
                      <span>•</span>
                      <span className="font-mono text-slate-400">
                        {provider}/{model}
                      </span>
                      {messages.length > 0 && (
                        <>
                          <span>•</span>
                          <span>{messages.length} messages</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-2 flex-shrink-0">
                  {/* Model Settings Toggle Button */}
                  <button
                    onClick={() => setShowModelSettings((prev) => !prev)}
                    className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-medium border transition-colors ${
                      showModelSettings
                        ? 'bg-amber-500/15 text-amber-300 border-amber-500/40'
                        : 'border-white/[0.08] text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
                    }`}
                    title="Toggle inference model settings"
                  >
                    <SlidersHorizontal className="w-3.5 h-3.5" />
                    <span className="hidden sm:inline">Settings</span>
                    {showModelSettings ? (
                      <ChevronUp className="w-3 h-3" />
                    ) : (
                      <ChevronDown className="w-3 h-3" />
                    )}
                  </button>

                  {/* Context Panel Toggle */}
                  <button
                    onClick={() => setContextOpen((prev) => !prev)}
                    className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-medium border transition-colors ${
                      contextOpen
                        ? 'bg-amber-500/15 text-amber-300 border-amber-500/40'
                        : 'border-white/[0.08] text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
                    }`}
                    title={contextOpen ? 'Hide context panel' : 'Show context & citations'}
                  >
                    <PanelRight className="w-3.5 h-3.5" />
                    <span className="hidden sm:inline">Sources</span>
                    {activeSources.length > 0 && (
                      <span className="w-4 h-4 rounded-full bg-amber-500 text-slate-950 font-bold text-[10px] flex items-center justify-center">
                        {activeSources.length}
                      </span>
                    )}
                  </button>

                  {/* New Chat Button */}
                  <button
                    onClick={handleNewChat}
                    className="p-1.5 rounded-xl border border-white/[0.08] text-slate-400 hover:text-white hover:bg-white/[0.06] transition-colors"
                    title="Start new consultation"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Collapsible Model & Agent Settings */}
              {showModelSettings && (
                <div className="mb-3 flex-shrink-0 animate-slide-in">
                  <ModelSelector
                    provider={provider}
                    setProvider={setProvider}
                    model={model}
                    setModel={setModel}
                    agentFramework={agentFramework}
                    setAgentFramework={setAgentFramework}
                    disabled={loading}
                  />
                </div>
              )}

              {/* Conversation Messages Container */}
              <div className="flex-1 min-h-0 spatial-panel p-4 sm:p-6 overflow-y-auto flex flex-col relative">
                {messages.length === 0 ? (
                  <div className="flex-1 flex flex-col justify-center items-center py-8">
                    <div className="w-14 h-14 rounded-2xl bg-amber-500/15 border border-amber-500/30 text-amber-400 flex items-center justify-center mb-4 shadow-lg shadow-amber-500/10">
                      <Sparkles className="w-7 h-7" />
                    </div>
                    <h2 className="text-xl font-bold text-slate-100 text-center tracking-tight">
                      Grounded Growth Insights
                    </h2>
                    <p className="text-xs sm:text-sm text-slate-400 max-w-lg text-center mt-1.5 mb-8 leading-relaxed">
                      Tactical answers on retention, product-led growth, pricing, and frameworks grounded in 50 verified Lenny's Podcast transcripts.
                    </p>

                    <SuggestedPrompts
                      onSelectPrompt={(p) => handleSendMessage(p)}
                      disabled={loading}
                    />
                  </div>
                ) : (
                  <div className="space-y-4">
                    {messages.map((m) => (
                      <ChatMessage
                        key={m.id}
                        message={m}
                        onSelectCitation={(cit) => {
                          setSelectedCitation(cit);
                          setContextOpen(true);
                        }}
                        onRetry={() => handleRetry(m.content)}
                      />
                    ))}

                    {loading && (
                      <div className="flex items-center space-x-3 my-4 p-3.5 bg-amber-500/10 border border-amber-500/20 rounded-2xl max-w-sm animate-pulse">
                        <div className="w-8 h-8 rounded-xl bg-amber-500 flex items-center justify-center text-slate-950 flex-shrink-0 font-bold shadow-md shadow-amber-500/30">
                          <Loader2 className="w-4 h-4 animate-spin" />
                        </div>
                        <div className="text-xs text-amber-300 font-medium">
                          Searching transcripts and synthesizing grounded response...
                        </div>
                      </div>
                    )}
                    <div ref={messagesEndRef} />
                  </div>
                )}
              </div>

              {/* Bottom Message Composer */}
              <div className="mt-3 flex-shrink-0">
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSendMessage();
                  }}
                  className="relative flex items-center spatial-panel p-1.5 border border-white/[0.1] shadow-2xl focus-within:border-amber-500/60 focus-within:ring-1 focus-within:ring-amber-500/50 transition-all"
                >
                  <textarea
                    ref={textareaRef}
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSendMessage();
                      }
                    }}
                    placeholder="Ask a question about growth, retention, PLG, or frameworks... (Press Enter to send, Shift+Enter for newline)"
                    rows={2}
                    disabled={loading}
                    className="w-full resize-none bg-transparent py-2.5 pl-3.5 pr-14 text-sm text-slate-100 placeholder-slate-500 focus:outline-none disabled:opacity-50"
                  />
                  <button
                    type="submit"
                    disabled={loading || !inputMessage.trim()}
                    className="absolute right-3.5 bottom-3.5 p-2 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold transition-all disabled:opacity-30 disabled:hover:from-amber-500 shadow-md shadow-amber-500/20"
                    title="Send message"
                  >
                    {loading ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Send className="w-4 h-4" />
                    )}
                  </button>
                </form>
                <div className="flex items-center justify-between mt-2 px-1 text-[11px] text-slate-500">
                  <span className="flex items-center">
                    <ShieldCheck className="w-3 h-3 text-emerald-400 mr-1" />
                    All answers strictly grounded in indexed transcript chunks.
                  </span>
                  {sessionId && (
                    <span className="font-mono text-slate-500">
                      ID: {sessionId.slice(0, 8)}...
                    </span>
                  )}
                </div>
              </div>
            </div>
          ) : activeTab === 'knowledge' ? (
            <div className="flex-1 min-h-0 overflow-y-auto">
              <KnowledgeExplorer onBackToChat={() => setActiveTab('chat')} />
            </div>
          ) : (
            <div className="flex-1 min-h-0 overflow-y-auto">
              <Ship30Generator
                provider={provider}
                model={model}
                onOpenArtifact={(art) => {
                  setActiveArtifact(art);
                  setLatestArtifact(art);
                }}
              />
            </div>
          )}
        </main>

        {/* Right Collapsible Context & Provenance Panel */}
        <ContextPanel
          isOpen={contextOpen}
          onClose={() => setContextOpen(false)}
          sources={activeSources}
          onSelectCitation={(cit) => setSelectedCitation(cit)}
          latestArtifact={latestArtifact}
          onOpenArtifact={(art) => setActiveArtifact(art)}
        />
      </div>

      {/* Citation Inspector Modal */}
      <CitationInspector
        citation={selectedCitation}
        onClose={() => setSelectedCitation(null)}
      />

      {/* Secure Artifact Viewer Modal */}
      <ArtifactViewer
        artifact={activeArtifact}
        onClose={() => setActiveArtifact(null)}
      />
    </div>
  );
};

export default App;
