import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ModelSelector } from '../components/ModelSelector';

describe('ModelSelector Component', () => {
  it('renders with initial values and qwen2.5:3b as default model', () => {
    render(
      <ModelSelector
        provider="ollama"
        setProvider={vi.fn()}
        model="qwen2.5:3b"
        setModel={vi.fn()}
        agentFramework="anthropic_tool_agent"
        setAgentFramework={vi.fn()}
      />
    );

    expect(screen.getByText('Inference Settings')).toBeDefined();
    const select = screen.getByLabelText(/Provider:/i) as HTMLSelectElement;
    expect(select.value).toBe('ollama');

    const modelSelect = screen.getByLabelText(/Model:/i) as HTMLSelectElement;
    expect(modelSelect.value).toBe('qwen2.5:3b');
    expect(screen.getByText(/qwen2\.5:3b \(Local Host \/ Default\)/i)).toBeDefined();
  });

  it('triggers provider and model reset when switching to Anthropic and back to Ollama', () => {
    const setProvider = vi.fn();
    const setModel = vi.fn();

    const { rerender } = render(
      <ModelSelector
        provider="ollama"
        setProvider={setProvider}
        model="qwen2.5:3b"
        setModel={setModel}
        agentFramework="anthropic_tool_agent"
        setAgentFramework={vi.fn()}
      />
    );

    const providerSelect = screen.getByLabelText(/Provider:/i);
    fireEvent.change(providerSelect, { target: { value: 'anthropic' } });

    expect(setProvider).toHaveBeenCalledWith('anthropic');
    expect(setModel).toHaveBeenCalledWith('claude-3-5-sonnet-20241022');

    // Switch back to Ollama
    rerender(
      <ModelSelector
        provider="anthropic"
        setProvider={setProvider}
        model="claude-3-5-sonnet-20241022"
        setModel={setModel}
        agentFramework="anthropic_tool_agent"
        setAgentFramework={vi.fn()}
      />
    );
    const providerSelect2 = screen.getByLabelText(/Provider:/i);
    fireEvent.change(providerSelect2, { target: { value: 'ollama' } });

    expect(setProvider).toHaveBeenCalledWith('ollama');
    expect(setModel).toHaveBeenCalledWith('qwen2.5:3b');
  });

  it('allows selecting Pi Coding Agent framework', () => {
    const setFramework = vi.fn();

    render(
      <ModelSelector
        provider="ollama"
        setProvider={vi.fn()}
        model="qwen2.5:3b"
        setModel={vi.fn()}
        agentFramework="anthropic_tool_agent"
        setAgentFramework={setFramework}
      />
    );

    const frameworkSelect = screen.getByLabelText(/Framework:/i);
    fireEvent.change(frameworkSelect, { target: { value: 'pi_coding_agent' } });

    expect(setFramework).toHaveBeenCalledWith('pi_coding_agent');
  });
});
