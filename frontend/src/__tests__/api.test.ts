import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { checkHealth, sendChatMessage, searchTranscripts, ApiError } from '../services/api';

describe('Frontend API Service', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it('checkHealth returns health data on 200 OK', async () => {
    const mockHealth = {
      status: 'healthy',
      timestamp: '2026-10-09T12:00:00Z',
      version: '1.0.0',
      database: 'available',
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockHealth,
    } as Response);

    const result = await checkHealth();
    expect(result.status).toBe('healthy');
    expect(result.database).toBe('available');
  });

  it('sendChatMessage sends request payload and returns ChatResponse', async () => {
    const mockResponse = {
      session_id: 'sess-123',
      message: 'Here is your grounded answer.',
      role: 'assistant',
      provider: 'ollama',
      model: 'llama3:8b',
      agent_framework: 'anthropic_tool_agent',
      sources: [],
      insufficient_evidence: false,
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    } as Response);

    const result = await sendChatMessage({
      message: 'What is growth?',
      provider: 'ollama',
      model: 'qwen2.5:3b',
    });

    expect(result.session_id).toBe('sess-123');
    expect(result.message).toBe('Here is your grounded answer.');
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/chat'),
      expect.objectContaining({
        body: JSON.stringify({
          message: 'What is growth?',
          provider: 'ollama',
          model: 'qwen2.5:3b',
        }),
      })
    );
  });

  it('sendChatMessage throws ApiError with status and detail on failure', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 503,
      json: async () => ({ detail: 'Ollama daemon is offline' }),
      text: async () => 'Ollama daemon is offline',
    } as unknown as Response);

    await expect(
      sendChatMessage({ message: 'Hello' })
    ).rejects.toThrowError(ApiError);
  });

  it('searchTranscripts calls search endpoint and returns results', async () => {
    const mockSearch = {
      query: 'retention',
      total_results: 1,
      results: [
        {
          chunk_id: 'c-1',
          transcript_id: 't-1',
          transcript_title: 'Growth Accounting',
          source_filename: 'file.md',
          chunk_index: 0,
          chunk_text: 'Text about retention',
          score: 25.0,
          metadata: {},
        },
      ],
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockSearch,
    } as Response);

    const result = await searchTranscripts('retention', 5);
    expect(result.total_results).toBe(1);
    expect(result.results[0].chunk_text).toBe('Text about retention');
  });

  it('listSessions retrieves saved sessions', async () => {
    const mockSessions = [
      {
        id: 'sess-1',
        title: 'Retention loops',
        created_at: '2026-10-10T00:00:00Z',
        updated_at: '2026-10-10T00:00:00Z',
        message_count: 2,
        last_message: 'Retention is key',
      },
    ];

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockSessions,
    } as Response);

    const { listSessions } = await import('../services/api');
    const result = await listSessions();
    expect(result.length).toBe(1);
    expect(result[0].title).toBe('Retention loops');
  });

  it('getSession retrieves session details and messages', async () => {
    const mockDetail = {
      id: 'sess-1',
      title: 'Retention loops',
      created_at: '2026-10-10T00:00:00Z',
      updated_at: '2026-10-10T00:00:00Z',
      messages: [
        { id: 'm-1', role: 'user', content: 'What is PLG?', created_at: '2026-10-10T00:00:00Z' },
        { id: 'm-2', role: 'assistant', content: 'PLG is...', created_at: '2026-10-10T00:00:01Z' },
      ],
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockDetail,
    } as Response);

    const { getSession } = await import('../services/api');
    const result = await getSession('sess-1');
    expect(result.id).toBe('sess-1');
    expect(result.messages.length).toBe(2);
  });
});
