import React, { useState, useMemo } from 'react';
import { SessionSummary } from '../types/api';
import {
  MessageSquare,
  Plus,
  Search,
  BookOpen,
  Feather,
  Trash2,
  Edit2,
  Check,
  X,
  ChevronLeft,
  ChevronRight,
  Cpu,
  Clock,
  Layers,
} from 'lucide-react';

interface SidebarProps {
  sessions: SessionSummary[];
  activeSessionId: string | null;
  onSelectSession: (sessionId: string) => void;
  onNewChat: () => void;
  onDeleteSession: (sessionId: string) => void;
  onRenameSession: (sessionId: string, newTitle: string) => void;
  activeTab: 'chat' | 'knowledge' | 'ship30';
  setActiveTab: (tab: 'chat' | 'knowledge' | 'ship30') => void;
  isOpen: boolean;
  onToggleOpen: () => void;
  provider: string;
  model: string;
  databaseStatus?: string;
  loadingSessions?: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
  onDeleteSession,
  onRenameSession,
  activeTab,
  setActiveTab,
  isOpen,
  onToggleOpen,
  provider,
  model,
  databaseStatus,
  loadingSessions = false,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
  const [touchStartX, setTouchStartX] = useState<number | null>(null);

  // Filter sessions by search query
  const filteredSessions = useMemo(() => {
    if (!searchQuery.trim()) return sessions;
    const q = searchQuery.toLowerCase();
    return sessions.filter(
      (s) =>
        s.title.toLowerCase().includes(q) ||
        (s.last_message && s.last_message.toLowerCase().includes(q))
    );
  }, [sessions, searchQuery]);

