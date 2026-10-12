import React from 'react';
import { SourceCitation, Ship30Response } from '../types/api';
import { X, Bookmark, ExternalLink, Feather, ShieldCheck, FileText } from 'lucide-react';

interface ContextPanelProps {
  isOpen: boolean;
  onClose: () => void;
  sources: SourceCitation[];
  onSelectCitation: (citation: SourceCitation) => void;
  latestArtifact: Ship30Response | null;
  onOpenArtifact: (artifact: Ship30Response) => void;
}

export const ContextPanel: React.FC<ContextPanelProps> = ({
  isOpen,
  onClose,
  sources,
  onSelectCitation,
  latestArtifact,
  onOpenArtifact,
}) => {
  if (!isOpen) return null;

  return (
    <aside className="w-80 lg:w-96 flex-shrink-0 flex flex-col h-full bg-dark-900 border-l border-white/[0.08] text-slate-200 z-30 shadow-2xl animate-slide-in overflow-hidden">
      {/* Header */}
      <div className="h-16 px-5 flex items-center justify-between border-b border-white/[0.08] bg-dark-950/40 flex-shrink-0">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-400">
            <Bookmark className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-100 tracking-tight">Context & Provenance</h3>
            <span className="text-[10px] text-slate-400 flex items-center">
              <ShieldCheck className="w-3 h-3 text-emerald-400 mr-1" />
              Verified Podcast Grounding
            </span>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-white/[0.06] transition-colors"
          title="Close panel"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="flex-1 min-h-0 overflow-y-auto p-4 space-y-5">
        {/* Artifact Quick View (if available) */}
        {latestArtifact && (
          <div className="p-4 rounded-2xl bg-gradient-to-br from-amber-500/10 via-amber-500/5 to-transparent border border-amber-500/30 shadow-md">
            <div className="flex items-center justify-between mb-2">
              <span className="inline-flex items-center space-x-1 text-[10px] font-bold uppercase tracking-wider text-amber-400 bg-amber-500/20 px-2 py-0.5 rounded-full">
                <Feather className="w-3 h-3 mr-1" />
                Latest Artifact
              </span>
              <span className="text-[11px] text-slate-400 font-mono">
                {latestArtifact.word_count}w
              </span>
            </div>
            <h4 className="text-xs font-bold text-slate-100 line-clamp-2 mb-1.5">
              {latestArtifact.title}
            </h4>
            <p className="text-[11px] text-slate-400 line-clamp-2 mb-3">
              {latestArtifact.hook}
            </p>
            <button
              onClick={() => onOpenArtifact(latestArtifact)}
              className="w-full flex items-center justify-center space-x-1.5 py-1.5 px-3 rounded-lg text-xs font-semibold bg-amber-500 text-slate-950 hover:bg-amber-400 transition-colors shadow-sm"
            >
              <span>View Full Essay Artifact</span>
              <ExternalLink className="w-3 h-3" />
            </button>
          </div>
        )}

        {/* Retrieved Citations */}
        <div>
          <div className="flex items-center justify-between mb-3 px-1">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Retrieved Sources ({sources.length})
            </span>
            <span className="text-[11px] text-amber-400 font-medium">Ranked by BM25</span>
          </div>

          {sources.length === 0 ? (
            <div className="p-6 text-center rounded-2xl bg-dark-950/40 border border-white/[0.06] text-xs text-slate-500 space-y-2">
              <FileText className="w-6 h-6 mx-auto text-slate-600" />
              <p className="font-medium text-slate-400">No active turn selected</p>
              <p className="text-[11px] text-slate-500">
                Ask a question in chat to view real citations and episode excerpts here.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {sources.map((src, idx) => {
                const guest = src.metadata?.guest || 'Lenny\'s Guest';
                const episode = src.metadata?.episode || src.metadata?.date || `#${src.chunk_index}`;
                const postUrl = src.metadata?.post_url || src.metadata?.source_url;
                const youtubeUrl = src.metadata?.youtube_url;

                return (
                  <div
                    key={src.chunk_id || idx}
                    onClick={() => onSelectCitation(src)}
                    className="p-3.5 rounded-xl bg-dark-950/60 border border-white/[0.08] hover:border-amber-500/40 transition-all duration-200 cursor-pointer spatial-card group"
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[10px] font-semibold text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded-md">
                        {guest} • Ep. {episode}
                      </span>
                      <span className="text-[10px] font-mono text-slate-500">
                        Score: {src.score ? src.score.toFixed(1) : 'N/A'}
                      </span>
                    </div>

                    <h5 className="text-xs font-semibold text-slate-200 group-hover:text-amber-200 transition-colors line-clamp-1 mb-2">
                      {src.transcript_title}
                    </h5>

                    <p className="text-[11px] text-slate-400 line-clamp-3 leading-relaxed italic bg-white/[0.02] p-2 rounded-lg border border-white/[0.04]">
                      "{src.chunk_text}"
                    </p>

                    {/* External Link pills */}
                    <div className="mt-2.5 pt-2 border-t border-white/[0.04] flex items-center space-x-2 text-[10px]">
                      {postUrl && (
                        <a
                          href={postUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="inline-flex items-center text-amber-400 hover:text-amber-300 font-medium space-x-1"
                        >
                          <span>Substack Post</span>
                          <ExternalLink className="w-2.5 h-2.5" />
                        </a>
                      )}
                      {youtubeUrl && (
                        <a
                          href={youtubeUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="inline-flex items-center text-red-400 hover:text-red-300 font-medium space-x-1"
                        >
                          <span>YouTube</span>
                          <ExternalLink className="w-2.5 h-2.5" />
                        </a>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </aside>
  );
};
