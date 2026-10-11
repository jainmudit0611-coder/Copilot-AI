import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RepositoryService } from '../../../services/repository.service';
import { WorkspaceService } from '../../../services/workspace.service';
import { ApiService } from '../../../services/api.service';
import { IconComponent } from '../icon/icon.component';
import { Repository } from '../../../models/types';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule, FormsModule, IconComponent],
  template: `
    <header class="h-16 border-b border-slate-800 bg-[#0b0f17]/90 backdrop-blur px-6 flex items-center justify-between sticky top-0 z-20">
      <div class="flex items-center gap-4">
        <div class="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-sm text-slate-300">
          <app-icon name="folder-git" class="w-4 h-4 text-blue-400"></app-icon>
          <select
            [ngModel]="activeRepository?.id"
            (ngModelChange)="onSelectRepo($event)"
            class="bg-transparent border-none outline-none text-slate-200 font-medium cursor-pointer"
          >
            <option *ngFor="let repo of repositories" [value]="repo.id" class="bg-slate-900 text-slate-200">
              {{ repo.name }} ({{ repo.default_branch }})
            </option>
          </select>
        </div>

        <div *ngIf="activeRepository" class="flex items-center gap-2 text-xs">
          <span
            *ngIf="activeRepository.status === 'COMPLETED'"
            class="flex items-center gap-1.5 text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20 font-medium"
          >
            <app-icon name="check-circle" class="w-3.5 h-3.5"></app-icon>
            Indexed ({{ activeRepository.indexed_files_count }} files)
          </span>

          <span
            *ngIf="activeRepository.status === 'FAILED'"
            class="flex items-center gap-1.5 text-rose-400 bg-rose-500/10 px-2.5 py-1 rounded-full border border-rose-500/20 font-medium"
          >
            <app-icon name="alert-circle" class="w-3.5 h-3.5"></app-icon>
            Indexing Failed
          </span>

          <span
            *ngIf="activeRepository.status !== 'COMPLETED' && activeRepository.status !== 'FAILED'"
            class="flex items-center gap-1.5 text-amber-400 bg-amber-500/10 px-2.5 py-1 rounded-full border border-amber-500/20 font-medium"
          >
            <app-icon name="loader" class="w-3.5 h-3.5 animate-spin"></app-icon>
            {{ activeRepository.status }}
          </span>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <button
          (click)="handleTriggerIndexing()"
          [disabled]="isBusy || !activeRepository"
          class="flex items-center gap-2 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-all shadow-md shadow-blue-600/20"
        >
          <app-icon name="refresh" [class]="'w-4 h-4 ' + (isBusy ? 'animate-spin' : '')"></app-icon>
          <span>{{ isBusy ? (isStatusIndexing ? activeRepository!.status + '...' : 'Starting Index...') : 'Re-index Repository' }}</span>
        </button>

        <div class="h-8 w-px bg-slate-800"></div>

        <div class="flex items-center gap-2 text-sm text-slate-400">
          <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>{{ activeWorkspace?.name || 'Main Workspace' }}</span>
        </div>
      </div>
    </header>
  `
})
export class HeaderComponent {
  private repoService = inject(RepositoryService);
  private wsService = inject(WorkspaceService);
  private api = inject(ApiService);

  isTriggering = false;

  get repositories(): Repository[] {
    return this.repoService.repositories;
  }

  get activeRepository(): Repository | null {
    return this.repoService.activeRepository;
  }

  get activeWorkspace() {
    return this.wsService.activeWorkspace;
  }

  get isStatusIndexing(): boolean {
    const status = this.activeRepository?.status;
    return !!status && ['DOWNLOADING', 'PARSING', 'CHUNKING', 'EMBEDDING', 'INDEXING'].includes(status);
  }

  get isBusy(): boolean {
    return this.isTriggering || this.isStatusIndexing;
  }

  onSelectRepo(repoId: string): void {
    const repo = this.repositories.find((r) => r.id === repoId);
    if (repo) {
      this.repoService.setActiveRepository(repo);
    }
  }

  handleTriggerIndexing(): void {
    if (!this.activeRepository || this.isBusy) return;
    this.isTriggering = true;
    this.api.triggerIndexing(this.activeRepository.id).subscribe({
      next: () => {
        this.repoService.refreshRepositories().subscribe({
          complete: () => {
            this.isTriggering = false;
          }
        });
      },
      error: (err) => {
        console.error('Trigger indexing failed:', err);
        this.isTriggering = false;
      }
    });
  }
}
