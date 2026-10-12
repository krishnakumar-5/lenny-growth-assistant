import React, { useState } from 'react';
import { ChatMessageItem, SourceCitation } from '../types/api';
import {
  Bot,
  User,
  Bookmark,
  AlertCircle,
  AlertTriangle,
  Copy,
  Check,
  RotateCw,
} from 'lucide-react';

interface ChatMessageProps {
  message: ChatMessageItem;
  onSelectCitation: (citation: SourceCitation) => void;
  onRetry?: (content: string) => void;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({
  message,
  onSelectCitation,
  onRetry,
}) => {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Format assistant response text with clean markdown-like formatting
  const renderFormattedContent = (content: string) => {
    const lines = content.split('\n');
    return lines.map((line, idx) => {
      const trimmed = line.trim();

      // Bullets
      if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
        return (
          <li key={idx} className="ml-5 list-disc my-1.5 text-slate-300">
            {formatInlineText(trimmed.substring(2))}
          </li>
        );
      }
      // Numbered lists
      const numMatch = trimmed.match(/^(\d+)\.\s+(.*)/);
      if (numMatch) {
        return (
          <li key={idx} className="ml-5 list-decimal my-1.5 text-slate-300">
            {formatInlineText(numMatch[2])}
          </li>
        );
      }
      // Headers
      if (trimmed.startsWith('### ')) {
        return (
          <h4 key={idx} className="font-bold text-slate-100 mt-4 mb-1.5 text-sm tracking-tight">
            {trimmed.substring(4)}
          </h4>
        );
      }
      if (trimmed.startsWith('## ')) {
        return (
          <h3 key={idx} className="font-bold text-amber-200 mt-5 mb-2 text-base tracking-tight border-b border-white/[0.06] pb-1">
            {trimmed.substring(3)}
          </h3>
        );
      }
      if (trimmed.startsWith('# ')) {
        return (
          <h2 key={idx} className="font-extrabold text-amber-100 mt-5 mb-2.5 text-lg tracking-tight">
            {trimmed.substring(2)}
          </h2>
        );
      }
      // Empty line
      if (!trimmed) {
        return <div key={idx} className="h-2" />;
      }
      // Standard paragraph
      return (
        <p key={idx} className="my-1.5 leading-relaxed text-slate-300">
          {formatInlineText(line)}
        </p>
      );
    });
  };

