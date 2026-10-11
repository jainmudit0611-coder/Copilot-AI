import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RepositoryService } from '../../services/repository.service';
import { ApiService } from '../../services/api.service';
import { DocGenerationResponse } from '../../models/types';
import { IconComponent } from '../../components/common/icon/icon.component';

@Component({
  selector: 'app-doc-generator',
  standalone: true,
  imports: [CommonModule, FormsModule, IconComponent],
  template: `
    <div class="p-8 space-y-6 max-w-5xl mx-auto">
      <div>
        <h1 class="text-2xl font-bold text-slate-100 tracking-tight flex items-center gap-2">
          <app-icon name="file-text" class="w-6 h-6 text-blue-400"></app-icon>
          <span>Automated Repository Documentation</span>
        </h1>
        <p class="text-sm text-slate-400 mt-1">
          Synthesize architecture overviews, module breakdowns, data flows, and README documentation using indexed AST evidence.
        </p>
      </div>

      <form (ngSubmit)="handleGenerate()" class="bg-slate-900 border border-slate-800 p-6 rounded-2xl flex items-center gap-4">
        <select
          [(ngModel)]="docType"
          name="docType"
          class="bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 font-medium cursor-pointer focus:outline-none focus:border-blue-500"
        >
          <option value="architecture">System Architecture & Data Flow</option>
          <option value="readme">Repository README.md</option>
          <option value="api">API Endpoints Specification</option>
          <option value="module">Module Dependencies & Services</option>
        </select>

        <button
          type="submit"
          [disabled]="isLoading"
          class="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium px-6 py-3 rounded-lg text-sm transition-all flex items-center gap-2 shadow-md shadow-blue-600/20"
        >
          <app-icon [name]="isLoading ? 'loader' : 'sparkles'" [class]="'w-4 h-4 ' + (isLoading ? 'animate-spin' : '')"></app-icon>
          <span>{{ isLoading ? 'Synthesizing Documentation...' : 'Generate Documentation' }}</span>
        </button>
      </form>

      <div *ngIf="docResult" class="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4">
        <div class="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 class="font-bold text-slate-100 text-base uppercase">Documentation ({{ docResult.doc_type }})</h3>
          <button
            (click)="handleCopy()"
            class="text-xs text-slate-400 hover:text-white flex items-center gap-1"
          >
            <app-icon [name]="copied ? 'check' : 'copy'" [class]="'w-3.5 h-3.5 ' + (copied ? 'text-emerald-400' : '')"></app-icon>
            <span>{{ copied ? 'Copied' : 'Copy Markdown' }}</span>
          </button>
        </div>
        <div class="bg-slate-950 p-6 rounded-xl border border-slate-800 font-mono text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">
          {{ docResult.content }}
        </div>
      </div>
    </div>
  `
})
export class DocGeneratorComponent {
  private repoService = inject(RepositoryService);
  private api = inject(ApiService);

  docType = 'architecture';
  docResult: DocGenerationResponse | null = null;
  isLoading = false;
  copied = false;

  handleGenerate(): void {
    const repo = this.repoService.activeRepository;
    if (!repo) return;
    this.isLoading = true;

    this.api.generateDoc(repo.id, { doc_type: this.docType }).subscribe({
      next: (res) => {
        this.docResult = res;
        this.isLoading = false;
      },
      error: (err) => {
        console.error(err);
        this.isLoading = false;
      }
    });
  }

  handleCopy(): void {
    if (!this.docResult) return;
    navigator.clipboard.writeText(this.docResult.content);
    this.copied = true;
    setTimeout(() => (this.copied = false), 2000);
  }
}