  // Group sessions by date
  const groupedSessions = useMemo(() => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
    const yesterday = today - 86400000;
    const lastWeek = today - 7 * 86400000;

    const groups: { [key: string]: SessionSummary[] } = {
      Today: [],
      Yesterday: [],
      'Previous 7 Days': [],
      Older: [],
    };

    filteredSessions.forEach((session) => {
      const sessionDate = new Date(session.updated_at || session.created_at).getTime();
      if (sessionDate >= today) {
        groups['Today'].push(session);
      } else if (sessionDate >= yesterday) {
        groups['Yesterday'].push(session);
      } else if (sessionDate >= lastWeek) {
        groups['Previous 7 Days'].push(session);
      } else {
        groups['Older'].push(session);
      }
    });

    return groups;
  }, [filteredSessions]);

  const handleStartRename = (session: SessionSummary, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingSessionId(session.id);
    setEditingTitle(session.title);
  };

  const handleSaveRename = (sessionId: string, e: React.FormEvent) => {
    e.preventDefault();
    if (editingTitle.trim()) {
      onRenameSession(sessionId, editingTitle.trim());
    }
    setEditingSessionId(null);
  };

  const handleCancelRename = (e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingSessionId(null);
  };

  const handleDelete = (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    onDeleteSession(sessionId);
  };

  // Touch swipe support for mobile drawer
  const handleTouchStart = (e: React.TouchEvent) => {
    setTouchStartX(e.touches[0].clientX);
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    if (touchStartX === null) return;
    const touchEndX = e.changedTouches[0].clientX;
    const diff = touchEndX - touchStartX;
    if (diff < -50 && isOpen) {
      // Swiped left: close drawer
      onToggleOpen();
    }
    setTouchStartX(null);
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onToggleOpen}
          className="fixed inset-0 bg-black/70 backdrop-blur-sm z-40 lg:hidden transition-opacity duration-300"
          aria-hidden="true"
        />
      )}

      {/* Sidebar Container */}
      <aside
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
        className={`fixed lg:static top-0 bottom-0 left-0 z-50 flex flex-col h-full bg-dark-900 border-r border-white/[0.08] text-slate-200 transition-all duration-300 ease-in-out shadow-2xl lg:shadow-none overflow-hidden ${
          isOpen ? 'w-72 sm:w-80 translate-x-0' : '-translate-x-full lg:translate-x-0 lg:w-16'
        }`}
      >
        {/* Header & Logo */}
        <div className="h-16 px-4 flex items-center justify-between border-b border-white/[0.08] flex-shrink-0 bg-dark-950/40">
          <div className="flex items-center space-x-3 overflow-hidden">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-amber-500 via-amber-600 to-orange-600 flex items-center justify-center text-white shadow-lg shadow-amber-500/20 flex-shrink-0 ring-1 ring-white/20">
              <span className="font-black text-base tracking-tight">L</span>
            </div>
            {isOpen && (
              <div className="truncate animate-fade-in">
                <span className="font-bold text-sm text-slate-100 tracking-tight block truncate">
                  Lenny Growth AI
                </span>
                <span className="text-[10px] text-amber-400/90 font-medium tracking-wide flex items-center">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mr-1.5 animate-pulse" />
                  WORKSPACE
                </span>
              </div>
            )}
          </div>

          {/* Desktop Toggle Button */}
          <button
            onClick={onToggleOpen}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-white/[0.06] transition-colors focus:outline-none focus:ring-1 focus:ring-amber-500/50"
            title={isOpen ? 'Collapse sidebar' : 'Expand sidebar'}
          >
            {isOpen ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </button>
        </div>

        {/* Primary Action: New Chat */}
        <div className="p-3 border-b border-white/[0.06] flex-shrink-0">
          <button
            onClick={() => {
              onNewChat();
              setActiveTab('chat');
            }}
            className={`w-full flex items-center justify-center space-x-2 py-2.5 px-3 rounded-xl font-medium text-xs transition-all duration-200 shadow-md ${
              isOpen
                ? 'bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-orange-600 text-white shadow-amber-500/20 hover:shadow-amber-500/30 spatial-card'
                : 'bg-amber-500/20 text-amber-400 hover:bg-amber-500/30'
            }`}
            title="Start a new chat session"
          >
            <Plus className="w-4 h-4 flex-shrink-0" />
            {isOpen && <span>New Conversation</span>}
          </button>
        </div>

        {/* Navigation Tabs (Chat / Transcripts / Ship 30) */}
        <div className="p-2 border-b border-white/[0.06] flex-shrink-0 space-y-1">
          <button
            onClick={() => setActiveTab('chat')}
            className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
              activeTab === 'chat'
                ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
            }`}
            title="Chat Workspace"
          >
            <MessageSquare className="w-4 h-4 text-amber-500 flex-shrink-0" />
            {isOpen && <span>Grounded Chat</span>}
          </button>
          <button
            onClick={() => setActiveTab('knowledge')}
            className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
              activeTab === 'knowledge'
                ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
            }`}
            title="Transcript Knowledge Explorer"
          >
            <BookOpen className="w-4 h-4 text-amber-500 flex-shrink-0" />
            {isOpen && <span>Transcript Explorer</span>}
          </button>
          <button
            onClick={() => setActiveTab('ship30')}
            className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
              activeTab === 'ship30'
                ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
            }`}
            title="Ship 30 Essay Studio"
          >
            <Feather className="w-4 h-4 text-amber-500 flex-shrink-0" />
            {isOpen && <span>Ship 30 Essay Studio</span>}
          </button>
        </div>

        {/* Collapsible Session History Area */}
        {isOpen ? (
          <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
            {/* Search Bar */}
            <div className="p-3 pb-2 flex-shrink-0">
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search past conversations..."
                  className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-dark-950/60 border border-white/[0.08] text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/50 transition-colors"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="absolute right-2.5 top-2.5 text-slate-500 hover:text-slate-300"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>

            {/* Session Items List */}
            <div className="flex-1 min-h-0 overflow-y-auto px-2 py-1 space-y-4">
              {loadingSessions ? (
                <div className="p-4 text-center text-xs text-slate-500 space-y-2">
                  <div className="w-5 h-5 border-2 border-amber-500/30 border-t-amber-500 rounded-full animate-spin mx-auto" />
                  <span>Loading conversations...</span>
                </div>
              ) : filteredSessions.length === 0 ? (
                <div className="p-6 text-center text-xs text-slate-500">
                  {searchQuery ? (
                    <p>No conversations matched "{searchQuery}"</p>
                  ) : (
                    <div className="space-y-1.5">
                      <Clock className="w-5 h-5 mx-auto text-slate-600" />
                      <p className="font-medium text-slate-400">No chat history yet</p>
                      <p className="text-[11px] text-slate-500">
                        Start a conversation to automatically save it here.
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                Object.entries(groupedSessions).map(([groupTitle, groupSessions]) => {
                  if (groupSessions.length === 0) return null;
                  return (
                    <div key={groupTitle} className="space-y-1">
                      <div className="px-2 text-[10px] font-bold uppercase tracking-wider text-slate-500">
                        {groupTitle}
                      </div>
                      {groupSessions.map((session) => {
                        const isActive = session.id === activeSessionId;
                        const isEditing = session.id === editingSessionId;

                        return (
                          <div
                            key={session.id}
                            onClick={() => {
                              onSelectSession(session.id);
                              setActiveTab('chat');
                            }}
                            className={`group relative rounded-xl px-2.5 py-2 text-xs transition-all duration-150 cursor-pointer border ${
                              isActive
                                ? 'bg-amber-500/10 border-amber-500/30 text-amber-200 shadow-sm shadow-amber-500/5'
                                : 'border-transparent text-slate-300 hover:bg-white/[0.04] hover:text-slate-100'
                            }`}
                          >
                            {isEditing ? (
                              <form
                                onSubmit={(e) => handleSaveRename(session.id, e)}
                                className="flex items-center space-x-1"
                                onClick={(e) => e.stopPropagation()}
                              >
                                <input
                                  type="text"
                                  value={editingTitle}
                                  onChange={(e) => setEditingTitle(e.target.value)}
                                  autoFocus
                                  className="flex-1 bg-dark-950 border border-amber-500/60 rounded px-1.5 py-0.5 text-xs text-slate-100 focus:outline-none"
                                />
                                <button
                                  type="submit"
                                  className="p-1 text-emerald-400 hover:text-emerald-300"
                                  title="Save title"
                                >
                                  <Check className="w-3.5 h-3.5" />
                                </button>
                                <button
                                  type="button"
                                  onClick={handleCancelRename}
                                  className="p-1 text-slate-400 hover:text-slate-200"
                                  title="Cancel"
                                >
                                  <X className="w-3.5 h-3.5" />
                                </button>
                              </form>
                            ) : (
                              <div className="flex items-start justify-between space-x-2">
                                <div className="flex-1 min-w-0">
                                  <div className="font-medium truncate">{session.title}</div>
                                  {session.last_message && (
                                    <div className="text-[11px] text-slate-500 truncate mt-0.5">
                                      {session.last_message}
                                    </div>
                                  )}
                                </div>

                                {/* Actions on Hover */}
                                <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                  <button
                                    onClick={(e) => handleStartRename(session, e)}
                                    className="p-1 text-slate-400 hover:text-slate-200 hover:bg-white/[0.08] rounded"
                                    title="Rename conversation"
                                  >
                                    <Edit2 className="w-3 h-3" />
                                  </button>
                                  <button
                                    onClick={(e) => handleDelete(session.id, e)}
                                    className="p-1 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded"
                                    title="Delete conversation"
                                  >
                                    <Trash2 className="w-3 h-3" />
                                  </button>
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  );
                })
              )}
            </div>
          </div>
        ) : (
          /* Mini Collapsed Icons */
          <div className="flex-1 min-h-0 flex flex-col items-center py-4 space-y-3 overflow-hidden">
            <div className="w-8 h-8 rounded-lg bg-white/[0.04] flex items-center justify-center text-slate-400">
              <Layers className="w-4 h-4" />
            </div>
          </div>
        )}

        {/* Compact Footer Status Indicator */}
        <div className="p-3 border-t border-white/[0.08] bg-dark-950/60 flex-shrink-0">
          <div className="flex items-center space-x-2 text-[11px] text-slate-400">
            <Cpu className="w-3.5 h-3.5 text-amber-500 flex-shrink-0" />
            {isOpen ? (
              <div className="truncate flex-1">
                <span className="text-slate-300 font-medium truncate block">{model}</span>
                <span className="text-[10px] text-slate-500 truncate block">
                  {provider} • {databaseStatus || 'Local DB'}
                </span>
              </div>
            ) : null}
          </div>
        </div>
      </aside>
    </>
  );
};
