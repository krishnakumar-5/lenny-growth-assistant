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
      {/* Hero Header */}
      <div className="bg-gradient-to-r from-amber-500 to-amber-600 rounded-2xl p-6 sm:p-8 text-white shadow-md">
        <div className="flex items-center space-x-2.5 mb-2">
          <div className="w-8 h-8 rounded-lg bg-white/20 backdrop-blur flex items-center justify-center">
            <Feather className="w-4 h-4" />
          </div>
          <span className="text-xs uppercase tracking-wider font-bold text-amber-100">
            Dedicated Skill
          </span>
        </div>
        <h2 className="text-xl sm:text-2xl font-bold tracking-tight mb-2">
          Ship 30 for 30: Atomic Essay Generator
        </h2>
        <p className="text-xs sm:text-sm text-amber-50 max-w-2xl leading-relaxed">
          Operationalize insights from Lenny's Podcast into concise, 200–300 word "Atomic Essays" designed with the framework by Dickie Bush & Nicolas Cole.
        </p>
      </div>

      {/* Generator Form */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-2">
            Growth Topic / Framework
          </label>
          <textarea
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="E.g., Why product-led sales depends on Product-Qualified Leads, or Shreyas Doshi's principles of product strategy..."
            rows={3}
            disabled={loading}
            className="w-full rounded-xl border border-slate-200 p-3 text-sm focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 bg-slate-50/50"
          />
        </div>

        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-2">
            Target Audience
          </label>
          <input
            type="text"
            value={audience}
            onChange={(e) => setAudience(e.target.value)}
            disabled={loading}
            className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 bg-slate-50/50"
          />
        </div>

        {error && (
          <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-start space-x-2 text-rose-800 text-xs">
            <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-bold">Grounding Safeguard Notice:</span> {error}
            </div>
          </div>
        )}

        <div className="flex justify-end pt-2">
          <button
            onClick={() => handleGenerate()}
            disabled={loading || !topic.trim()}
            className="flex items-center space-x-2 bg-amber-600 hover:bg-amber-700 text-white px-6 py-2.5 rounded-xl font-semibold text-sm transition-colors shadow-sm disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Synthesizing Atomic Essay (200-300w)...</span>
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
        <h3 className="text-sm font-bold text-slate-800 flex items-center space-x-2">
          <BookOpen className="w-4 h-4 text-amber-600" />
          <span>Curated Growth Frameworks (Instant Generation)</span>
        </h3>
        <p className="text-xs text-slate-500">
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
              className="text-left p-4 rounded-xl border border-slate-200 bg-white hover:border-amber-400 hover:shadow-sm transition-all group disabled:opacity-50 flex items-center justify-between"
            >
              <div>
                <span className="text-[10px] font-semibold uppercase tracking-wider text-amber-700 bg-amber-50 px-2 py-0.5 rounded">
                  {item.guest}
                </span>
                <h4 className="text-xs font-semibold text-slate-800 group-hover:text-amber-800 mt-1">
                  {item.title}
                </h4>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-amber-600 group-hover:translate-x-0.5 transition-all flex-shrink-0 ml-2" />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
