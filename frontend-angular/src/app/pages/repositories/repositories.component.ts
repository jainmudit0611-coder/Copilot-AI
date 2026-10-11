import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RepositoryService } from '../../services/repository.service';
import { ApiService } from '../../services/api.service';
import { IconComponent } from '../../components/common/icon/icon.component';
import { Repository } from '../../models/types';

@Component({
  selector: 'app-repositories',
  standalone: true,
  imports: [CommonModule, FormsModule, IconComponent],
  template: `
    <div class="p-8 space-y-6 max-w-7xl mx-auto">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-slate-100 tracking-tight">Repositories</h1>
          <p class="text-sm text-slate-400 mt-1">Connect GitHub repositories or upload project archives for indexing.</p>
        </div>
        <button
          (click)="showModal = true"
          class="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg font-medium text-sm transition-all shadow-md shadow-blue-600/20"
        >
          <app-icon name="plus" class="w-4 h-4"></app-icon> Add Repository
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        <div
          *ngFor="let repo of repositories"
          class="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-sm flex flex-col justify-between"
        >
          <div>
            <div class="flex items-start justify-between">
              <div class="flex items-center gap-2">
                <app-icon name="folder-git" class="w-5 h-5 text-blue-400"></app-icon>
                <h3 class="font-semibold text-slate-100 text-base">{{ repo.name }}</h3>
              </div>
              <span
                *ngIf="repo.status === 'COMPLETED'"
                class="text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded-full font-medium"
              >
                Indexed
              </span>
              <span
                *ngIf="repo.status !== 'COMPLETED'"
                class="text-xs bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2 py-0.5 rounded-full font-medium flex items-center gap-1"
              >
                <app-icon name="loader" class="w-3 h-3 animate-spin"></app-icon> {{ repo.status }}
              </span>
            </div>
            <p class="text-xs text-slate-400 mt-2 line-clamp-2">{{ repo.description || 'No description' }}</p>
          </div>

          <div class="pt-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400 font-mono">
            <span>{{ repo.indexed_files_count }} Files</span>
            <span>{{ repo.indexed_chunks_count }} Chunks</span>
            <button
              (click)="reindexRepo(repo.id)"
              class="text-blue-400 hover:underline font-sans"
            >
              Re-index
            </button>
          </div>
        </div>
      </div>

      <!-- Add Repo Modal -->
      <div *ngIf="showModal" class="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
        <form (ngSubmit)="handleCreate()" class="bg-slate-900 border border-slate-800 p-6 rounded-2xl max-w-md w-full space-y-4">
          <h3 class="text-lg font-bold text-slate-100">Connect Repository</h3>
          <input
            type="text"
            required
            placeholder="Repository Name (e.g. My Next.js Backend)"
            [(ngModel)]="name"
            name="name"
            class="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
          <input
            type="url"
            placeholder="GitHub Repository URL (e.g. https://github.com/org/repo)"
            [(ngModel)]="githubUrl"
            name="githubUrl"
            class="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
          <textarea
            placeholder="Description"
            [(ngModel)]="description"
            name="description"
            class="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 placeholder-slate-500 h-24 focus:outline-none focus:border-blue-500"
          ></textarea>
          <div class="flex justify-end gap-2 pt-2">
            <button
              type="button"
              (click)="showModal = false"
              class="px-4 py-2 bg-slate-800 text-slate-300 rounded-lg text-sm hover:bg-slate-700 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              [disabled]="isCreating"
              class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-all"
            >
              {{ isCreating ? 'Connecting...' : 'Connect & Index' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  `
})
export class RepositoriesComponent {
  private repoService = inject(RepositoryService);
  private api = inject(ApiService);

  showModal = false;
  name = '';
  githubUrl = '';
  description = '';
  isCreating = false;

  get repositories(): Repository[] {
    return this.repoService.repositories;
  }

  handleCreate(): void {
    if (!this.name.trim() || this.isCreating) return;
    this.isCreating = true;

    this.api.createRepository({
      workspace_id: 'default-ws',
      name: this.name,
      github_url: this.githubUrl,
      description: this.description
    }).subscribe({
      next: (repo) => {
        this.api.triggerIndexing(repo.id).subscribe({
          next: () => {
            this.repoService.refreshRepositories().subscribe({
              complete: () => {
                this.isCreating = false;
                this.showModal = false;
                this.name = '';
                this.githubUrl = '';
                this.description = '';
              }
            });
          },
          error: () => {
            this.isCreating = false;
          }
        });
      },
      error: (err) => {
        console.error(err);
        this.isCreating = false;
      }
    });
  }

  reindexRepo(repoId: string): void {
    this.api.triggerIndexing(repoId).subscribe({
      next: () => {
        this.repoService.refreshRepositories().subscribe();
      }
    });
  }
}
