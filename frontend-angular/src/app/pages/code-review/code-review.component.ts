import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RepositoryService } from '../../services/repository.service';
import { ApiService } from '../../services/api.service';
import { CodeReviewResponse, ReviewFinding } from '../../models/types';
import { IconComponent } from '../../components/common/icon/icon.component';

@Component({
  selector: 'app-code-review',
  standalone: true,
  imports: [CommonModule, FormsModule, IconComponent],
  template: `
    <div class="p-8 space-y-6 max-w-6xl mx-auto">
      <div>
        <h1 class="text-2xl font-bold text-slate-100 tracking-tight flex items-center gap-2">
          <app-icon name="shield-alert" class="w-6 h-6 text-purple-400"></app-icon>
          <span>Automated Code Review Agent</span>
        </h1>
        <p class="text-sm text-slate-400 mt-1">
          Perform actionable pull request diff analysis for security vulnerabilities, bugs, performance flaws, and type safety.
        </p>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <form (ngSubmit)="handleRunReview()" class="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4 shadow-sm">
          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
              <app-icon name="code" class="w-4 h-4 text-blue-400"></app-icon>
              <span>Git Diff / PR Code Snippet</span>
            </label>
            <textarea
              rows="12"
              required
              [(ngModel)]="gitDiff"
              name="gitDiff"
              class="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-slate-300 font-mono focus:outline-none focus:border-purple-500"
            ></textarea>
          </div>

          <button
            type="submit"
            [disabled]="isLoading"
            class="w-full bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white font-medium py-3 rounded-lg text-sm transition-all shadow-md shadow-purple-600/20 flex items-center justify-center gap-2"
          >
            <app-icon [name]="isLoading ? 'loader' : 'sparkles'" [class]="'w-4 h-4 ' + (isLoading ? 'animate-spin' : '')"></app-icon>
            <span>{{ isLoading ? 'Performing AI Review...' : 'Run Code Review' }}</span>
          </button>
        </form>

        <div class="space-y-4">
          <div *ngIf="review" class="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4 shadow-sm">
            <div class="border-b border-slate-800 pb-3">
              <h3 class="font-bold text-slate-100 text-base">Review Summary</h3>
              <p class="text-xs text-slate-300 mt-1">{{ review.summary }}</p>
            </div>

            <div class="space-y-3">
              <div *ngFor="let f of review.findings" class="bg-slate-950 border border-slate-800 p-4 rounded-xl space-y-2">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <span
                      [ngClass]="getSeverityBadge(f.severity)"
                      class="text-xs px-2.5 py-0.5 rounded border font-semibold"
                    >
                      {{ f.severity }}
                    </span>
                    <span class="text-xs text-slate-400 font-medium">{{ f.category }}</span>
                  </div>
                  <button
                    (click)="jumpToCitation(f)"
                    class="text-xs text-blue-400 font-mono hover:underline"
                  >
                    {{ f.file }}:{{ f.line }}
                  </button>
                </div>

                <h4 class="font-medium text-slate-200 text-xs">{{ f.description }}</h4>
                <p class="text-xs text-slate-400 leading-relaxed">
                  <span class="text-slate-300 font-semibold">Recommendation:</span> {{ f.recommendation }}
                </p>
              </div>
            </div>
          </div>

          <div
            *ngIf="!review"
            class="h-full bg-slate-900/40 border border-dashed border-slate-800 rounded-2xl flex flex-col items-center justify-center text-slate-500 p-8 text-center text-xs"
          >
            <app-icon name="alert-circle" class="w-8 h-8 text-slate-600 mb-2"></app-icon>
            <p>Paste git diff output to receive categorical severity findings and line recommendations.</p>
          </div>
        </div>
      </div>
    </div>
  `
})
export class CodeReviewComponent {
  private repoService = inject(RepositoryService);
  private api = inject(ApiService);

  gitDiff = `--- a/backend/routes/auth_routes.py
+++ b/backend/routes/auth_routes.py
@@ -22,6 +22,8 @@ async def update_user_profile(user_id: str, payload: UserProfileUpdate):
     user = USERS_DB[user_id]
     if payload.name:
         user["name"] = payload.name
     return user`;
  review: CodeReviewResponse | null = null;
  isLoading = false;

  handleRunReview(): void {
    const repo = this.repoService.activeRepository;
    if (!repo) return;
    this.isLoading = true;

    this.api.reviewCode(repo.id, { git_diff: this.gitDiff }).subscribe({
      next: (res) => {
        this.review = res;
        this.isLoading = false;
      },
      error: (err) => {
        console.error(err);
        this.isLoading = false;
      }
    });
  }

  jumpToCitation(f: ReviewFinding): void {
    this.repoService.jumpToCitation({
      file: f.file,
      start_line: f.line,
      end_line: f.line + 5,
      relevance: f.confidence
    });
  }

  getSeverityBadge(severity: string): string {
    switch (severity.toUpperCase()) {
      case 'HIGH':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/30';
      case 'MEDIUM':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/30';
      default:
        return 'bg-blue-500/20 text-blue-300 border-blue-500/30';
    }
  }
}
