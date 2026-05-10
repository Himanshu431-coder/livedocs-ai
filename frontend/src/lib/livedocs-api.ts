const BASE = "/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(await res.text() || `HTTP ${res.status}`);
  return res.json();
}

export interface Citation {
  source_file: string;
  chunk_text: string;
  relevance_score: number;
  chunk_index: number;
}

export interface AgentStep {
  agent: "orchestrator" | "researcher" | "analyst" | "synthesizer" | "verifier";
  action: string;
  thought: string;
  result: string;
  latency_ms: number;
}

export interface QueryResponse {
  answer: string;
  citations: Citation[];
  agent_trace: AgentStep[];
  complexity: string;
  total_latency_ms: number;
  documents_searched: number;
  chunks_retrieved: number;
  model_used: string;
  conversation_id: string;
  confidence_score: number;
}

export interface DocItem {
  filename: string;
  size_bytes: number;
  modified_at: string;
  doc_type: string;
}

export interface Stats {
  total_chunks: number;
  total_documents: number;
  documents: string[];
  bm25_indexed: boolean;
}

export interface MCPTool {
  name: string;
  description: string;
  inputSchema: {
    type: string;
    properties: Record<string, { type: string; description: string; required?: boolean }>;
    required: string[];
  };
}

export interface MCPManifest {
  server: { name: string; version: string };
  tools: MCPTool[];
  tool_count: number;
}

export const api = {
  query: (params: { question: string; workspace: string; conversation_id?: string }): Promise<QueryResponse> =>
    request("/query", { method: "POST", body: JSON.stringify({ ...params, agent_mode: true }) }),

  listDocuments: (workspace: string): Promise<{ documents: DocItem[]; total: number; workspace: string }> =>
    request(`/documents?workspace=${workspace}`),

  addDocument: (params: { filename: string; content: string; workspace: string }): Promise<{ status: string; filename: string }> =>
    request("/documents", { method: "POST", body: JSON.stringify(params) }),

  deleteDocument: (filename: string, workspace: string): Promise<{ status: string }> =>
    request(`/documents/${filename}?workspace=${workspace}`, { method: "DELETE" }),

  stats: (workspace: string): Promise<Stats> =>
    request(`/analytics/stats?workspace=${workspace}`),

  mcpManifest: (): Promise<MCPManifest> =>
    request("/mcp/manifest"),
};