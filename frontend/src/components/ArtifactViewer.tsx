import React, { useState } from 'react';
import { Ship30Response } from '../types/api';
import { X, Copy, Check, Download, Eye, Code, Layout, ShieldCheck, Bookmark, Feather } from 'lucide-react';

interface ArtifactViewerProps {
  artifact: Ship30Response | null;
  onClose: () => void;
}

export const ArtifactViewer: React.FC<ArtifactViewerProps> = ({ artifact, onClose }) => {
  const [activeTab, setActiveTab] = useState<'preview' | 'html' | 'raw'>('preview');
  const [copied, setCopied] = useState(false);

  if (!artifact) return null;

  const handleCopyMarkdown = () => {
    navigator.clipboard.writeText(artifact.content_markdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadMarkdown = () => {
    const blob = new Blob([artifact.content_markdown], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    const filename = `${artifact.title.toLowerCase().replace(/[^a-z0-9]+/g, '-')}.md`;
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-dark-950/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="relative spatial-panel bg-dark-900 border border-white/[0.1] rounded-2xl max-w-3xl w-full shadow-2xl overflow-hidden flex flex-col max-h-[90vh] animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="px-6 py-4 border-b border-white/[0.08] bg-dark-950/50 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-amber-500/15 border border-amber-500/30 text-amber-400 flex items-center justify-center shadow-sm">
              <Feather className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="font-bold text-slate-100 text-base tracking-tight">
                  Artifact Viewer: Atomic Essay
                </h3>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                  <ShieldCheck className="w-3 h-3 mr-1" />
                  Secure Sandbox
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Grounded in Lenny's Podcast insights from <strong className="text-slate-200">{artifact.guest_attribution}</strong>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-white/[0.06] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Subheader & Controls */}
        <div className="px-6 py-3 border-b border-white/[0.08] bg-dark-950/30 flex flex-wrap items-center justify-between gap-3">
          {/* Tab Navigation */}
          <div className="flex items-center bg-dark-950 p-1 rounded-xl border border-white/[0.08]">
            <button
              onClick={() => setActiveTab('preview')}
              className={`flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition-colors ${
                activeTab === 'preview' ? 'bg-amber-500 text-slate-950 shadow-sm' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Eye className="w-3.5 h-3.5" />
              <span>Preview</span>
            </button>
            <button
              onClick={() => setActiveTab('html')}
              className={`flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition-colors ${
                activeTab === 'html' ? 'bg-amber-500 text-slate-950 shadow-sm' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Layout className="w-3.5 h-3.5" />
              <span>HTML Card (Isolated)</span>
            </button>
            <button
              onClick={() => setActiveTab('raw')}
              className={`flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition-colors ${
                activeTab === 'raw' ? 'bg-amber-500 text-slate-950 shadow-sm' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Code className="w-3.5 h-3.5" />
              <span>Raw Markdown</span>
            </button>
          </div>

          {/* Word Count Constraint Badge */}
          <div className="flex items-center space-x-2">
            <span
              className={`text-xs px-2.5 py-1 rounded-full font-semibold border ${
                artifact.within_constraints
                  ? 'bg-amber-500/15 text-amber-300 border-amber-500/30'
                  : 'bg-rose-500/15 text-rose-300 border-rose-500/30'
              }`}
            >
              {artifact.word_count} words • {artifact.within_constraints ? (artifact.word_count > 500 ? 'Ship 30 Compliant (~1,250w)' : 'Ship 30 Compliant') : 'Word Count Notice'}
            </span>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-2">
            <button
              onClick={handleCopyMarkdown}
              className="flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-medium border border-white/[0.08] text-slate-300 hover:bg-white/[0.06] hover:text-white transition-colors"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-slate-400" />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>
            <button
              onClick={handleDownloadMarkdown}
              className="flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 shadow-sm transition-all"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export .md</span>
            </button>
          </div>
        </div>

        {/* Content Viewer */}
        <div className="p-6 flex-1 overflow-y-auto bg-dark-950/40">
          {activeTab === 'preview' && (
            <div className="spatial-card p-6 sm:p-8 space-y-4 max-w-2xl mx-auto">
              <div className="inline-block px-3 py-1 rounded-full bg-amber-500/15 border border-amber-500/30 text-amber-400 text-[11px] font-bold uppercase tracking-wider">
                Atomic Essay • Ship 30 for 30
              </div>
              <h2 className="text-2xl font-black text-slate-100 leading-snug">
                {artifact.title}
              </h2>
              <div className="text-xs text-slate-400 border-b border-white/[0.08] pb-3">
                Insights by <strong className="text-slate-200">{artifact.guest_attribution}</strong> • Verified from Lenny's Podcast
              </div>
              <div className="text-slate-200 text-sm leading-relaxed whitespace-pre-wrap font-sans space-y-3">
                {artifact.content_markdown.split('\n\n').map((paragraph, i) => (
                  <p key={i}>{paragraph.replace(/^#+\s.*$/g, '')}</p>
                ))}
              </div>

              {/* Citations Footer */}
              {artifact.sources.length > 0 && (
                <div className="mt-6 pt-4 border-t border-white/[0.08]">
                  <div className="text-xs font-semibold text-slate-400 mb-2 flex items-center space-x-1">
                    <Bookmark className="w-3.5 h-3.5 text-amber-400" />
                    <span>Grounding Sources:</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {artifact.sources.map((s, idx) => (
                      <span
                        key={idx}
                        className="text-[11px] px-2 py-0.5 rounded-md bg-amber-500/15 text-amber-300 border border-amber-500/30"
                      >
                        {s.transcript_title} (#{s.chunk_index})
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'html' && (
            <div className="flex flex-col items-center justify-center">
              <div className="w-full bg-white rounded-2xl shadow-lg overflow-hidden min-h-[460px]">
                {/* Sandboxed iframe for isolated rendering */}
                <iframe
                  title="Sanitized HTML Artifact Preview"
                  srcDoc={artifact.content_html}
                  sandbox=""
                  className="w-full h-[520px] border-0"
                />
              </div>
              <p className="text-[11px] text-slate-400 mt-2 text-center">
                Rendered securely inside an isolated, sandboxed iframe without script execution privileges.
              </p>
            </div>
          )}

          {activeTab === 'raw' && (
            <div className="bg-dark-950 text-slate-200 rounded-2xl p-5 font-mono text-xs leading-relaxed overflow-x-auto border border-white/[0.08] whitespace-pre-wrap select-text">
              {artifact.content_markdown}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
