import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RepositoryService } from '../../services/repository.service';
import { ApiService } from '../../services/api.service';
import { TestGenerationResponse } from '../../models/types';
import { IconComponent } from '../../components/common/icon/icon.component';
import { CodeViewerComponent } from '../../components/repository/code-viewer/code-viewer.component';

@Component({
  selector: 'app-test-generator',
  standalone: true,
  imports: [CommonModule, FormsModule, IconComponent, CodeViewerComponent],
  template: `
    <div class="p-8 space-y-6 max-w-6xl mx-auto">
      <div>
        <h1 class="text-2xl font-bold text-slate-100 tracking-tight flex items-center gap-2">
          <app-icon name="test-tube" class="w-6 h-6 text-emerald-400"></app-icon>
          <span>Automated Test Suite Generator</span>
        </h1>
        <p class="text-sm text-slate-400 mt-1">
          Generate comprehensive Pytest, Vitest, or Jest unit test suites covering happy path, edge cases, and exception handling.
        </p>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <form (ngSubmit)="handleGenerate()" class="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4 shadow-sm lg:col-span-1">
          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-1">Target File</label>
            <input
              type="text"
              required
              [(ngModel)]="filePath"
              name="filePath"
              class="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 font-mono focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-1">Testing Framework</label>
            <select
              [(ngModel)]="framework"
              name="framework"
              class="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 font-mono cursor-pointer focus:outline-none focus:border-emerald-500"
            >
              <option value="pytest">Pytest (Python)</option>
              <option value="vitest">Vitest (TypeScript/React)</option>
              <option value="jest">Jest (JavaScript)</option>
            </select>
          </div>

          <button
            type="submit"
            [disabled]="isLoading"
            class="w-full bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-medium py-3 rounded-lg text-sm transition-all shadow-md shadow-emerald-600/20 flex items-center justify-center gap-2"
          >
            <app-icon [name]="isLoading ? 'loader' : 'sparkles'" [class]="'w-4 h-4 ' + (isLoading ? 'animate-spin' : '')"></app-icon>
            <span>{{ isLoading ? 'Generating Tests...' : 'Generate Test Suite' }}</span>
          </button>
        </form>

        <div class="lg:col-span-2 h-[450px] bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden flex flex-col shadow-sm">
          <div class="h-10 bg-[#0f172a] border-b border-slate-800 px-4 flex items-center justify-between shrink-0">
            <span class="text-xs font-mono text-slate-300">Generated Tests ({{ framework }})</span>
            <div *ngIf="result" class="flex items-center gap-2">
              <button (click)="handleCopy()" class="text-xs text-slate-400 hover:text-white flex items-center gap-1">
                <app-icon [name]="copied ? 'check' : 'copy'" [class]="'w-3.5 h-3.5 ' + (copied ? 'text-emerald-400' : '')"></app-icon>
                <span>{{ copied ? 'Copied' : 'Copy' }}</span>
              </button>
              <button (click)="handleDownload()" class="text-xs text-blue-400 hover:underline flex items-center gap-1">
                <app-icon name="download" class="w-3.5 h-3.5"></app-icon>
                <span>Download</span>
              </button>
            </div>
          </div>

          <div class="flex-1 overflow-hidden">
            <app-code-viewer
              *ngIf="result"
              [content]="result.test_code"
              [language]="framework === 'pytest' ? 'python' : 'typescript'"
              [filePath]="'tests/test_' + (filePath.split('/').pop() || 'suite')"
            ></app-code-viewer>

            <div
              *ngIf="!result"
              class="h-full flex items-center justify-center text-slate-500 text-xs"
            >
              Select target file and framework to generate test suites.
            </div>
          </div>
        </div>
      </div>
    </div>
  `
})
export class TestGeneratorComponent {
  private repoService = inject(RepositoryService);
  private api = inject(ApiService);

  filePath = 'backend/routes/order_routes.py';
  framework: 'pytest' | 'vitest' | 'jest' = 'pytest';
  result: TestGenerationResponse | null = null;
  isLoading = false;
  copied = false;

  handleGenerate(): void {
    const repo = this.repoService.activeRepository;
    if (!repo) return;
    this.isLoading = true;

    this.api.generateTests(repo.id, {
      file_path: this.filePath,
      framework: this.framework
    }).subscribe({
      next: (res) => {
        this.result = res;
        this.isLoading = false;
      },
      error: (err) => {
        console.error(err);
        this.isLoading = false;
      }
    });
  }

  handleCopy(): void {
    if (this.result) {
      navigator.clipboard.writeText(this.result.test_code);
      this.copied = true;
      setTimeout(() => (this.copied = false), 2000);
    }
  }

  handleDownload(): void {
    if (!this.result) return;
    const blob = new Blob([this.result.test_code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const ext = this.framework === 'pytest' ? '.py' : '.ts';
    a.download = `test_${this.filePath.split('/').pop()?.split('.')[0] || 'suite'}${ext}`;
    a.click();
  }
}
