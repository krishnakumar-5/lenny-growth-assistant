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
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="relative bg-white rounded-2xl max-w-3xl w-full shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[90vh] animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50/80 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-amber-500 text-white flex items-center justify-center shadow-sm">
              <Feather className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="font-bold text-slate-900 text-base">
                  Artifact Viewer: Atomic Essay
                </h3>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <ShieldCheck className="w-3 h-3 mr-1" />
                  Secure Sandbox
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Grounded in Lenny's Podcast insights from <strong>{artifact.guest_attribution}</strong>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200/60 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Subheader & Controls */}
        <div className="px-6 py-3 border-b border-slate-100 bg-white flex flex-wrap items-center justify-between gap-3">
          {/* Tab Navigation */}
          <div className="flex items-center bg-slate-100 p-1 rounded-lg">
            <button
              onClick={() => setActiveTab('preview')}
              className={`flex items-center space-x-1.5 px-3 py-1 rounded-md text-xs font-semibold transition-colors ${
                activeTab === 'preview' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Eye className="w-3.5 h-3.5" />
              <span>Preview</span>
            </button>
            <button
              onClick={() => setActiveTab('html')}
              className={`flex items-center space-x-1.5 px-3 py-1 rounded-md text-xs font-semibold transition-colors ${
                activeTab === 'html' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Layout className="w-3.5 h-3.5" />
              <span>HTML Card (Isolated)</span>
            </button>
            <button
              onClick={() => setActiveTab('raw')}
              className={`flex items-center space-x-1.5 px-3 py-1 rounded-md text-xs font-semibold transition-colors ${
                activeTab === 'raw' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'
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
                  ? 'bg-amber-50 text-amber-900 border-amber-300'
                  : 'bg-rose-50 text-rose-800 border-rose-200'
              }`}
            >
              {artifact.word_count} words • {artifact.within_constraints ? (artifact.word_count > 500 ? 'Ship 30 Compliant (~1,250w)' : 'Ship 30 Compliant (200-300w)') : 'Word Count Notice'}
            </span>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-2">
            <button
              onClick={handleCopyMarkdown}
              className="flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-medium border border-slate-200 text-slate-700 hover:bg-slate-50 transition-colors"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5 text-slate-500" />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>
            <button
              onClick={handleDownloadMarkdown}
              className="flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-900 text-white hover:bg-slate-800 transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export .md</span>
            </button>
          </div>
        </div>

        {/* Content Viewer */}
        <div className="p-6 flex-1 overflow-y-auto bg-slate-50/40">
          {activeTab === 'preview' && (
            <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm space-y-4 max-w-2xl mx-auto">
              <div className="inline-block px-3 py-1 rounded-full bg-amber-50 border border-amber-200 text-amber-800 text-[11px] font-bold uppercase tracking-wider">
                Atomic Essay • Ship 30 for 30
              </div>
              <h2 className="text-2xl font-black text-slate-900 leading-snug">
                {artifact.title}
              </h2>
              <div className="text-xs text-slate-500 border-b border-slate-100 pb-3">
                Insights by <strong className="text-slate-800">{artifact.guest_attribution}</strong> • Verified from Lenny's Podcast
              </div>
              <div className="text-slate-800 text-sm leading-relaxed whitespace-pre-wrap font-sans space-y-3">
                {artifact.content_markdown.split('\n\n').map((paragraph, i) => (
                  <p key={i}>{paragraph.replace(/^#+\s.*$/g, '')}</p>
                ))}
              </div>

              {/* Citations Footer */}
              {artifact.sources.length > 0 && (
                <div className="mt-6 pt-4 border-t border-slate-100">
                  <div className="text-xs font-semibold text-slate-500 mb-2 flex items-center space-x-1">
                    <Bookmark className="w-3.5 h-3.5 text-amber-600" />
                    <span>Grounding Sources:</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {artifact.sources.map((s, idx) => (
                      <span
                        key={idx}
                        className="text-[11px] px-2 py-0.5 rounded-md bg-amber-50 text-amber-900 border border-amber-200"
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
              <div className="w-full bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden min-h-[460px]">
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
            <div className="bg-slate-900 text-slate-100 rounded-2xl p-5 font-mono text-xs leading-relaxed overflow-x-auto shadow-inner border border-slate-800 whitespace-pre-wrap select-text">
              {artifact.content_markdown}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
