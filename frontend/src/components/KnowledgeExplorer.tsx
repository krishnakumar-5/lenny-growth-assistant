import React, { useState } from 'react';
import { searchTranscripts } from '../services/api';
import { SearchResultChunk } from '../types/api';
import { Search, BookOpen, AlertCircle, Bookmark, User, Hash, Loader2 } from 'lucide-react';

export const KnowledgeExplorer: React.FC = () => {
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
      {/* Search Header */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <div className="flex items-center space-x-2.5 mb-2">
          <BookOpen className="w-5 h-5 text-amber-600" />
          <h2 className="text-lg font-bold text-slate-900">
            Podcast Transcript Knowledge Explorer
          </h2>
        </div>
        <p className="text-xs text-slate-500 mb-5">
          Query the underlying vector and keyword retrieval engine (`POST /api/v1/sources/search`) to inspect indexed chunks, relevancy scoring, and provenance.
        </p>

        <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-grow">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search concepts (e.g. 'cohort retention', 'growth loops', 'Elena Verna')..."
              className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500 bg-slate-50/50"
            />
          </div>

          <div className="flex items-center space-x-2">
            <select
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              className="text-xs rounded-xl border border-slate-200 bg-slate-50 py-2.5 px-3 font-medium text-slate-700 focus:outline-none focus:border-amber-500"
            >
              <option value={3}>Top 3</option>
              <option value={5}>Top 5</option>
              <option value={10}>Top 10</option>
            </select>

            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="flex items-center space-x-2 bg-amber-600 hover:bg-amber-700 text-white px-5 py-2.5 rounded-xl font-medium text-sm transition-colors shadow-sm disabled:opacity-50"
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
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-center space-x-2 text-rose-800 text-sm">
          <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Results Header */}
      {totalResults !== null && (
        <div className="flex items-center justify-between px-1">
          <h3 className="text-sm font-semibold text-slate-700">
            {totalResults} {totalResults === 1 ? 'match' : 'matches'} found for "{searchedQuery}"
          </h3>
        </div>
      )}

      {/* Results List */}
      <div className="space-y-4">
        {results.map((chunk) => {
          const guest = chunk.metadata?.guest || 'Not specified';
          const episode = chunk.metadata?.episode || 'Not specified';
          const isSynthetic = chunk.metadata?.synthetic_test_data;

          return (
            <div
              key={chunk.chunk_id}
              className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:shadow transition-shadow space-y-3"
            >
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
                <div className="flex items-center space-x-2">
                  <Bookmark className="w-4 h-4 text-amber-600 flex-shrink-0" />
                  <h4 className="font-semibold text-slate-900 text-sm">{chunk.transcript_title}</h4>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-0.5 rounded-full font-semibold">
                    Relevance: {chunk.score.toFixed(1)}
                  </span>
                  <span className="text-xs text-slate-500 font-mono">
                    Chunk #{chunk.chunk_index}
                  </span>
                </div>
              </div>

              {isSynthetic && (
                <div className="text-xs text-amber-800 bg-amber-50 px-3 py-1.5 rounded-lg border border-amber-200 flex items-center space-x-1.5">
                  <AlertCircle className="w-3.5 h-3.5 text-amber-600 flex-shrink-0" />
                  <span>Benchmark Synthetic Test Fixture (Not authentic episode recording)</span>
                </div>
              )}

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs text-slate-600">
                <div className="flex items-center space-x-1.5">
                  <User className="w-3.5 h-3.5 text-slate-400" />
                  <span>Guest: <strong className="text-slate-800">{guest}</strong></span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <Hash className="w-3.5 h-3.5 text-slate-400" />
                  <span>Episode: <strong className="text-slate-800">{episode}</strong></span>
                </div>
                <div className="flex items-center space-x-1.5 text-slate-500">
                  <span>File: <strong className="text-slate-700">{chunk.source_filename}</strong></span>
                </div>
              </div>

              <div className="p-3 bg-slate-50 rounded-xl text-xs font-mono text-slate-700 leading-relaxed border border-slate-100 whitespace-pre-wrap">
                {chunk.chunk_text}
              </div>
            </div>
          );
        })}

        {totalResults === 0 && (
          <div className="text-center py-12 bg-white rounded-2xl border border-slate-200 p-8 space-y-3">
            <BookOpen className="w-10 h-10 text-slate-300 mx-auto" />
            <h4 className="font-semibold text-slate-800 text-sm">No Matching Transcripts Found</h4>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              The search query did not match any indexed chunks in `data/transcripts/`. Under the Grounded Growth Assistant rules, queries without matching evidence trigger the anti-hallucination refusal gate.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
