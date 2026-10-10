export interface SourceCitation {
  chunk_id: string;
  transcript_id: string;
  transcript_title: string;
  source_filename: string;
  chunk_index: number;
  chunk_text: string;
  score: number;
  metadata: {
    guest?: string;
    episode?: number | string;
    topic?: string;
    synthetic_test_data?: boolean;
    start_char?: number;
    end_char?: number;
    [key: string]: any;
  };
}

export interface ChatRequest {
  message: string;
  session_id?: string;
  provider?: string;
  model?: string;
  agent_framework?: string;
}

export interface ChatResponse {
  session_id: string;
  message: string;
  role: string;
  provider: string;
  model: string;
  agent_framework?: string;
  sources: SourceCitation[];
  insufficient_evidence: boolean;
  created_at?: string;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
  database: string;
}

export interface SearchResultChunk {
  chunk_id: string;
  transcript_id: string;
  transcript_title: string;
  source_filename: string;
  chunk_index: number;
  chunk_text: string;
  score: number;
  metadata: Record<string, any>;
}

export interface SearchResponse {
  query: string;
  total_results: number;
  results: SearchResultChunk[];
}

export interface Ship30Request {
  topic: string;
  target_audience?: string;
  provider?: string;
  model?: string;
}

export interface Ship30Response {
  title: string;
  hook: string;
  word_count: number;
  within_constraints: boolean;
  content_markdown: string;
  content_html: string;
  guest_attribution: string;
  sources: SourceCitation[];
  created_at: string;
}

export interface ChatMessageItem {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  provider?: string;
  model?: string;
  agent_framework?: string;
  sources?: SourceCitation[];
  insufficient_evidence?: boolean;
  isError?: boolean;
}
