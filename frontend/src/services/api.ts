import {
  User,
  Workspace,
  Repository,
  FileNode,
  FileDetail,
  StructuredAIResponse,
  AgentRunResult,
  BugAnalysisResponse,
  CodeReviewResponse,
  TestGenerationResponse,
  DocGenerationResponse,
  EvaluationSummary,
  AIRunMetric
} from '../types';

const API_BASE = '/api/v1';

async function fetchJson<T>(url: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Network error' }));
    throw new Error(errorData.detail?.message || errorData.detail || 'API request failed');
  }

  return await response.json();
}

export const api = {
  // Auth
  register: (data: any) => fetchJson<{ access_token: string; user: User }>('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
  login: (data: any) => fetchJson<{ access_token: string; user: User }>('/auth/login', { method: 'POST', body: JSON.stringify(data) }),
  getMe: () => fetchJson<User>('/auth/me'),

  // Workspaces
  getWorkspaces: () => fetchJson<Workspace[]>('/workspaces'),
  createWorkspace: (data: { name: string; slug: string }) => fetchJson<Workspace>('/workspaces', { method: 'POST', body: JSON.stringify(data) }),

  // Repositories
  getRepositories: (workspaceId?: string) => fetchJson<Repository[]>(`/repositories${workspaceId ? `?workspace_id=${workspaceId}` : ''}`),
  createRepository: (data: any) => fetchJson<Repository>('/repositories', { method: 'POST', body: JSON.stringify(data) }),
  triggerIndexing: (repoId: string) => fetchJson<{ status: string }>(`/repositories/${repoId}/index`, { method: 'POST' }),
  getFiles: (repoId: string) => fetchJson<FileNode[]>(`/repositories/${repoId}/files`),
  getFileDetail: (repoId: string, filePath: string) => fetchJson<FileDetail>(`/repositories/${repoId}/files/${encodeURIComponent(filePath)}`),

  // AI Workflows
  chat: (repoId: string, message: string) => fetchJson<StructuredAIResponse>(`/repositories/${repoId}/chat`, { method: 'POST', body: JSON.stringify({ message }) }),
  runAgent: (repoId: string, message: string) => fetchJson<AgentRunResult>(`/repositories/${repoId}/agent`, { method: 'POST', body: JSON.stringify({ message }) }),
  analyzeBug: (repoId: string, data: { error_message: string; stack_trace?: string; file_path?: string }) => fetchJson<BugAnalysisResponse>(`/repositories/${repoId}/bug-analysis`, { method: 'POST', body: JSON.stringify(data) }),
  reviewCode: (repoId: string, data: { git_diff?: string }) => fetchJson<CodeReviewResponse>(`/repositories/${repoId}/code-review`, { method: 'POST', body: JSON.stringify(data) }),
  generateTests: (repoId: string, data: { file_path: string; framework: string }) => fetchJson<TestGenerationResponse>(`/repositories/${repoId}/generate-tests`, { method: 'POST', body: JSON.stringify(data) }),
  generateDoc: (repoId: string, data: { doc_type: string }) => fetchJson<DocGenerationResponse>(`/repositories/${repoId}/documentation`, { method: 'POST', body: JSON.stringify(data) }),

  // Evaluation & Observability
  getEvaluation: (repoId: string) => fetchJson<EvaluationSummary>(`/evaluations/${repoId}`),
  triggerEvaluation: (repoId: string) => fetchJson<EvaluationSummary>(`/evaluations/run/${repoId}`, { method: 'POST' }),
  getAIRuns: () => fetchJson<AIRunMetric[]>('/ai-runs'),
  getObservabilitySummary: () => fetchJson<{ total_ai_queries: number; total_tokens_consumed: number; average_latency_ms: number; total_cost_usd: number; active_model: string }>('/ai-runs/metrics/summary'),
};
