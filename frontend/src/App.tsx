import React, { useState, useEffect, useRef } from 'react';
import { Navbar } from './components/Navbar';
import { ModelSelector } from './components/ModelSelector';
import { ChatMessage } from './components/ChatMessage';
import { SuggestedPrompts } from './components/SuggestedPrompts';
import { KnowledgeExplorer } from './components/KnowledgeExplorer';
import { CitationInspector } from './components/CitationInspector';
import { Ship30Generator } from './components/Ship30Generator';
import { ArtifactViewer } from './components/ArtifactViewer';
import { checkHealth, sendChatMessage, ApiError } from './services/api';
import { ChatMessageItem, HealthResponse, SourceCitation, Ship30Response } from './types/api';
import { Send, Loader2, Sparkles } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'chat' | 'knowledge' | 'ship30'>('chat');
  const [activeArtifact, setActiveArtifact] = useState<Ship30Response | null>(null);
  const [messages, setMessages] = useState<ChatMessageItem[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

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

  const handleResetSession = () => {
    setSessionId(null);
    setMessages([]);
  };

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
    } catch (err: any) {
      let errorText = err.detail || err.message || 'An unexpected error occurred while communicating with the assistant.';
      
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

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-800">
      {/* Top Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        health={health}
        healthLoading={healthLoading}
        sessionId={sessionId}
        onResetSession={handleResetSession}
      />

      {/* Main Workspace Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 flex flex-col">
        {activeTab === 'chat' ? (
          <div className="flex-1 flex flex-col max-w-4xl w-full mx-auto">
            {/* Model & Agent Settings Bar */}
            <div className="mb-4">
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

            {/* Conversation Messages Container */}
            <div className="flex-1 bg-white border border-slate-200 rounded-2xl shadow-sm p-4 sm:p-6 overflow-y-auto min-h-[460px] flex flex-col">
              {messages.length === 0 ? (
                <div className="flex-1 flex flex-col justify-center items-center py-6">
                  <div className="w-12 h-12 rounded-2xl bg-amber-100 text-amber-700 flex items-center justify-center mb-3">
                    <Sparkles className="w-6 h-6" />
                  </div>
                  <h2 className="text-lg font-bold text-slate-900 text-center">
                    Grounded Growth Insights
                  </h2>
                  <p className="text-xs text-slate-500 max-w-md text-center mt-1 mb-6">
                    Ask tactical questions regarding retention, product-led growth, pricing, and frameworks from verified Lenny's Podcast transcripts.
                  </p>

                  <SuggestedPrompts
                    onSelectPrompt={(p) => handleSendMessage(p)}
                    disabled={loading}
                  />
                </div>
              ) : (
                <div className="space-y-2">
                  {messages.map((m) => (
                    <ChatMessage
                      key={m.id}
                      message={m}
                      onSelectCitation={(cit) => setSelectedCitation(cit)}
                    />
                  ))}

                  {loading && (
                    <div className="flex items-center space-x-3 my-4 p-3 bg-amber-50/60 border border-amber-200/50 rounded-2xl max-w-sm">
                      <div className="w-8 h-8 rounded-full bg-amber-500 flex items-center justify-center text-white flex-shrink-0 animate-pulse">
                        <Loader2 className="w-4 h-4 animate-spin" />
                      </div>
                      <div className="text-xs text-amber-900 font-medium">
                        Searching transcripts and synthesizing grounded response...
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
              )}
            </div>

            {/* Input Bar */}
            <div className="mt-4">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSendMessage();
                }}
                className="relative flex items-center"
              >
                <textarea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage();
                    }
                  }}
                  placeholder="Ask a question about growth, retention, PLG, or frameworks... (Press Enter to send)"
                  rows={2}
                  disabled={loading}
                  className="w-full resize-none rounded-2xl border border-slate-200 bg-white py-3 pl-4 pr-14 text-sm shadow-sm focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 disabled:opacity-50"
                />
                <button
                  type="submit"
                  disabled={loading || !inputMessage.trim()}
                  className="absolute right-3 p-2 rounded-xl bg-amber-600 text-white hover:bg-amber-700 transition-colors disabled:opacity-40 disabled:hover:bg-amber-600 shadow-sm"
                  title="Send message"
                >
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                </button>
              </form>
              <div className="flex items-center justify-between mt-2 px-1 text-[11px] text-slate-400">
                <span>All answers are strictly grounded in indexed transcript chunks.</span>
                {sessionId && <span className="font-mono">Session: {sessionId.slice(0, 8)}...</span>}
              </div>
            </div>
          </div>
        ) : activeTab === 'knowledge' ? (
          <KnowledgeExplorer />
        ) : (
          <Ship30Generator
            provider={provider}
            model={model}
            onOpenArtifact={(art) => setActiveArtifact(art)}
          />
        )}
      </main>

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
