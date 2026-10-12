import React, { useState } from 'react';
import { generateShip30Essay } from '../services/api';
import { Ship30Response } from '../types/api';
import { Feather, Sparkles, Loader2, AlertCircle, ArrowRight, BookOpen } from 'lucide-react';

interface Ship30GeneratorProps {
  provider: string;
  model: string;
  onOpenArtifact: (artifact: Ship30Response) => void;
}

export const Ship30Generator: React.FC<Ship30GeneratorProps> = ({
  provider,
  model,
  onOpenArtifact,
}) => {
  const [topic, setTopic] = useState('');
  const [audience, setAudience] = useState('Growth PMs, Founders, and Product Leaders');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const curatedTopics = [
    {
      title: 'Elena Verna: Retention & The Leaky Bucket',
      query: 'Elena Verna why retention precedes acquisition and the leaky bucket fallacy',
      guest: 'Elena Verna',
    },
    {
      title: 'Elena Verna: The 14-Day Reverse Trial',
      query: 'Elena Verna freemium vs free trial vs reverse trial mechanics in B2B',
      guest: 'Elena Verna',
    },
    {
      title: 'Shreyas Doshi: High Agency in Product Craft',
      query: 'Shreyas Doshi high agency product management and treating constraints as puzzles',
      guest: 'Shreyas Doshi',
    },
    {
      title: 'Shreyas Doshi: The Pre-Mortem Ritual',
      query: 'Shreyas Doshi product strategy and pre-mortems before launch',
      guest: 'Shreyas Doshi',
    },
    {
      title: 'Brian Balfour: Loops vs Funnels',
      query: 'Brian Balfour why traditional funnels are obsolete and growth loops compound',
      guest: 'Brian Balfour',
    },
    {
      title: 'Brian Balfour: The Four Fits Framework',
      query: 'Brian Balfour the four fits framework for venture scale growth',
      guest: 'Brian Balfour',
    },
  ];

  const handleGenerate = async (selectedTopic?: string) => {
    const topicToUse = selectedTopic || topic;
    if (!topicToUse.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await generateShip30Essay({
        topic: topicToUse.trim(),
        target_audience: audience,
        provider,
        model,
      });

      onOpenArtifact(response);
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to generate Atomic Essay');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6 space-y-6">
      {/* Hero Header Panel */}
      <div className="spatial-panel p-6 sm:p-8 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-48 bg-gradient-to-bl from-amber-500/15 via-orange-500/5 to-transparent pointer-events-none" />

        <div className="flex items-center space-x-2.5 mb-3">
          <div className="w-9 h-9 rounded-xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-400 shadow-sm">
            <Feather className="w-4 h-4" />
          </div>
          <span className="text-xs uppercase tracking-wider font-bold text-amber-400">
            Dedicated Ship 30 Skill
          </span>
          <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/30">
            Target ~1,250 Words
          </span>
        </div>
        <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-100 mb-2">
          Ship 30 for 30: Long-Form Essay Studio
        </h2>
        <p className="text-xs sm:text-sm text-slate-400 max-w-2xl leading-relaxed">
          Operationalize insights from Lenny's Podcast into grounded long-form essays (1,150–1,350 words) structured with Ship 30 principles: compelling hook, clear headings, skimmable bullet points, and verified source citations.
        </p>
      </div>

      {/* Generator Form */}
      <div className="spatial-panel p-6 sm:p-7 space-y-4">
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-2">
            Growth Topic / Framework
          </label>
          <textarea
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="E.g., Why product-led sales depends on Product-Qualified Leads, or Shreyas Doshi's principles of product strategy..."
            rows={3}
            disabled={loading}
            className="w-full rounded-xl border border-white/[0.1] p-3 text-sm focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 bg-dark-950/70 text-slate-100 placeholder-slate-500 transition-colors"
          />
        </div>

        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-2">
            Target Audience
          </label>
          <input
            type="text"
            value={audience}
            onChange={(e) => setAudience(e.target.value)}
            disabled={loading}
            className="w-full rounded-xl border border-white/[0.1] px-3.5 py-2.5 text-sm focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 bg-dark-950/70 text-slate-100 placeholder-slate-500 transition-colors"
          />
        </div>

        {error && (
          <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl flex items-start space-x-2 text-rose-300 text-xs">
            <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-bold">Grounding Safeguard Notice:</span> {error}
            </div>
          </div>
        )}

        <div className="flex justify-end pt-2">
          <button
            onClick={() => handleGenerate()}
            disabled={loading || !topic.trim()}
            className="flex items-center space-x-2 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 px-6 py-2.5 rounded-xl font-bold text-sm transition-all shadow-md shadow-amber-500/20 disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Synthesizing Long-Form Essay (~1,250w)...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Generate Atomic Essay Artifact</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Curated Templates Section */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-slate-200 flex items-center space-x-2">
          <BookOpen className="w-4 h-4 text-amber-400" />
          <span>Curated Growth Frameworks (Instant Generation)</span>
        </h3>
        <p className="text-xs text-slate-400">
          Click any verified framework below to pull transcript evidence and generate an Atomic Essay artifact:
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {curatedTopics.map((item, idx) => (
            <button
              key={idx}
              disabled={loading}
              onClick={() => {
                setTopic(item.query);
                handleGenerate(item.query);
              }}
              className="text-left p-4 rounded-xl spatial-card hover:border-amber-500/40 transition-all group disabled:opacity-50 flex items-center justify-between"
            >
              <div>
                <span className="text-[10px] font-semibold uppercase tracking-wider text-amber-400 bg-amber-500/15 border border-amber-500/30 px-2 py-0.5 rounded">
                  {item.guest}
                </span>
                <h4 className="text-xs font-semibold text-slate-200 group-hover:text-white mt-1.5 transition-colors">
                  {item.title}
                </h4>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-amber-400 group-hover:translate-x-1 transition-all flex-shrink-0 ml-2" />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
