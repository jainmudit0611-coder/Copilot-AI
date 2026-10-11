import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FileNode } from '../../../models/types';
import { IconComponent } from '../../common/icon/icon.component';

@Component({
  selector: 'app-file-tree',
  standalone: true,
  imports: [CommonModule, IconComponent],
  template: `
    <div class="w-64 bg-[#0f172a]/80 border-r border-slate-800 h-full overflow-y-auto p-2">
      <div class="text-xs font-semibold text-slate-400 uppercase tracking-wider px-3 py-2">
        Repository Files ({{ files.length }})
      </div>
      <div class="space-y-0.5">
        <button
          *ngFor="let file of files"
          (click)="selectFile.emit(file.path)"
          [class.bg-blue-600-20]="selectedFile === file.path"
          class="w-full text-left px-3 py-2 rounded-md text-xs font-mono flex items-center justify-between transition-all"
          [ngClass]="
            selectedFile === file.path
              ? 'bg-blue-600/20 text-blue-300 font-semibold border border-blue-500/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
          "
        >
          <div class="flex items-center gap-2 truncate">
            <app-icon [name]="getFileIconName(file.language)" [class]="'w-4 h-4 ' + getFileIconColor(file.language)"></app-icon>
            <span class="truncate">{{ file.path }}</span>
          </div>
          <span class="text-[10px] text-slate-500 shrink-0 ml-1">{{ getFileSizeKb(file.size_bytes) }}k</span>
        </button>
      </div>
    </div>
  `
})
export class FileTreeComponent {
  @Input() files: FileNode[] = [];
  @Input() selectedFile: string | null = null;
  @Output() selectFile = new EventEmitter<string>();

  getFileIconName(lang: string): string {
    const l = (lang || '').toLowerCase();
    if (l === 'json' || l === 'yaml') return 'file-json';
    if (l === 'markdown') return 'file-text';
    return 'file-code';
  }

  getFileIconColor(lang: string): string {
    const l = (lang || '').toLowerCase();
    if (l === 'typescript' || l === 'javascript') return 'text-blue-400';
    if (l === 'python') return 'text-amber-400';
    if (l === 'json' || l === 'yaml') return 'text-emerald-400';
    if (l === 'markdown') return 'text-purple-400';
    return 'text-slate-400';
  }

  getFileSizeKb(bytes: number): number {
    return Math.round(bytes / 1024);
  }
}
