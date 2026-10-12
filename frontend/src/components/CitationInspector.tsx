import React from 'react';
import { SourceCitation } from '../types/api';
import { X, FileText, User, Hash, AlertCircle, Bookmark, ExternalLink } from 'lucide-react';

interface CitationInspectorProps {
  citation: SourceCitation | null;
  onClose: () => void;
}

export const CitationInspector: React.FC<CitationInspectorProps> = ({ citation, onClose }) => {
  if (!citation) return null;

  const isSynthetic = citation.metadata?.synthetic_test_data || citation.metadata?.is_test_fixture;
  const guest = citation.metadata?.guest || 'Not specified';
  const episode = citation.metadata?.episode || citation.metadata?.date || 'Not specified';
  const topic = citation.metadata?.topic || 'General Growth';
  const postUrl = citation.metadata?.post_url || citation.metadata?.source_url;
  const youtubeUrl = citation.metadata?.youtube_url;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-dark-950/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="relative spatial-panel bg-dark-900 border border-white/[0.1] max-w-2xl w-full shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="px-6 py-4 border-b border-white/[0.08] flex items-center justify-between bg-dark-950/50">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-400">
              <Bookmark className="w-4 h-4" />
            </div>
            <h3 className="font-semibold text-slate-100 text-base tracking-tight">
              Verified Transcript Citation
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-white/[0.06] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4 max-h-[75vh] overflow-y-auto">
          {/* Synthetic disclaimer if applicable */}
          {isSynthetic && (
            <div className="p-3 bg-amber-500/15 border border-amber-500/30 rounded-xl flex items-start space-x-2 text-amber-300 text-xs">
              <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold">Synthetic Benchmark Test Data:</span> This chunk is derived from test fixtures and is not an authentic recording from Lenny's Podcast.
              </div>
            </div>
          )}

          {/* Transcript Details */}
          <div className="bg-dark-950/60 rounded-xl p-4 border border-white/[0.08] space-y-2.5">
            <h4 className="font-semibold text-slate-100 text-sm tracking-tight">{citation.transcript_title}</h4>
            <div className="grid grid-cols-2 gap-2 text-xs text-slate-400">
              <div className="flex items-center space-x-1.5">
                <User className="w-3.5 h-3.5 text-slate-500" />
                <span>Guest: <strong className="text-slate-200">{guest}</strong></span>
              </div>
              <div className="flex items-center space-x-1.5">
                <Hash className="w-3.5 h-3.5 text-slate-500" />
                <span>Episode: <strong className="text-slate-200">{episode}</strong></span>
              </div>
              <div className="flex items-center space-x-1.5">
                <Bookmark className="w-3.5 h-3.5 text-slate-500" />
                <span>Topic: <strong className="text-slate-200">{topic}</strong></span>
              </div>
              <div className="flex items-center space-x-1.5 truncate">
                <FileText className="w-3.5 h-3.5 text-slate-500" />
                <span>File: <strong className="text-slate-200">{citation.source_filename}</strong></span>
              </div>
            </div>
            <div className="pt-2 border-t border-white/[0.06] flex items-center justify-between text-xs text-slate-400">
              <span className="font-mono">Chunk #{citation.chunk_index}</span>
              <span className="inline-flex items-center px-2 py-0.5 rounded-full font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                Score: {citation.score.toFixed(1)}
              </span>
            </div>
            {postUrl && (
              <div className="pt-2 border-t border-white/[0.06] flex items-center space-x-2 text-xs">
                <span className="text-slate-400 font-medium">Original Post:</span>
                <a
                  href={postUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-amber-400 hover:text-amber-300 underline font-medium truncate inline-flex items-center space-x-1"
                >
                  <span className="truncate">{postUrl}</span>
                  <ExternalLink className="w-3 h-3 flex-shrink-0" />
                </a>
              </div>
            )}
            {youtubeUrl && (
              <div className="pt-2 border-t border-white/[0.06] flex items-center space-x-2 text-xs">
                <span className="text-slate-400 font-medium">YouTube:</span>
                <a
                  href={youtubeUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-red-400 hover:text-red-300 underline font-medium truncate inline-flex items-center space-x-1"
                >
                  <span className="truncate">{youtubeUrl}</span>
                  <ExternalLink className="w-3 h-3 flex-shrink-0" />
                </a>
              </div>
            )}
          </div>

          {/* Excerpt */}
          <div className="space-y-1.5">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Chunk Excerpt
            </label>
            <div className="p-4 bg-dark-950/80 rounded-xl text-xs font-mono text-slate-200 leading-relaxed border border-white/[0.08] max-h-60 overflow-y-auto whitespace-pre-wrap">
              {citation.chunk_text}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-white/[0.08] bg-dark-950/50 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-white/[0.08] text-slate-200 hover:bg-white/[0.12] hover:text-white transition-colors"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};
