import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
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
  AIRunMetric,
  ObservabilitySummary
} from '../models/types';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private http = inject(HttpClient);
  private readonly baseUrl = '/api/v1';

  // Auth
  register(data: any): Observable<{ access_token: string; user: User }> {
    return this.http.post<{ access_token: string; user: User }>(`${this.baseUrl}/auth/register`, data);
  }

  login(data: any): Observable<{ access_token: string; user: User }> {
    return this.http.post<{ access_token: string; user: User }>(`${this.baseUrl}/auth/login`, data);
  }

  getMe(): Observable<User> {
    return this.http.get<User>(`${this.baseUrl}/auth/me`);
  }

  // Workspaces
  getWorkspaces(): Observable<Workspace[]> {
    return this.http.get<Workspace[]>(`${this.baseUrl}/workspaces`);
  }

  createWorkspace(data: { name: string; slug: string }): Observable<Workspace> {
    return this.http.post<Workspace>(`${this.baseUrl}/workspaces`, data);
  }

  // Repositories
  getRepositories(workspaceId?: string): Observable<Repository[]> {
    const query = workspaceId ? `?workspace_id=${workspaceId}` : '';
    return this.http.get<Repository[]>(`${this.baseUrl}/repositories${query}`);
  }

  createRepository(data: any): Observable<Repository> {
    return this.http.post<Repository>(`${this.baseUrl}/repositories`, data);
  }

  triggerIndexing(repoId: string): Observable<{ status: string }> {
    return this.http.post<{ status: string }>(`${this.baseUrl}/repositories/${repoId}/index`, {});
  }

  getFiles(repoId: string): Observable<FileNode[]> {
    return this.http.get<FileNode[]>(`${this.baseUrl}/repositories/${repoId}/files`);
  }

  getFileDetail(repoId: string, filePath: string): Observable<FileDetail> {
    return this.http.get<FileDetail>(`${this.baseUrl}/repositories/${repoId}/files/${encodeURIComponent(filePath)}`);
  }

  // AI Workflows
  chat(repoId: string, message: string): Observable<StructuredAIResponse> {
    return this.http.post<StructuredAIResponse>(`${this.baseUrl}/repositories/${repoId}/chat`, { message });
  }

  runAgent(repoId: string, message: string): Observable<AgentRunResult> {
    return this.http.post<AgentRunResult>(`${this.baseUrl}/repositories/${repoId}/agent`, { message });
  }

  analyzeBug(repoId: string, data: { error_message: string; stack_trace?: string; file_path?: string }): Observable<BugAnalysisResponse> {
    return this.http.post<BugAnalysisResponse>(`${this.baseUrl}/repositories/${repoId}/bug-analysis`, data);
  }

  reviewCode(repoId: string, data: { git_diff?: string }): Observable<CodeReviewResponse> {
    return this.http.post<CodeReviewResponse>(`${this.baseUrl}/repositories/${repoId}/code-review`, data);
  }

  generateTests(repoId: string, data: { file_path: string; framework: string }): Observable<TestGenerationResponse> {
    return this.http.post<TestGenerationResponse>(`${this.baseUrl}/repositories/${repoId}/generate-tests`, data);
  }

  generateDoc(repoId: string, data: { doc_type: string }): Observable<DocGenerationResponse> {
    return this.http.post<DocGenerationResponse>(`${this.baseUrl}/repositories/${repoId}/documentation`, data);
  }

  // Evaluation & Observability
  getEvaluation(repoId: string): Observable<EvaluationSummary> {
    return this.http.get<EvaluationSummary>(`${this.baseUrl}/evaluations/${repoId}`);
  }

  triggerEvaluation(repoId: string): Observable<EvaluationSummary> {
    return this.http.post<EvaluationSummary>(`${this.baseUrl}/evaluations/run/${repoId}`, {});
  }

  getAIRuns(): Observable<AIRunMetric[]> {
    return this.http.get<AIRunMetric[]>(`${this.baseUrl}/ai-runs`);
  }

  getObservabilitySummary(): Observable<ObservabilitySummary> {
    return this.http.get<ObservabilitySummary>(`${this.baseUrl}/ai-runs/metrics/summary`);
  }
}
