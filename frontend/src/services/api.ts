import { ChatRequest, ChatResponse, HealthResponse, SearchResponse } from '../types/api';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

export async function checkHealth(): Promise<HealthResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/health`);
    if (!res.ok) {
      const errorText = await res.text();
      throw new ApiError(res.status, `Health check failed: ${errorText}`);
    }
    return await res.json();
  } catch (err: any) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(0, err.message || 'Unable to connect to backend server');
  }
}

export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const errJson = await res.json();
      if (errJson && errJson.detail) {
        errorDetail = errJson.detail;
      }
    } catch {
      // Non-JSON error response fallback
      const text = await res.text();
      if (text) errorDetail = text;
    }
    throw new ApiError(res.status, errorDetail);
  }

  return await res.json();
}

export async function searchTranscripts(query: string, limit = 5): Promise<SearchResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/sources/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query, limit }),
  });

  if (!res.ok) {
    let errorDetail = `Search failed with status ${res.status}`;
    try {
      const errJson = await res.json();
      if (errJson && errJson.detail) {
        errorDetail = errJson.detail;
      }
    } catch {
      // Fallback
    }
    throw new ApiError(res.status, errorDetail);
  }

  return await res.json();
}

export async function generateShip30Essay(request: import('../types/api').Ship30Request): Promise<import('../types/api').Ship30Response> {
  const res = await fetch(`${API_BASE_URL}/api/v1/skills/ship30-essay`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!res.ok) {
    let errorDetail = `Essay generation failed with status ${res.status}`;
    try {
      const errJson = await res.json();
      if (errJson && errJson.detail) {
        errorDetail = errJson.detail;
      }
    } catch {
      const text = await res.text();
      if (text) errorDetail = text;
    }
    throw new ApiError(res.status, errorDetail);
  }

  return await res.json();
}
