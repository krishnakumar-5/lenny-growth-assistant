import React from 'react';
import { SourceCitation } from '../types/api';
import { X, FileText, User, Hash, AlertCircle, Bookmark } from 'lucide-react';

interface CitationInspectorProps {
  citation: SourceCitation | null;
  onClose: () => void;
}

export const CitationInspector: React.FC<CitationInspectorProps> = ({ citation, onClose }) => {
  if (!citation) return null;

  const isSynthetic = citation.metadata?.synthetic_test_data;
  const guest = citation.metadata?.guest || 'Not specified';
  const episode = citation.metadata?.episode || 'Not specified';
  const topic = citation.metadata?.topic || 'General Growth';

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="relative bg-white rounded-2xl max-w-2xl w-full shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/60">
          <div className="flex items-center space-x-2">
            <Bookmark className="w-5 h-5 text-amber-600" />
            <h3 className="font-semibold text-slate-900 text-base">
              Verified Transcript Citation
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4 max-h-[75vh] overflow-y-auto">
          {/* Synthetic disclaimer if applicable */}
          {isSynthetic && (
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl flex items-start space-x-2 text-amber-800 text-xs">
              <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold">Synthetic Benchmark Test Data:</span> This chunk is derived from test fixtures and is not an authentic recording from Lenny's Podcast.
              </div>
            </div>
          )}

          {/* Transcript Details */}
          <div className="bg-slate-50 rounded-xl p-4 border border-slate-200/80 space-y-2">
            <h4 className="font-semibold text-slate-900 text-sm">{citation.transcript_title}</h4>
            <div className="grid grid-cols-2 gap-2 text-xs text-slate-600">
              <div className="flex items-center space-x-1.5">
                <User className="w-3.5 h-3.5 text-slate-400" />
                <span>Guest: <strong className="text-slate-800">{guest}</strong></span>
              </div>
              <div className="flex items-center space-x-1.5">
                <Hash className="w-3.5 h-3.5 text-slate-400" />
                <span>Episode: <strong className="text-slate-800">{episode}</strong></span>
              </div>
              <div className="flex items-center space-x-1.5">
                <Bookmark className="w-3.5 h-3.5 text-slate-400" />
                <span>Topic: <strong className="text-slate-800">{topic}</strong></span>
              </div>
              <div className="flex items-center space-x-1.5">
                <FileText className="w-3.5 h-3.5 text-slate-400" />
                <span>File: <strong className="text-slate-800">{citation.source_filename}</strong></span>
              </div>
            </div>
            <div className="pt-2 border-t border-slate-200/60 flex items-center justify-between text-xs text-slate-500">
              <span>Chunk #{citation.chunk_index}</span>
              <span className="inline-flex items-center px-2 py-0.5 rounded-full font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                Score: {citation.score.toFixed(1)}
              </span>
            </div>
          </div>

          {/* Full Excerpt */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1.5">
              Source Excerpt
            </label>
            <div className="p-4 bg-slate-100/70 border border-slate-200 rounded-xl text-sm leading-relaxed text-slate-800 font-mono whitespace-pre-wrap select-text">
              {citation.chunk_text}
            </div>
          </div>

          {/* Metadata Raw */}
          <div className="text-[11px] text-slate-400 font-mono">
            Chunk ID: {citation.chunk_id}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 bg-slate-50 border-t border-slate-100 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-900 text-white rounded-xl text-xs font-medium hover:bg-slate-800 transition-colors"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};
