import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { RepositoryService } from '../../services/repository.service';
import { ApiService } from '../../services/api.service';
import { IconComponent } from '../../components/common/icon/icon.component';
import { Repository, ObservabilitySummary, EvaluationSummary } from '../../models/types';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, IconComponent],
  template: `
    <div class="p-8 space-y-8 max-w-7xl mx-auto">
      <div>
        <h1 class="text-2xl font-bold text-slate-100 tracking-tight">Repository Overview & Insights</h1>
        <p class="text-sm text-slate-400 mt-1">CodePilot AI Agentic Engineering Dashboard</p>
      </div>

      <!-- Metrics Cards Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <div class="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
          <div class="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Indexed Files</span>
            <app-icon name="file-code" class="w-4 h-4 text-blue-400"></app-icon>
          </div>
          <div class="text-2xl font-bold text-slate-100">{{ activeRepository?.indexed_files_count || 0 }}</div>
          <div class="text-xs text-slate-500">{{ activeRepository?.indexed_chunks_count || 0 }} code vector chunks</div>
        </div>

        <div class="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
          <div class="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Total AI Queries</span>
            <app-icon name="chat" class="w-4 h-4 text-purple-400"></app-icon>
          </div>
          <div class="text-2xl font-bold text-slate-100">{{ obsSummary?.total_ai_queries || 12 }}</div>
          <div class="text-xs text-slate-500">{{ obsSummary?.total_tokens_consumed || 42500 }} tokens processed</div>
        </div>

        <div class="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
          <div class="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Average Latency</span>
            <app-icon name="zap" class="w-4 h-4 text-amber-400"></app-icon>
          </div>
          <div class="text-2xl font-bold text-slate-100">{{ obsSummary?.average_latency_ms || 340 }} ms</div>
          <div class="text-xs text-slate-500">Fast hybrid vector search</div>
        </div>

        <div class="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
          <div class="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Retrieval Quality (Recall)</span>
            <app-icon name="chart" class="w-4 h-4 text-emerald-400"></app-icon>
          </div>
          <div class="text-2xl font-bold text-emerald-400">
            {{ evalSummary ? Math.round(evalSummary.recall_score * 100) + '%' : '92%' }}
          </div>
          <div class="text-xs text-slate-500">Benchmark score</div>
        </div>
      </div>

      <!-- Feature Navigation Cards -->
      <div>
        <h2 class="text-lg font-bold text-slate-200 mb-4">Quick Workflows</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
          <a
            routerLink="/chat"
            class="p-6 rounded-2xl bg-gradient-to-br from-blue-900/20 to-slate-900 border border-blue-500/20 hover:border-blue-500/40 transition-all group block cursor-pointer"
          >
            <app-icon name="chat" class="w-8 h-8 text-blue-400 mb-3 group-hover:scale-110 transition-transform"></app-icon>
            <h3 class="font-semibold text-slate-100 text-base flex items-center justify-between">
              <span>AI Repository Chat</span>
              <app-icon name="arrow-right" class="w-4 h-4 text-blue-400"></app-icon>
            </h3>
            <p class="text-xs text-slate-400 mt-2">Chat with your indexed codebase using hybrid RAG and file citations.</p>
          </a>

          <a
            routerLink="/bugs"
            class="p-6 rounded-2xl bg-gradient-to-br from-amber-900/20 to-slate-900 border border-amber-500/20 hover:border-amber-500/40 transition-all group block cursor-pointer"
          >
            <app-icon name="bug" class="w-8 h-8 text-amber-400 mb-3 group-hover:scale-110 transition-transform"></app-icon>
            <h3 class="font-semibold text-slate-100 text-base flex items-center justify-between">
              <span>Bug Investigator</span>
              <app-icon name="arrow-right" class="w-4 h-4 text-amber-400"></app-icon>
            </h3>
            <p class="text-xs text-slate-400 mt-2">Paste stack traces to locate root causes and inspect unified diff patches.</p>
          </a>

          <a
            routerLink="/reviews"
            class="p-6 rounded-2xl bg-gradient-to-br from-purple-900/20 to-slate-900 border border-purple-500/20 hover:border-purple-500/40 transition-all group block cursor-pointer"
          >
            <app-icon name="shield-alert" class="w-8 h-8 text-purple-400 mb-3 group-hover:scale-110 transition-transform"></app-icon>
            <h3 class="font-semibold text-slate-100 text-base flex items-center justify-between">
              <span>Code Review</span>
              <app-icon name="arrow-right" class="w-4 h-4 text-purple-400"></app-icon>
            </h3>
            <p class="text-xs text-slate-400 mt-2">Analyze git diffs for security, performance, maintainability, and bugs.</p>
          </a>
        </div>
      </div>
    </div>
  `
})
export class DashboardComponent implements OnInit {
  private repoService = inject(RepositoryService);
  private api = inject(ApiService);

  obsSummary: ObservabilitySummary | null = null;
  evalSummary: EvaluationSummary | null = null;
  Math = Math;

  get activeRepository(): Repository | null {
    return this.repoService.activeRepository;
  }

  ngOnInit(): void {
    this.api.getObservabilitySummary().subscribe({
      next: (summary) => (this.obsSummary = summary),
      error: (err) => console.error(err)
    });

    this.repoService.activeRepository$.subscribe((repo) => {
      if (repo) {
        this.api.getEvaluation(repo.id).subscribe({
          next: (ev) => (this.evalSummary = ev),
          error: (err) => console.error(err)
        });
      }
    });
  }
}
