import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RepositoryService } from '../../services/repository.service';
import { ApiService } from '../../services/api.service';
import { BugAnalysisResponse } from '../../models/types';
import { DiffViewerComponent } from '../../components/bug/diff-viewer/diff-viewer.component';
import { IconComponent } from '../../components/common/icon/icon.component';

@Component({
  selector: 'app-bug-analyzer',
  standalone: true,
  imports: [CommonModule, FormsModule, DiffViewerComponent, IconComponent],
  template: `
    <div class="p-8 space-y-6 max-w-6xl mx-auto">
      <div>
        <h1 class="text-2xl font-bold text-slate-100 tracking-tight flex items-center gap-2">
          <app-icon name="bug" class="w-6 h-6 text-amber-400"></app-icon>
          <span>Automated Bug Investigator</span>
        </h1>
        <p class="text-sm text-slate-400 mt-1">
          Paste error logs or stack traces to isolate root causes, locate affected files, and generate proposed diff patches.
        </p>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Input Form -->
        <form (ngSubmit)="handleAnalyze()" class="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4 shadow-sm">
          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-1">Error Message</label>
            <input
              type="text"
              required
              [(ngModel)]="errorMessage"
              name="errorMessage"
              class="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 font-mono focus:outline-none focus:border-amber-500"
            />
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-1">Stack Trace</label>
            <textarea
              rows="6"
              [(ngModel)]="stackTrace"
              name="stackTrace"
              class="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-slate-300 font-mono focus:outline-none focus:border-amber-500"
            ></textarea>
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-1">Target File (Optional)</label>
            <input
              type="text"
              [(ngModel)]="filePath"
              name="filePath"
              class="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 font-mono focus:outline-none focus:border-amber-500"
            />
          </div>

          <button
            type="submit"
            [disabled]="isLoading"
            class="w-full bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white font-medium py-3 rounded-lg text-sm transition-all shadow-md shadow-amber-600/20 flex items-center justify-center gap-2"
          >
            <app-icon [name]="isLoading ? 'loader' : 'sparkles'" [class]="'w-4 h-4 ' + (isLoading ? 'animate-spin' : '')"></app-icon>
            <span>{{ isLoading ? 'Investigating Repository...' : 'Investigate Bug' }}</span>
          </button>
        </form>

        <!-- Output Results -->
        <div class="space-y-4">
          <div *ngIf="analysis" class="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4 shadow-sm">
            <div class="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 class="font-bold text-slate-100 text-base">{{ analysis.error_summary }}</h3>
              <span class="text-xs bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2.5 py-1 rounded-full font-medium">
                Risk: {{ analysis.risk }}
              </span>
            </div>

            <div class="space-y-2">
              <h4 class="text-xs font-semibold text-slate-300">Likely Root Cause</h4>
              <p class="text-xs text-slate-300 bg-slate-950 p-3 rounded-lg border border-slate-800 leading-relaxed font-sans">
                {{ analysis.likely_root_cause }}
              </p>
            </div>

            <div class="space-y-2">
              <h4 class="text-xs font-semibold text-slate-300">Suggested Fix Strategy</h4>
              <p class="text-xs text-slate-300 bg-slate-950 p-3 rounded-lg border border-slate-800 leading-relaxed font-sans">
                {{ analysis.suggested_fix }}
              </p>
            </div>

            <div *ngIf="analysis.proposed_patch" class="pt-2">
              <app-diff-viewer [patch]="analysis.proposed_patch"></app-diff-viewer>
            </div>
          </div>

          <div
            *ngIf="!analysis"
            class="h-full bg-slate-900/40 border border-dashed border-slate-800 rounded-2xl flex flex-col items-center justify-center text-slate-500 p-8 text-center text-xs"
          >
            <app-icon name="alert-triangle" class="w-8 h-8 text-slate-600 mb-2"></app-icon>
            <p>Submit stack trace details to generate an empirical root-cause diagnosis and diff proposal.</p>
          </div>
        </div>
      </div>
    </div>
  `
})
export class BugAnalyzerComponent {
  private repoService = inject(RepositoryService);
  private api = inject(ApiService);

  errorMessage = "TypeError: Cannot read properties of undefined (reading 'map') in create_order idempotency check";
  stackTrace = `Traceback (most recent call last):
  File "backend/routes/order_routes.py", line 28, in create_order
    if x_idempotency_key in PROCESSED_KEYS:
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "backend/services/payment_gateway.py", line 42, in charge
    response = await res.json()
UnhandledPromiseRejection: Cannot read properties of undefined`;
  filePath = 'backend/routes/order_routes.py';
  analysis: BugAnalysisResponse | null = null;
  isLoading = false;

  handleAnalyze(): void {
    const repo = this.repoService.activeRepository;
    if (!repo) return;
    this.isLoading = true;

    this.api.analyzeBug(repo.id, {
      error_message: this.errorMessage,
      stack_trace: this.stackTrace,
      file_path: this.filePath
    }).subscribe({
      next: (res) => {
        this.analysis = res;
        this.isLoading = false;
      },
      error: (err) => {
        console.error(err);
        this.isLoading = false;
      }
    });
  }
}
