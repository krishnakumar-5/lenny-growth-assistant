import React from 'react';
import { HealthResponse } from '../types/api';
import {
  Activity,
  BookOpen,
  MessageSquare,
  RotateCcw,
  ShieldCheck,
  AlertTriangle,
  Feather,
  Menu,
  PanelRight,
} from 'lucide-react';

interface NavbarProps {
  activeTab: 'chat' | 'knowledge' | 'ship30';
  setActiveTab: (tab: 'chat' | 'knowledge' | 'ship30') => void;
  health: HealthResponse | null;
  healthLoading: boolean;
  sessionId: string | null;
  onResetSession: () => void;
  onToggleSidebar?: () => void;
  onToggleContext?: () => void;
  isContextOpen?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  health,
  healthLoading,
  sessionId,
  onResetSession,
  onToggleSidebar,
  onToggleContext,
  isContextOpen = false,
}) => {
  const isHealthy = health?.status === 'healthy' || health?.status === 'running';
  const isDbAvailable = health?.database === 'available';

  return (
    <header className="border-b border-white/[0.08] bg-dark-900/90 backdrop-blur-xl sticky top-0 z-30 flex-shrink-0 w-full">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Left: Mobile Sidebar Trigger & Brand */}
        <div className="flex items-center space-x-3">
          {onToggleSidebar && (
            <button
              onClick={onToggleSidebar}
              className="p-2 -ml-2 rounded-xl text-slate-400 hover:text-slate-100 hover:bg-white/[0.06] transition-colors lg:hidden"
              title="Toggle sidebar"
            >
              <Menu className="w-5 h-5" />
            </button>
          )}

          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-amber-500 via-amber-600 to-orange-600 flex items-center justify-center text-white shadow-lg shadow-amber-500/20 ring-1 ring-white/20">
              <span className="font-bold text-base tracking-tight">L</span>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="font-bold text-slate-100 tracking-tight text-sm sm:text-base">
                  The Lenny Growth Assistant
                </h1>
                <span className="hidden sm:inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold bg-amber-500/15 text-amber-300 border border-amber-500/30">
                  Grounded RAG
                </span>
              </div>
              <p className="text-[11px] text-slate-400 hidden md:block">
                Product & Growth insights operationalized from verified podcast transcripts
              </p>
            </div>
          </div>
        </div>

        {/* Center: Navigation Tabs */}
        <div className="flex items-center bg-dark-950/80 p-1 rounded-xl border border-white/[0.08]">
          <button
            onClick={() => setActiveTab('chat')}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'chat'
                ? 'bg-amber-500 text-slate-950 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>Chat</span>
          </button>
          <button
            onClick={() => setActiveTab('knowledge')}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'knowledge'
                ? 'bg-amber-500 text-slate-950 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>Transcripts</span>
          </button>
          <button
            onClick={() => setActiveTab('ship30')}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'ship30'
                ? 'bg-amber-500 text-slate-950 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
            }`}
          >
            <Feather className="w-3.5 h-3.5" />
            <span>Ship 30 Essays</span>
          </button>
        </div>

        {/* Right Status & Controls */}
        <div className="flex items-center space-x-2.5">
          {/* Health Pill */}
          <div className="hidden md:flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium border border-white/[0.08] bg-dark-950/70">
            {healthLoading ? (
              <span className="flex items-center text-slate-400">
                <Activity className="w-3 h-3 mr-1 animate-spin text-amber-500" />
                Connecting...
              </span>
            ) : isHealthy ? (
              <span className="flex items-center text-emerald-400">
                <ShieldCheck className="w-3.5 h-3.5 mr-1 text-emerald-400" />
                API v{health?.version || '1.0'}
                {isDbAvailable ? (
                  <span className="ml-1 text-emerald-400/80 font-normal">(Postgres Online)</span>
                ) : (
                  <span className="ml-1 text-amber-400/90 font-normal">(SQLite DB)</span>
                )}
              </span>
            ) : (
              <span className="flex items-center text-rose-400">
                <AlertTriangle className="w-3.5 h-3.5 mr-1 text-rose-400" />
                API Offline
              </span>
            )}
          </div>

          {/* Reset Session */}
          {sessionId && (
            <button
              onClick={onResetSession}
              title="Reset conversation session"
              className="flex items-center space-x-1 px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-300 hover:text-slate-100 hover:bg-white/[0.08] border border-white/[0.1] transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">New Session</span>
            </button>
          )}

          {/* Context Panel Toggle */}
          {onToggleContext && (
            <button
              onClick={onToggleContext}
              className={`p-2 rounded-xl border transition-colors ${
                isContextOpen
                  ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.06] border-white/[0.08]'
              }`}
              title={isContextOpen ? 'Close context panel' : 'Open context & citations panel'}
            >
              <PanelRight className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
