import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ChatMessage } from '../components/ChatMessage';
import { ChatMessageItem, SourceCitation } from '../types/api';

describe('ChatMessage Component', () => {
  it('renders a user message correctly', () => {
    const userMessage: ChatMessageItem = {
      id: 'msg-1',
      role: 'user',
      content: 'What is cohort retention?',
      timestamp: new Date('2026-10-09T12:00:00Z'),
    };

    render(<ChatMessage message={userMessage} onSelectCitation={vi.fn()} />);
    expect(screen.getByText('What is cohort retention?')).toBeDefined();
  });

  it('renders an assistant message with citations and handles citation click', () => {
    const onSelectCitation = vi.fn();
    const mockCitation: SourceCitation = {
      chunk_id: 'c-1',
      transcript_id: 't-1',
      transcript_title: 'Elena Verna on Growth Accounting',
      source_filename: 'growth.md',
      chunk_index: 0,
      chunk_text: 'Retention is the foundation of growth.',
      score: 32.5,
      metadata: { guest: 'Elena Verna' },
    };

    const assistantMessage: ChatMessageItem = {
      id: 'msg-2',
      role: 'assistant',
      content: 'According to Elena Verna, retention is foundational.',
      timestamp: new Date('2026-10-09T12:01:00Z'),
      provider: 'ollama',
      model: 'llama3:8b',
      agent_framework: 'pi_coding_agent',
      sources: [mockCitation],
      insufficient_evidence: false,
    };

    render(<ChatMessage message={assistantMessage} onSelectCitation={onSelectCitation} />);

    expect(screen.getByText(/According to Elena Verna/i)).toBeDefined();
    expect(screen.getByText('Elena Verna on Growth Accounting')).toBeDefined();
    expect(screen.getByText('ollama/llama3:8b')).toBeDefined();
    expect(screen.getByText('pi_coding_agent')).toBeDefined();

    // Click citation pill
    const citationBtn = screen.getByTitle(/Inspect transcript excerpt/i);
    fireEvent.click(citationBtn);
    expect(onSelectCitation).toHaveBeenCalledWith(mockCitation);
  });

  it('displays the insufficient evidence warning when flagged', () => {
    const refusalMessage: ChatMessageItem = {
      id: 'msg-3',
      role: 'assistant',
      content: 'I could not find sufficient information in the transcripts.',
      timestamp: new Date('2026-10-09T12:02:00Z'),
      insufficient_evidence: true,
    };

    render(<ChatMessage message={refusalMessage} onSelectCitation={vi.fn()} />);
    expect(screen.getByText(/Strict Grounding Active:/i)).toBeDefined();
  });
});
