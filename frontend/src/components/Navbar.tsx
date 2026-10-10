import React from 'react';
import { HealthResponse } from '../types/api';
import { Activity, BookOpen, MessageSquare, RotateCcw, ShieldCheck, AlertTriangle, Feather } from 'lucide-react';

interface NavbarProps {
  activeTab: 'chat' | 'knowledge' | 'ship30';
  setActiveTab: (tab: 'chat' | 'knowledge' | 'ship30') => void;
  health: HealthResponse | null;
  healthLoading: boolean;
  sessionId: string | null;
  onResetSession: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  health,
  healthLoading,
  sessionId,
  onResetSession,
}) => {
  const isHealthy = health?.status === 'healthy' || health?.status === 'running';
  const isDbAvailable = health?.database === 'available';

  return (
    <header className="border-b border-slate-200 bg-white/80 backdrop-blur sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-500 to-amber-600 flex items-center justify-center text-white shadow-md shadow-amber-500/20">
            <span className="font-bold text-lg tracking-tight">L</span>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="font-semibold text-slate-900 tracking-tight text-base sm:text-lg">
                The Lenny Growth Assistant
              </h1>
              <span className="hidden sm:inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-800 border border-amber-200">
                Grounded RAG
              </span>
            </div>
            <p className="text-xs text-slate-500 hidden sm:block">
              Product & Growth insights operationalized from verified podcast transcripts
            </p>
          </div>
        </div>

        {/* Center Navigation Tabs */}
        <div className="flex items-center bg-slate-100 p-1 rounded-lg">
          <button
            onClick={() => setActiveTab('chat')}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'chat'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <MessageSquare className="w-4 h-4" />
            <span>Chat</span>
          </button>
          <button
            onClick={() => setActiveTab('knowledge')}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'knowledge'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <BookOpen className="w-4 h-4" />
            <span>Transcripts</span>
          </button>
          <button
            onClick={() => setActiveTab('ship30')}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'ship30'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Feather className="w-4 h-4" />
            <span>Ship 30 Essays</span>
          </button>
        </div>

        {/* Right Status & Controls */}
        <div className="flex items-center space-x-3">
          {/* Health Pill */}
          <div className="hidden md:flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium border bg-slate-50">
            {healthLoading ? (
              <span className="flex items-center text-slate-500">
                <Activity className="w-3.5 h-3.5 mr-1 animate-spin text-slate-400" />
                Connecting...
              </span>
            ) : isHealthy ? (
              <span className="flex items-center text-emerald-700">
                <ShieldCheck className="w-3.5 h-3.5 mr-1 text-emerald-600" />
                API v{health?.version || '1.0'}
                {isDbAvailable ? (
                  <span className="ml-1 text-emerald-600 font-normal">(Postgres Online)</span>
                ) : (
                  <span className="ml-1 text-amber-600 font-normal">(SQLite/Offline DB)</span>
                )}
              </span>
            ) : (
              <span className="flex items-center text-rose-700">
                <AlertTriangle className="w-3.5 h-3.5 mr-1 text-rose-600" />
                API Offline
              </span>
            )}
          </div>

          {/* Reset Session */}
          {sessionId && (
            <button
              onClick={onResetSession}
              title="Reset conversation session"
              className="flex items-center space-x-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-slate-200 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">New Session</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
