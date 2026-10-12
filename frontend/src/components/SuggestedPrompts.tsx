import React from 'react';
import { ShieldAlert, Sparkles, TrendingUp, Compass, ArrowUpRight } from 'lucide-react';

interface SuggestedPromptsProps {
  onSelectPrompt: (prompt: string) => void;
  disabled?: boolean;
}

export const SuggestedPrompts: React.FC<SuggestedPromptsProps> = ({ onSelectPrompt, disabled }) => {
  const groundedPrompts = [
    {
      title: 'Elena Verna on Retention Accounting',
      query: 'What is the hierarchy of growth and retention accounting according to Elena Verna?',
      tag: 'Retention Operating Model',
      icon: TrendingUp,
    },
    {
      title: 'Cohort Retention vs Acquisition',
      query: 'Why does Elena Verna argue retention must precede acquisition in early startups?',
      tag: 'Product Strategy',
      icon: Compass,
    },
    {
      title: '14-Day Reverse Trial Mechanics',
      query: 'How does a reverse trial work compared to freemium and free trial models?',
      tag: 'B2B Growth Playbook',
      icon: Sparkles,
    },
  ];

  const testRefusalPrompt = {
    title: 'Anti-Hallucination Gate Test',
    query: 'Explain quantum thermodynamics and interstellar propulsion architectures.',
    tag: 'Strict Refusal Test',
    icon: ShieldAlert,
  };

  return (
    <div className="max-w-2xl mx-auto my-6 px-4 w-full">
      <div className="text-center mb-5">
        <h3 className="text-sm font-bold text-slate-200 tracking-tight">
          Explore Lenny's Growth Knowledge Base
        </h3>
        <p className="text-xs text-slate-400 mt-1">
          Select a sample query to test retrieval grounding or verify anti-hallucination safeguards:
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {groundedPrompts.map((p, idx) => {
          const Icon = p.icon;
          return (
            <button
              key={idx}
              disabled={disabled}
              onClick={() => onSelectPrompt(p.query)}
              className="text-left p-3.5 rounded-xl border border-white/[0.08] bg-dark-900/80 hover:border-amber-500/40 hover:bg-dark-850 hover:shadow-depth transition-all duration-200 group disabled:opacity-50 spatial-card"
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-semibold text-slate-200 group-hover:text-amber-300 transition-colors flex items-center">
                  <Icon className="w-3.5 h-3.5 mr-1.5 text-amber-400 flex-shrink-0" />
                  {p.title}
                </span>
                <ArrowUpRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-amber-400 transition-colors" />
              </div>
              <div className="mb-2">
                <span className="text-[10px] bg-amber-500/10 text-amber-400/90 border border-amber-500/20 px-1.5 py-0.5 rounded font-medium">
                  {p.tag}
                </span>
              </div>
              <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                "{p.query}"
              </p>
            </button>
          );
        })}

        {/* Anti-Hallucination Refusal Test */}
        <button
          disabled={disabled}
          onClick={() => onSelectPrompt(testRefusalPrompt.query)}
          className="text-left p-3.5 rounded-xl border border-rose-900/40 bg-rose-950/20 hover:border-rose-500/60 hover:bg-rose-950/30 hover:shadow-depth transition-all duration-200 group disabled:opacity-50 spatial-card"
        >
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs font-semibold text-rose-200 group-hover:text-rose-100 flex items-center">
              <ShieldAlert className="w-3.5 h-3.5 mr-1.5 text-rose-400 flex-shrink-0" />
              {testRefusalPrompt.title}
            </span>
            <span className="text-[10px] bg-rose-500/20 text-rose-300 border border-rose-500/30 px-1.5 py-0.5 rounded font-medium">
              Refusal Gate
            </span>
          </div>
          <p className="text-xs text-rose-300/80 line-clamp-2 leading-relaxed mt-3">
            "{testRefusalPrompt.query}"
          </p>
        </button>
      </div>
    </div>
  );
};
