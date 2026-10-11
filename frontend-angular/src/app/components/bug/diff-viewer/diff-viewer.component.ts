import { Component, Input, Output, EventEmitter, OnChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IconComponent } from '../../common/icon/icon.component';

@Component({
  selector: 'app-diff-viewer',
  standalone: true,
  imports: [CommonModule, IconComponent],
  template: `
    <div class="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
      <div class="h-10 bg-[#0f172a] border-b border-slate-800 px-4 flex items-center justify-between">
        <div class="flex items-center gap-2 text-xs font-semibold text-slate-300">
          <app-icon name="code" class="w-4 h-4 text-blue-400"></app-icon>
          <span>Proposed Unified Diff Patch</span>
        </div>

        <div *ngIf="status === 'IDLE'" class="flex items-center gap-2">
          <button
            (click)="handleReject()"
            class="flex items-center gap-1 text-xs bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 px-2.5 py-1 rounded font-medium transition-all"
          >
            <app-icon name="x" class="w-3.5 h-3.5"></app-icon> Reject
          </button>
          <button
            (click)="handleApprove()"
            class="flex items-center gap-1 text-xs bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-2.5 py-1 rounded font-medium transition-all"
          >
            <app-icon name="check" class="w-3.5 h-3.5"></app-icon> Approve Patch
          </button>
        </div>

        <span
          *ngIf="status !== 'IDLE'"
          [ngClass]="status === 'APPROVED' ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' : 'bg-rose-500/20 text-rose-300 border-rose-500/30'"
          class="text-xs px-2.5 py-1 rounded font-medium border"
        >
          {{ status === 'APPROVED' ? 'Patch Approved (Pending User Write Confirmation)' : 'Patch Rejected' }}
        </span>
      </div>

      <div class="p-4 font-mono text-xs overflow-x-auto bg-[#0b0f17] max-h-96">
        <div
          *ngFor="let line of diffLines"
          [ngClass]="getLineClass(line)"
          class="whitespace-pre py-0.5"
        >
          {{ line }}
        </div>
      </div>
    </div>
  `
})
export class DiffViewerComponent implements OnChanges {
  @Input() patch: string = '';
  @Output() approve = new EventEmitter<void>();
  @Output() reject = new EventEmitter<void>();

  status: 'IDLE' | 'APPROVED' | 'REJECTED' = 'IDLE';
  diffLines: string[] = [];

  ngOnChanges(): void {
    this.diffLines = (this.patch || '').split('\n');
    this.status = 'IDLE';
  }

  handleApprove(): void {
    this.status = 'APPROVED';
    this.approve.emit();
  }

  handleReject(): void {
    this.status = 'REJECTED';
    this.reject.emit();
  }

  getLineClass(line: string): string {
    if (line.startsWith('+')) return 'bg-emerald-500/10 text-emerald-400 font-semibold px-2 py-0.5 rounded-sm';
    if (line.startsWith('-')) return 'bg-rose-500/10 text-rose-400 font-semibold px-2 py-0.5 rounded-sm';
    if (line.startsWith('@')) return 'text-blue-400 font-bold';
    return 'text-slate-400 px-2';
  }
}
