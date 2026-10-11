import { Component, Input, OnChanges, SimpleChanges, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IconComponent } from '../../common/icon/icon.component';

@Component({
  selector: 'app-code-viewer',
  standalone: true,
  imports: [CommonModule, IconComponent],
  template: `
    <div class="h-full w-full flex flex-col bg-[#0b0f17]">
      <div class="h-10 bg-[#0f172a] border-b border-slate-800 px-4 flex items-center justify-between text-xs text-slate-400 shrink-0">
        <span class="font-mono text-slate-200">{{ filePath }}</span>
        <div class="flex items-center gap-2">
          <span
            *ngIf="highlightRange"
            class="bg-blue-600/20 text-blue-400 px-2 py-0.5 rounded border border-blue-500/30"
          >
            Highlighted: Lines {{ highlightRange.startLine }}-{{ highlightRange.endLine }}
          </span>
          <button
            (click)="copyCode()"
            class="text-slate-400 hover:text-white flex items-center gap-1 transition-colors px-2 py-0.5 rounded bg-slate-800/80 hover:bg-slate-800"
          >
            <app-icon [name]="copied ? 'check' : 'copy'" class="w-3.5 h-3.5 text-slate-300"></app-icon>
            <span class="text-[11px]">{{ copied ? 'Copied' : 'Copy' }}</span>
          </button>
        </div>
      </div>

      <div #scrollContainer class="flex-1 overflow-auto font-mono text-[13px] leading-5 p-4 bg-[#0b0f17]">
        <div class="flex min-w-full">
          <!-- Line Numbers -->
          <div class="select-none pr-4 text-right text-slate-600 shrink-0 border-r border-slate-800/60 font-mono">
            <div
              *ngFor="let line of lines; let i = index"
              [id]="'line-num-' + (i + 1)"
              [class.text-blue-400]="isLineHighlighted(i + 1)"
              [class.font-bold]="isLineHighlighted(i + 1)"
              class="h-5 text-xs"
            >
              {{ i + 1 }}
            </div>
          </div>

          <!-- Code Lines -->
          <div class="pl-4 flex-1 overflow-x-auto whitespace-pre font-mono">
            <div
              *ngFor="let line of lines; let i = index"
              [id]="'line-code-' + (i + 1)"
              [class.bg-blue-600-15]="isLineHighlighted(i + 1)"
              [class.border-l-2]="isLineHighlighted(i + 1)"
              [class.border-blue-500]="isLineHighlighted(i + 1)"
              [class.pl-2]="isLineHighlighted(i + 1)"
              class="h-5 text-slate-200 transition-colors"
              [ngClass]="{
                'bg-blue-600/15 text-blue-200': isLineHighlighted(i + 1)
              }"
            >{{ line || ' ' }}</div>
          </div>
        </div>
      </div>
    </div>
  `
})
export class CodeViewerComponent implements OnChanges {
  @Input() content: string = '';
  @Input() language: string = 'typescript';
  @Input() filePath: string = '';
  @Input() highlightRange?: { startLine: number; endLine: number } | null = null;

  @ViewChild('scrollContainer') scrollContainer?: ElementRef<HTMLDivElement>;

  lines: string[] = [];
  copied = false;

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['content']) {
      this.lines = (this.content || '').split('\n');
    }

    if (changes['highlightRange'] && this.highlightRange?.startLine) {
      setTimeout(() => this.scrollToHighlight(), 100);
    }
  }

  isLineHighlighted(lineNumber: number): boolean {
    if (!this.highlightRange) return false;
    const start = this.highlightRange.startLine;
    const end = this.highlightRange.endLine || start;
    return lineNumber >= start && lineNumber <= end;
  }

  scrollToHighlight(): void {
    if (!this.highlightRange || !this.scrollContainer) return;
    const lineElement = document.getElementById(`line-code-${this.highlightRange.startLine}`);
    if (lineElement) {
      lineElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }

  copyCode(): void {
    navigator.clipboard.writeText(this.content || '');
    this.copied = true;
    setTimeout(() => {
      this.copied = false;
    }, 2000);
  }
}
