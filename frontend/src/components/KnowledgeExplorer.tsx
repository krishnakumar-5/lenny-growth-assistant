import React, { useState } from 'react';
import { searchTranscripts } from '../services/api';
import { SearchResultChunk } from '../types/api';
import {
  Search,
  BookOpen,
  AlertCircle,
  Bookmark,
  User,
  Hash,
  Loader2,
  ExternalLink,
  Calendar,
  Sparkles,
} from 'lucide-react';

interface KnowledgeExplorerProps {
  onBackToChat?: () => void;
}

export const KnowledgeExplorer: React.FC<KnowledgeExplorerProps> = ({ onBackToChat }) => {
  const [query, setQuery] = useState('');
  const [limit, setLimit] = useState(5);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<SearchResultChunk[]>([]);
  const [totalResults, setTotalResults] = useState<number | null>(null);
  const [searchedQuery, setSearchedQuery] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const data = await searchTranscripts(query.trim(), limit);
      setResults(data.results);
      setTotalResults(data.total_results);
      setSearchedQuery(data.query);
    } catch (err: any) {
      setError(err.detail || err.message || 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-6 space-y-6">
      {/* Search Header Panel */}
      <div className="spatial-panel p-6 sm:p-7 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-40 bg-gradient-to-bl from-amber-500/10 via-transparent to-transparent pointer-events-none" />

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-5">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-400">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-100 flex items-center space-x-2">
                <span>Podcast Transcript Knowledge Explorer</span>
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                  50 Episodes Indexed
                </span>
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Inspect vector and keyword retrieval results, similarity scoring, and authentic source provenance.
              </p>
            </div>
          </div>

          {onBackToChat && (
            <button
              onClick={onBackToChat}
              className="self-start sm:self-auto text-xs px-3 py-1.5 rounded-xl border border-white/[0.08] text-slate-300 hover:text-white hover:bg-white/[0.06] transition-colors"
            >
              Back to Chat
            </button>
          )}
        </div>

        <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-grow">
            <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search concepts (e.g. 'cohort retention', 'growth loops', 'Elena Verna', 'Shreyas Doshi')..."
              className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-white/[0.1] bg-dark-950/70 text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500 transition-colors"
            />
          </div>

          <div className="flex items-center space-x-2">
            <select
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              className="text-xs rounded-xl border border-white/[0.1] bg-dark-950/80 py-2.5 px-3 font-medium text-slate-300 focus:outline-none focus:border-amber-500"
            >
              <option value={3}>Top 3</option>
              <option value={5}>Top 5</option>
              <option value={10}>Top 10</option>
            </select>

            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="flex items-center space-x-2 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 px-5 py-2.5 rounded-xl font-bold text-sm transition-all shadow-md shadow-amber-500/20 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Searching...</span>
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  <span>Search</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Error display */}
      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl flex items-center space-x-2 text-rose-300 text-sm">
          <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Results Header */}
      {totalResults !== null && (
        <div className="flex items-center justify-between px-1">
          <h3 className="text-sm font-semibold text-slate-300 flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-amber-400" />
            <span>
              {totalResults} {totalResults === 1 ? 'match' : 'matches'} found for "{searchedQuery}"
            </span>
          </h3>
        </div>
      )}

      {/* Results List */}
      <div className="space-y-4">
        {results.map((chunk) => {
          const guest = chunk.metadata?.guest || 'Not specified';
          const episode = chunk.metadata?.episode || 'Not specified';
          const isSynthetic = chunk.metadata?.synthetic_test_data;
          const sourceUrl = chunk.metadata?.source_url;
          const youtubeUrl = chunk.metadata?.youtube_url;
          const pubDate = chunk.metadata?.publication_date;

          return (
            <div
              key={chunk.chunk_id}
              className="spatial-card p-5 sm:p-6 space-y-4"
            >
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/[0.08] pb-3">
                <div className="flex items-center space-x-2.5">
                  <Bookmark className="w-4 h-4 text-amber-400 flex-shrink-0" />
                  <h4 className="font-semibold text-slate-100 text-sm tracking-tight">
                    {chunk.transcript_title}
                  </h4>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 px-2.5 py-0.5 rounded-full font-semibold">
                    Relevance: {chunk.score.toFixed(1)}
                  </span>
                  <span className="text-xs text-slate-500 font-mono">
                    Chunk #{chunk.chunk_index}
                  </span>
                </div>
              </div>

              {isSynthetic && (
                <div className="text-xs text-amber-300 bg-amber-500/15 px-3 py-1.5 rounded-lg border border-amber-500/30 flex items-center space-x-1.5">
                  <AlertCircle className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
                  <span>Benchmark Synthetic Test Fixture (Not authentic episode recording)</span>
                </div>
              )}

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs text-slate-400">
                <div className="flex items-center space-x-1.5">
                  <User className="w-3.5 h-3.5 text-slate-500" />
                  <span>Guest: <strong className="text-slate-200">{guest}</strong></span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <Hash className="w-3.5 h-3.5 text-slate-500" />
                  <span>Episode: <strong className="text-slate-200">{episode}</strong></span>
                </div>
                {pubDate && (
                  <div className="flex items-center space-x-1.5">
                    <Calendar className="w-3.5 h-3.5 text-slate-500" />
                    <span>Date: <strong className="text-slate-200">{pubDate}</strong></span>
                  </div>
                )}
                <div className="flex items-center space-x-1.5 text-slate-500 truncate">
                  <span>File: <strong className="text-slate-300">{chunk.source_filename}</strong></span>
                </div>
              </div>

              {/* Chunk text with code-like styling */}
              <div className="p-3.5 bg-dark-950/70 rounded-xl text-xs font-mono text-slate-300 leading-relaxed border border-white/[0.06] whitespace-pre-wrap">
                {chunk.chunk_text}
              </div>

              {/* External source links if available */}
              {(sourceUrl || youtubeUrl) && (
                <div className="flex flex-wrap items-center gap-3 pt-1 text-xs border-t border-white/[0.06]">
                  {sourceUrl && (
                    <a
                      href={sourceUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center space-x-1 text-amber-400 hover:text-amber-300 transition-colors"
                    >
                      <ExternalLink className="w-3 h-3" />
                      <span>Original Substack Article</span>
                    </a>
                  )}
                  {youtubeUrl && (
                    <a
                      href={youtubeUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center space-x-1 text-red-400 hover:text-red-300 transition-colors"
                    >
                      <ExternalLink className="w-3 h-3" />
                      <span>YouTube Episode</span>
                    </a>
                  )}
                </div>
              )}
            </div>
          );
        })}

        {totalResults === 0 && (
          <div className="text-center py-12 spatial-panel p-8 space-y-3">
            <BookOpen className="w-10 h-10 text-slate-600 mx-auto" />
            <h4 className="font-semibold text-slate-200 text-sm">No Matching Transcripts Found</h4>
            <p className="text-xs text-slate-400 max-w-sm mx-auto leading-relaxed">
              The search query did not match any indexed chunks. Under the Grounded Growth Assistant rules, queries without matching evidence trigger the anti-hallucination refusal gate.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
