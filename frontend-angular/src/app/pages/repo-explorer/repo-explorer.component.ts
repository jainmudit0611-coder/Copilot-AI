import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RepositoryService } from '../../services/repository.service';
import { ApiService } from '../../services/api.service';
import { FileNode, FileDetail, ActiveFileSelection } from '../../models/types';
import { FileTreeComponent } from '../../components/repository/file-tree/file-tree.component';
import { CodeViewerComponent } from '../../components/repository/code-viewer/code-viewer.component';
import { IconComponent } from '../../components/common/icon/icon.component';

@Component({
  selector: 'app-repo-explorer',
  standalone: true,
  imports: [CommonModule, FileTreeComponent, CodeViewerComponent, IconComponent],
  template: `
    <div class="flex h-[calc(100vh-4rem)] overflow-hidden">
      <!-- Left: File Tree -->
      <app-file-tree
        [files]="files"
        [selectedFile]="selectedFile"
        (selectFile)="onSelectFile($event)"
      ></app-file-tree>

      <!-- Center: Code Viewer -->
      <div class="flex-1 h-full min-w-0">
        <app-code-viewer
          *ngIf="fileDetail"
          [content]="fileDetail.content"
          [language]="fileDetail.language"
          [filePath]="fileDetail.path"
          [highlightRange]="getHighlightRange()"
        ></app-code-viewer>

        <div
          *ngIf="!fileDetail"
          class="h-full flex items-center justify-center text-slate-500 text-sm"
        >
          Select a file from the repository tree to inspect.
        </div>
      </div>

      <!-- Right: Metadata Panel -->
      <div class="w-72 bg-[#0f172a] border-l border-slate-800 p-4 space-y-4 overflow-y-auto shrink-0">
        <div class="flex items-center gap-2 text-xs font-semibold text-slate-300 uppercase tracking-wider">
          <app-icon name="info" class="w-4 h-4 text-blue-400"></app-icon>
          <span>File Context</span>
        </div>

        <div *ngIf="fileDetail" class="space-y-3 text-xs">
          <div class="bg-slate-900 border border-slate-800 p-3 rounded-lg space-y-1 font-mono text-slate-300">
            <div>Path: {{ fileDetail.path }}</div>
            <div>Language: {{ fileDetail.language }}</div>
            <div>Size: {{ Math.round(fileDetail.size_bytes / 1024) }} KB</div>
          </div>

          <div class="bg-slate-900 border border-slate-800 p-3 rounded-lg space-y-2">
            <div class="font-semibold text-slate-300 flex items-center gap-1.5">
              <app-icon name="layers" class="w-3.5 h-3.5 text-purple-400"></app-icon>
              <span>RAG Chunk Info</span>
            </div>
            <p class="text-slate-400 text-[11px]">Indexed with symbol boundaries and AST signatures in pgvector.</p>
          </div>
        </div>
      </div>
    </div>
  `
})
export class RepoExplorerComponent implements OnInit {
  private repoService = inject(RepositoryService);
  private api = inject(ApiService);

  files: FileNode[] = [];
  selectedFile: string | null = null;
  fileDetail: FileDetail | null = null;
  Math = Math;

  get activeRepository() {
    return this.repoService.activeRepository;
  }

  get activeSelection(): ActiveFileSelection | null {
    return this.repoService.activeSelection;
  }

  ngOnInit(): void {
    this.repoService.activeRepository$.subscribe((repo) => {
      if (repo) {
        this.api.getFiles(repo.id).subscribe({
          next: (data) => {
            this.files = data;
            if (data.length > 0 && !this.selectedFile) {
              this.onSelectFile(data[0].path);
            }
          },
          error: (err) => console.error(err)
        });
      }
    });

    this.repoService.activeSelection$.subscribe((sel) => {
      if (sel?.filePath) {
        this.onSelectFile(sel.filePath);
      }
    });
  }

  onSelectFile(path: string): void {
    this.selectedFile = path;
    const repo = this.activeRepository;
    if (repo) {
      this.api.getFileDetail(repo.id, path).subscribe({
        next: (detail) => (this.fileDetail = detail),
        error: (err) => console.error(err)
      });
    }
  }

  getHighlightRange() {
    if (this.activeSelection && this.activeSelection.filePath === this.fileDetail?.path) {
      return {
        startLine: this.activeSelection.startLine || 1,
        endLine: this.activeSelection.endLine || 10
      };
    }
    return null;
  }
}
