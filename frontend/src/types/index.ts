export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  is_active: boolean;
}

export interface Workspace {
  id: string;
  name: string;
  slug: string;
  owner_id: string;
}


export interface Repository {
  id: string;
  workspace_id: string;
  name: string;
  description?: string;
  github_url?: string;
  default_branch: string;
  status: 'PENDING' | 'DOWNLOADING' | 'PARSING' | 'CHUNKING' | 'EMBEDDING' | 'INDEXING' | 'COMPLETED' | 'FAILED';
  indexed_files_count: number;
  indexed_chunks_count: number;
  summary?: Record<string, any>;
  last_indexed_at?: string;
}

export interface FileNode {
  id: string;
  path: string;
  language: string;
  size_bytes: number;
  summary?: string;
}

export interface FileDetail extends FileNode {
  content: string;
}

export interface Citation {
  file: string;
  start_line: number;
  end_line: number;
  relevance: number;
  snippet?: string;
}

export interface StructuredAIResponse {
  answer: string;
  citations: Citation[];
  confidence: number;
  reasoning_summary: string;
  limitations?: string[];
}

export interface AgentToolCall {
  tool_name: string;
  arguments: Record<string, any>;
  output: any;
}

export interface AgentRunResult {
  answer: string;
  citations: Citation[];
  steps_taken: AgentToolCall[];
  reasoning_summary: string;
}

export interface BugAnalysisResponse {
  error_summary: string;
  likely_root_cause: string;
  evidence: string;
  suggested_fix: string;
  risk: string;
  affected_files: string[];
  proposed_patch?: string;
  tests_to_add: string[];
}

export interface ReviewFinding {
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
  category: string;
  file: string;
  line: number;
  description: string;
  evidence: string;
  recommendation: string;
  confidence: number;
}

export interface CodeReviewResponse {
  summary: string;
  findings: ReviewFinding[];
}

export interface TestGenerationResponse {
  framework: string;
  test_code: string;
  explanation: string;
}

export interface DocGenerationResponse {
  doc_type: string;
  content: string;
}

export interface EvaluationSummary {
  id?: string;
  repository_id: string;
  precision_score: number;
  recall_score: number;
  groundedness_score: number;
  citation_accuracy: number;
  total_questions: number;
  results: any[];
  created_at?: string;
}

export interface AIRunMetric {
  id: string;
  feature: string;
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  latency_ms: number;
  estimated_cost_usd: number;
  status: string;
  created_at: string;
}
