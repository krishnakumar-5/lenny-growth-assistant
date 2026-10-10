import React from 'react';
import { Cpu, Bot, Settings2 } from 'lucide-react';

interface ModelSelectorProps {
  provider: string;
  setProvider: (p: string) => void;
  model: string;
  setModel: (m: string) => void;
  agentFramework: string;
  setAgentFramework: (f: string) => void;
  disabled?: boolean;
}

export const ModelSelector: React.FC<ModelSelectorProps> = ({
  provider,
  setProvider,
  model,
  setModel,
  agentFramework,
  setAgentFramework,
  disabled = false,
}) => {
  const handleProviderChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newProvider = e.target.value;
    setProvider(newProvider);
    if (newProvider === 'ollama') {
      setModel('llama3:8b');
    } else if (newProvider === 'anthropic') {
      setModel('claude-3-5-sonnet-20241022');
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-3 shadow-sm flex flex-wrap items-center justify-between gap-3 text-sm">
      <div className="flex items-center space-x-2 text-slate-700 font-medium">
        <Settings2 className="w-4 h-4 text-amber-600" />
        <span className="text-xs uppercase tracking-wider text-slate-500 font-semibold">Inference Settings</span>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        {/* Provider Selector */}
        <div className="flex items-center space-x-1.5">
          <label htmlFor="provider-select" className="text-xs text-slate-500 flex items-center">
            <Cpu className="w-3.5 h-3.5 mr-1 text-slate-400" /> Provider:
          </label>
          <select
            id="provider-select"
            value={provider}
            onChange={handleProviderChange}
            disabled={disabled}
            className="text-xs rounded-lg border-slate-200 bg-slate-50 py-1 px-2.5 text-slate-800 font-medium border focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 disabled:opacity-50"
          >
            <option value="ollama">Ollama (Local Offline)</option>
            <option value="anthropic">Anthropic (Cloud API)</option>
          </select>
        </div>

        {/* Model Selector */}
        <div className="flex items-center space-x-1.5">
          <label htmlFor="model-select" className="text-xs text-slate-500">
            Model:
          </label>
          {provider === 'ollama' ? (
            <select
              id="model-select"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              disabled={disabled}
              className="text-xs rounded-lg border-slate-200 bg-slate-50 py-1 px-2.5 text-slate-800 font-medium border focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 disabled:opacity-50"
            >
              <option value="llama3:8b">llama3:8b (Standard)</option>
              <option value="qwen2.5:3b">qwen2.5:3b (Local Host)</option>
              <option value="mistral:7b">mistral:7b</option>
              <option value="llama3.1:8b">llama3.1:8b</option>
            </select>
          ) : (
            <select
              id="model-select"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              disabled={disabled}
              className="text-xs rounded-lg border-slate-200 bg-slate-50 py-1 px-2.5 text-slate-800 font-medium border focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 disabled:opacity-50"
            >
              <option value="claude-3-5-sonnet-20241022">claude-3-5-sonnet-20241022</option>
              <option value="claude-3-5-haiku-20241022">claude-3-5-haiku-20241022</option>
            </select>
          )}
        </div>

        {/* Agent Framework Selector */}
        <div className="flex items-center space-x-1.5">
          <label htmlFor="framework-select" className="text-xs text-slate-500 flex items-center">
            <Bot className="w-3.5 h-3.5 mr-1 text-slate-400" /> Framework:
          </label>
          <select
            id="framework-select"
            value={agentFramework}
            onChange={(e) => setAgentFramework(e.target.value)}
            disabled={disabled}
            className="text-xs rounded-lg border-slate-200 bg-slate-50 py-1 px-2.5 text-slate-800 font-medium border focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 disabled:opacity-50"
          >
            <option value="anthropic_tool_agent">Anthropic Tool Agent</option>
            <option value="pi_coding_agent">Pi Coding Agent (CLI)</option>
          </select>
        </div>
      </div>
    </div>
  );
};
