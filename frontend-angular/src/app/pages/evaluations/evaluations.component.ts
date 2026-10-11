import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RepositoryService } from '../../services/repository.service';
import { ApiService } from '../../services/api.service';
import { EvaluationSummary } from '../../models/types';
import { IconComponent } from '../../components/common/icon/icon.component';

@Component({
  selector: 'app-evaluations',
  standalone: true,
  imports: [CommonModule, IconComponent],
  template: `
    <div class="p-8 space-y-6 max-w-6xl mx-auto">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-slate-100 tracking-tight flex items-center gap-2">
            <app-icon name="chart" class="w-6 h-6 text-emerald-400"></app-icon>
            <span>RAG Retrieval & Evaluation Quality Framework</span>
          </h1>
          <p class="text-sm text-slate-400 mt-1">
            Empirical benchmark metrics evaluating context precision, recall, groundedness, and citation accuracy.
          </p>
        </div>

        <button
          (click)="handleRunEval()"
          [disabled]="isLoading || !activeRepository"
          class="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg font-medium text-sm transition-all shadow-md shadow-emerald-600/20"
        >
          <app-icon name="refresh" [class]="'w-4 h-4 ' + (isLoading ? 'animate-spin' : '')"></app-icon>
          <span>{{ isLoading ? 'Running Benchmark...' : 'Run Evaluation Benchmark' }}</span>
        </button>
      </div>

      <div *ngIf="evalData" class="space-y-6">
        <!-- Metric Cards -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-5">
          <div class="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-1">
            <div class="text-xs text-slate-400 font-medium">Context Precision</div>
            <div class="text-3xl font-bold text-blue-400">{{ Math.round(evalData.precision_score * 100) }}%</div>
            <div class="text-[11px] text-slate-500">Relevant chunks retrieved</div>
          </div>

          <div class="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-1">
            <div class="text-xs text-slate-400 font-medium">Context Recall</div>
            <div class="text-3xl font-bold text-emerald-400">{{ Math.round(evalData.recall_score * 100) }}%</div>
            <div class="text-[11px] text-slate-500">Coverage of standard expected files</div>
          </div>

          <div class="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-1">
            <div class="text-xs text-slate-400 font-medium">Answer Groundedness</div>
            <div class="text-3xl font-bold text-purple-400">{{ Math.round(evalData.groundedness_score * 100) }}%</div>
            <div class="text-[11px] text-slate-500">Zero hallucination score</div>
          </div>

          <div class="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-1">
            <div class="text-xs text-slate-400 font-medium">Citation Accuracy</div>
            <div class="text-3xl font-bold text-amber-400">{{ Math.round(evalData.citation_accuracy * 100) }}%</div>
            <div class="text-[11px] text-slate-500">Source line resolution</div>
          </div>
        </div>

        <!-- Question Benchmark Results Table -->
        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
          <h3 class="font-bold text-slate-100 text-base">Benchmark Question Test Suite</h3>
          <div class="space-y-3">
            <div *ngFor="let res of evalData.results" class="bg-slate-950 border border-slate-800 p-4 rounded-xl space-y-2">
              <div class="flex items-center justify-between">
                <h4 class="font-medium text-slate-200 text-sm">{{ res.question }}</h4>
                <span class="text-xs text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded font-mono">
                  Precision: {{ Math.round(res.precision * 100) }}% | Recall: {{ Math.round(res.recall * 100) }}%
                </span>
              </div>

              <div class="text-xs text-slate-400 space-y-1 font-mono">
                <div>Expected: {{ res.expected.join(', ') }}</div>
                <div>Retrieved: {{ res.retrieved.join(', ') }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `
})
export class EvaluationsComponent implements OnInit {
  private repoService = inject(RepositoryService);
  private api = inject(ApiService);

  evalData: EvaluationSummary | null = null;
  isLoading = false;
  Math = Math;

  get activeRepository() {
    return this.repoService.activeRepository;
  }

  ngOnInit(): void {
    this.repoService.activeRepository$.subscribe((repo) => {
      if (repo) {
        this.fetchEval(repo.id);
      }
    });
  }

  fetchEval(repoId: string): void {
    this.isLoading = true;
    this.api.getEvaluation(repoId).subscribe({
      next: (data) => {
        this.evalData = data;
        this.isLoading = false;
      },
      error: (err) => {
        console.error(err);
        this.isLoading = false;
      }
    });
  }

  handleRunEval(): void {
    const repo = this.activeRepository;
    if (!repo) return;
    this.isLoading = true;

    this.api.triggerEvaluation(repo.id).subscribe({
      next: (data) => {
        this.evalData = data;
        this.isLoading = false;
      },
      error: (err) => {
        console.error(err);
        this.isLoading = false;
      }
    });
  }
}
