import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Navbar } from '../components/Navbar';

describe('Navbar Component', () => {
  it('renders application title and branding', () => {
    render(
      <Navbar
        activeTab="chat"
        setActiveTab={vi.fn()}
        health={{ status: 'running', timestamp: '2026-10-09T00:00:00Z', version: '1.0.0', database: 'available' }}
        healthLoading={false}
        sessionId={null}
        onResetSession={vi.fn()}
      />
    );

    expect(screen.getByText('The Lenny Growth Assistant')).toBeDefined();
    expect(screen.getByText('Grounded RAG')).toBeDefined();
  });

  it('switches tabs when clicked', () => {
    const setActiveTab = vi.fn();
    render(
      <Navbar
        activeTab="chat"
        setActiveTab={setActiveTab}
        health={null}
        healthLoading={false}
        sessionId={null}
        onResetSession={vi.fn()}
      />
    );

    const transcriptsTab = screen.getByText('Transcripts');
    fireEvent.click(transcriptsTab);
    expect(setActiveTab).toHaveBeenCalledWith('knowledge');

    const ship30Tab = screen.getByText('Ship 30 Essays');
    fireEvent.click(ship30Tab);
    expect(setActiveTab).toHaveBeenCalledWith('ship30');
  });

  it('shows New Session button when sessionId is active', () => {
    const onReset = vi.fn();
    render(
      <Navbar
        activeTab="chat"
        setActiveTab={vi.fn()}
        health={null}
        healthLoading={false}
        sessionId="test-session-123"
        onResetSession={onReset}
      />
    );

    const resetButton = screen.getByTitle('Reset conversation session');
    expect(resetButton).toBeDefined();
    fireEvent.click(resetButton);
    expect(onReset).toHaveBeenCalled();
  });
});
