import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Sidebar } from '../components/Sidebar';
import { SessionSummary } from '../types/api';

describe('Sidebar Component', () => {
  const mockSessions: SessionSummary[] = [
    {
      id: 'session-today-1',
      title: 'Elena Verna Retention Strategy',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      message_count: 4,
      last_message: 'Retention precedes acquisition.',
    },
    {
      id: 'session-old-1',
      title: 'Brian Balfour Growth Loops',
      created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
      updated_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
      message_count: 2,
      last_message: 'Loops compound over time.',
    },
  ];

  it('renders application branding, New Conversation button, and session items', () => {
    const onSelectSession = vi.fn();
    const onNewChat = vi.fn();

    render(
      <Sidebar
        sessions={mockSessions}
        activeSessionId="session-today-1"
        onSelectSession={onSelectSession}
        onNewChat={onNewChat}
        onDeleteSession={vi.fn()}
        onRenameSession={vi.fn()}
        activeTab="chat"
        setActiveTab={vi.fn()}
        isOpen={true}
        onToggleOpen={vi.fn()}
        provider="ollama"
        model="qwen2.5:3b"
      />
    );

    expect(screen.getByText('Lenny Growth AI')).toBeDefined();
    expect(screen.getByText('New Conversation')).toBeDefined();
    expect(screen.getByText('Elena Verna Retention Strategy')).toBeDefined();

    // Trigger New Chat
    const newChatBtn = screen.getByText('New Conversation');
    fireEvent.click(newChatBtn);
    expect(onNewChat).toHaveBeenCalled();
  });

  it('filters sessions by search query', () => {
    render(
      <Sidebar
        sessions={mockSessions}
        activeSessionId={null}
        onSelectSession={vi.fn()}
        onNewChat={vi.fn()}
        onDeleteSession={vi.fn()}
        onRenameSession={vi.fn()}
        activeTab="chat"
        setActiveTab={vi.fn()}
        isOpen={true}
        onToggleOpen={vi.fn()}
        provider="ollama"
        model="qwen2.5:3b"
      />
    );

    const searchInput = screen.getByPlaceholderText('Search past conversations...');
    fireEvent.change(searchInput, { target: { value: 'Balfour' } });

    expect(screen.queryByText('Elena Verna Retention Strategy')).toBeNull();
    expect(screen.getByText('Brian Balfour Growth Loops')).toBeDefined();
  });
});
