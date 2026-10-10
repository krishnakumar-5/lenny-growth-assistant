import React from 'react';
import { ShieldAlert } from 'lucide-react';

interface SuggestedPromptsProps {
  onSelectPrompt: (prompt: string) => void;
  disabled?: boolean;
}

export const SuggestedPrompts: React.FC<SuggestedPromptsProps> = ({ onSelectPrompt, disabled }) => {
  const groundedPrompts = [
    {
      title: 'Elena Verna on Growth Accounting',
      query: 'What is the hierarchy of growth and retention accounting according to Elena Verna?',
      tag: 'Grounded Query',
    },
    {
      title: 'Cohort Retention Metrics',
      query: 'How do you measure cohort retention over time?',
      tag: 'Product Strategy',
    },
    {
      title: 'Product-Led Growth Levers',
      query: 'What are the main growth levers in product-led organizations?',
      tag: 'Playbook',
    },
  ];

  const testRefusalPrompt = {
    title: 'Anti-Hallucination Gate Test',
    query: 'Explain quantum entanglement and supercomputing architecture.',
    tag: 'Test Refusal (Zero Grounding)',
  };

  return (
    <div className="max-w-2xl mx-auto my-6 px-4">
      <div className="text-center mb-4">
        <h3 className="text-base font-semibold text-slate-900">
          Explore Lenny's Growth Knowledge Base
        </h3>
        <p className="text-xs text-slate-500 mt-1">
          Select a sample query to test retrieval grounding or verify anti-hallucination safeguards:
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
        {groundedPrompts.map((p, idx) => (
          <button
            key={idx}
            disabled={disabled}
            onClick={() => onSelectPrompt(p.query)}
            className="text-left p-3 rounded-xl border border-slate-200 bg-white hover:border-amber-400 hover:shadow-md transition-all group disabled:opacity-50"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-semibold text-slate-800 group-hover:text-amber-700">
                {p.title}
              </span>
              <span className="text-[10px] bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded font-medium">
                {p.tag}
              </span>
            </div>
            <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed">
              "{p.query}"
            </p>
          </button>
        ))}

        {/* Anti-Hallucination Refusal Test */}
        <button
          disabled={disabled}
          onClick={() => onSelectPrompt(testRefusalPrompt.query)}
          className="text-left p-3 rounded-xl border border-rose-200 bg-rose-50/40 hover:border-rose-400 hover:bg-rose-50 hover:shadow-md transition-all group disabled:opacity-50"
        >
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-semibold text-rose-900 group-hover:text-rose-700 flex items-center">
              <ShieldAlert className="w-3.5 h-3.5 mr-1 text-rose-500" />
              {testRefusalPrompt.title}
            </span>
            <span className="text-[10px] bg-rose-100 text-rose-700 px-1.5 py-0.5 rounded font-medium">
              Refusal Gate
            </span>
          </div>
          <p className="text-xs text-rose-700/80 line-clamp-2 leading-relaxed">
            "{testRefusalPrompt.query}"
          </p>
        </button>
      </div>
    </div>
  );
};