  // Inline formatting helper for **bold** and `code`
  const formatInlineText = (text: string) => {
    const parts = text.split(/(\*\*.*?\*\*|`.*?`)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return (
          <strong key={i} className="font-semibold text-slate-100">
            {part.slice(2, -2)}
          </strong>
        );
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return (
          <code
            key={i}
            className="bg-dark-950/80 text-amber-300 text-[11px] px-1.5 py-0.5 rounded font-mono border border-white/[0.08]"
          >
            {part.slice(1, -1)}
          </code>
        );
      }
      return part;
    });
  };

  return (
    <div className={`flex w-full my-4 ${isUser ? 'justify-end' : 'justify-start'} animate-fade-in`}>
      <div
        className={`flex max-w-3xl space-x-3 ${
          isUser ? 'flex-row-reverse space-x-reverse' : 'flex-row'
        }`}
      >
        {/* Avatar */}
        <div
          className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 text-white shadow-md text-xs font-medium ring-1 ${
            isUser
              ? 'bg-slate-800 text-slate-200 ring-white/10'
              : message.isError
              ? 'bg-rose-900 text-rose-200 ring-rose-500/30'
              : 'bg-gradient-to-tr from-amber-500 via-amber-600 to-orange-600 text-white ring-amber-400/30 shadow-amber-500/10'
          }`}
        >
          {isUser ? (
            <User className="w-4 h-4" />
          ) : message.isError ? (
            <AlertTriangle className="w-4 h-4" />
          ) : (
            <Bot className="w-4 h-4" />
          )}
        </div>

        {/* Message Bubble & Meta */}
        <div className="flex flex-col space-y-1.5 min-w-0">
          <div
            className={`rounded-2xl px-4 py-3.5 text-sm shadow-depth ${
              isUser
                ? 'bg-gradient-to-r from-amber-600 to-amber-700 text-white rounded-tr-none border border-amber-500/30'
                : message.isError
                ? 'bg-rose-950/40 text-rose-200 border border-rose-800/60 rounded-tl-none'
                : 'bg-dark-900/90 text-slate-200 border border-white/[0.08] rounded-tl-none spatial-panel'
            }`}
          >
            {/* Insufficient Evidence Warning Banner */}
            {message.insufficient_evidence && (
              <div className="mb-2.5 p-2.5 bg-amber-950/50 border border-amber-500/30 rounded-xl flex items-center space-x-2 text-xs text-amber-200">
                <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0" />
                <span>
                  <strong>Strict Grounding Active:</strong> No transcript evidence found; refusing speculation.
                </span>
              </div>
            )}

            {/* Message Body */}
            <div className={`leading-relaxed text-sm ${isUser ? 'whitespace-pre-wrap' : ''}`}>
              {isUser ? message.content : renderFormattedContent(message.content)}
            </div>

            {/* Grounding Sources / Citations List */}
            {message.sources && message.sources.length > 0 && (
              <div className="mt-3.5 pt-3 border-t border-white/[0.08]">
                <div className="text-xs font-semibold text-slate-400 mb-2 flex items-center space-x-1.5">
                  <Bookmark className="w-3.5 h-3.5 text-amber-400" />
                  <span>Grounding Sources ({message.sources.length}):</span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {message.sources.map((src, idx) => (
                    <button
                      key={src.chunk_id || idx}
                      onClick={() => onSelectCitation(src)}
                      className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-dark-950/80 text-amber-300 border border-amber-500/30 hover:bg-amber-500/15 hover:border-amber-400/50 transition-all duration-150 shadow-sm"
                      title={`Inspect transcript excerpt from ${src.transcript_title}`}
                    >
                      <Bookmark className="w-3 h-3 text-amber-400 flex-shrink-0" />
                      <span className="truncate max-w-[200px]">{src.transcript_title}</span>
                      <span className="text-[10px] text-amber-400 bg-amber-500/20 px-1 py-0.2 rounded font-mono">
                        #{src.chunk_index}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Assistant Action Bar (Copy & Retry) */}
            {!isUser && !message.isError && (
              <div className="mt-2.5 pt-2 border-t border-white/[0.04] flex items-center justify-between text-[11px] text-slate-400">
                <div className="flex items-center space-x-2">
                  <button
                    onClick={handleCopy}
                    className="flex items-center space-x-1 hover:text-amber-300 transition-colors p-1 rounded"
                    title="Copy response"
                  >
                    {copied ? (
                      <>
                        <Check className="w-3 h-3 text-emerald-400" />
                        <span className="text-emerald-400">Copied</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3 h-3" />
                        <span>Copy</span>
                      </>
                    )}
                  </button>
                  {onRetry && (
                    <button
                      onClick={() => onRetry(message.content)}
                      className="flex items-center space-x-1 hover:text-amber-300 transition-colors p-1 rounded"
                      title="Retry response"
                    >
                      <RotateCw className="w-3 h-3" />
                      <span>Retry</span>
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Turn Metadata Footer */}
          <div
            className={`flex items-center space-x-2 text-[11px] text-slate-500 px-1 ${
              isUser ? 'justify-end' : 'justify-start'
            }`}
          >
            <span>
              {new Date(message.timestamp).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
              })}
            </span>
            {!isUser && message.provider && (
              <>
                <span>•</span>
                <span className="font-mono text-slate-400">
                  {message.provider}/{message.model}
                </span>
              </>
            )}
            {!isUser && message.agent_framework && (
              <>
                <span>•</span>
                <span className="px-1.5 py-0.2 rounded bg-dark-950/80 text-amber-400 font-mono text-[10px] border border-white/[0.06]">
                  {message.agent_framework}
                </span>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
