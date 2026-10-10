import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ModelSelector } from '../components/ModelSelector';

describe('ModelSelector Component', () => {
  it('renders with initial values', () => {
    render(
      <ModelSelector
        provider="ollama"
        setProvider={vi.fn()}
        model="llama3:8b"
        setModel={vi.fn()}
        agentFramework="anthropic_tool_agent"
        setAgentFramework={vi.fn()}
      />
    );

    expect(screen.getByText('Inference Settings')).toBeDefined();
    const select = screen.getByLabelText(/Provider:/i) as HTMLSelectElement;
    expect(select.value).toBe('ollama');
  });

  it('triggers provider and model reset when switching to Anthropic', () => {
    const setProvider = vi.fn();
    const setModel = vi.fn();

    render(
      <ModelSelector
        provider="ollama"
        setProvider={setProvider}
        model="llama3:8b"
        setModel={setModel}
        agentFramework="anthropic_tool_agent"
        setAgentFramework={vi.fn()}
      />
    );

    const providerSelect = screen.getByLabelText(/Provider:/i);
    fireEvent.change(providerSelect, { target: { value: 'anthropic' } });

    expect(setProvider).toHaveBeenCalledWith('anthropic');
    expect(setModel).toHaveBeenCalledWith('claude-3-5-sonnet-20241022');
  });

  it('allows selecting Pi Coding Agent framework', () => {
    const setFramework = vi.fn();

    render(
      <ModelSelector
        provider="ollama"
        setProvider={vi.fn()}
        model="llama3:8b"
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
