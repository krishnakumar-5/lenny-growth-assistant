import React from 'react';
import { ChatMessageItem, SourceCitation } from '../types/api';
import { Bot, User, Bookmark, AlertCircle, AlertTriangle } from 'lucide-react';

interface ChatMessageProps {
  message: ChatMessageItem;
  onSelectCitation: (citation: SourceCitation) => void;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message, onSelectCitation }) => {
  const isUser = message.role === 'user';

  // Format assistant response text with simple markdown-like formatting (lists, bold, code)
  const renderFormattedContent = (content: string) => {
    const lines = content.split('\n');
    return lines.map((line, idx) => {
      // Check for bullet points
      if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
        return (
          <li key={idx} className="ml-4 list-disc my-1">
            {formatInlineText(line.trim().substring(2))}
          </li>
        );
      }
      // Check for numbered list
      const numMatch = line.trim().match(/^(\d+)\.\s+(.*)/);
      if (numMatch) {
        return (
          <li key={idx} className="ml-4 list-decimal my-1">
            {formatInlineText(numMatch[2])}
          </li>
        );
      }
      // Check for headers
      if (line.trim().startsWith('### ')) {
        return <h4 key={idx} className="font-bold text-slate-900 mt-3 mb-1 text-sm">{line.trim().substring(4)}</h4>;
      }
      if (line.trim().startsWith('## ')) {
        return <h3 key={idx} className="font-bold text-slate-900 mt-4 mb-1.5 text-base">{line.trim().substring(3)}</h3>;
      }
      if (line.trim().startsWith('# ')) {
        return <h2 key={idx} className="font-extrabold text-slate-900 mt-4 mb-2 text-lg">{line.trim().substring(2)}</h2>;
      }
      // Empty line
      if (!line.trim()) {
        return <div key={idx} className="h-2" />;
      }
      // Standard paragraph
      return (
        <p key={idx} className="my-1 leading-relaxed">
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
        return <strong key={i} className="font-semibold text-slate-900">{part.slice(2, -2)}</strong>;
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return (
          <code key={i} className="bg-slate-100 text-amber-800 text-xs px-1.5 py-0.5 rounded font-mono">
            {part.slice(1, -1)}
          </code>
        );
      }
      return part;
    });
  };

  return (
    <div className={`flex w-full my-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex max-w-3xl space-x-3 ${isUser ? 'flex-row-reverse space-x-reverse' : 'flex-row'}`}>
        {/* Avatar */}
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-white shadow-sm text-xs font-medium ${
            isUser
              ? 'bg-slate-700'
              : message.isError
              ? 'bg-rose-600'
              : 'bg-gradient-to-tr from-amber-500 to-amber-600'
          }`}
        >
          {isUser ? <User className="w-4 h-4" /> : message.isError ? <AlertTriangle className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
        </div>

        {/* Message Bubble & Meta */}
        <div className="flex flex-col space-y-1.5">
          <div
            className={`rounded-2xl px-4 py-3 text-sm shadow-sm ${
              isUser
                ? 'bg-amber-600 text-white rounded-tr-none'
                : message.isError
                ? 'bg-rose-50 text-rose-900 border border-rose-200 rounded-tl-none'
                : 'bg-white text-slate-800 border border-slate-200/80 rounded-tl-none'
            }`}
          >
            {/* Insufficient Evidence Warning Banner */}
            {message.insufficient_evidence && (
              <div className="mb-2 p-2.5 bg-amber-50 border border-amber-200 rounded-lg flex items-center space-x-2 text-xs text-amber-800">
                <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0" />
                <span>
                  <strong>Strict Grounding Active:</strong> No transcript evidence found; refusing speculation.
                </span>
              </div>
            )}

            {/* Message Body */}
            <div className={`leading-relaxed ${isUser ? 'whitespace-pre-wrap' : ''}`}>
              {isUser ? message.content : renderFormattedContent(message.content)}
            </div>

            {/* Sources / Citations List */}
            {message.sources && message.sources.length > 0 && (
              <div className="mt-3 pt-3 border-t border-slate-100">
                <div className="text-xs font-semibold text-slate-500 mb-2 flex items-center space-x-1">
                  <Bookmark className="w-3.5 h-3.5 text-amber-600" />
                  <span>Grounding Sources ({message.sources.length}):</span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {message.sources.map((src, idx) => (
                    <button
                      key={src.chunk_id || idx}
                      onClick={() => onSelectCitation(src)}
                      className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg text-xs font-medium bg-amber-50 text-amber-900 border border-amber-200/80 hover:bg-amber-100 hover:border-amber-300 transition-colors shadow-2xs"
                      title={`Inspect transcript excerpt from ${src.transcript_title}`}
                    >
                      <Bookmark className="w-3 h-3 text-amber-600 flex-shrink-0" />
                      <span className="truncate max-w-[200px]">{src.transcript_title}</span>
                      <span className="text-[10px] text-amber-700 bg-amber-200/60 px-1 py-0.2 rounded">
                        #{src.chunk_index}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Turn Metadata footer */}
          <div
            className={`flex items-center space-x-2 text-[11px] text-slate-400 px-1 ${
              isUser ? 'justify-end' : 'justify-start'
            }`}
          >
            <span>{new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
            {!isUser && message.provider && (
              <>
                <span>•</span>
                <span className="font-mono text-slate-500">{message.provider}/{message.model}</span>
              </>
            )}
            {!isUser && message.agent_framework && (
              <>
                <span>•</span>
                <span className="px-1.5 py-0.2 rounded bg-slate-100 text-slate-600 font-mono text-[10px]">
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
