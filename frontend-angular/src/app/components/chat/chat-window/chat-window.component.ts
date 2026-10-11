import { Component, Input, Output, EventEmitter, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RepositoryService } from '../../../services/repository.service';
import { StructuredAIResponse, AgentRunResult, Citation } from '../../../models/types';
import { IconComponent } from '../../common/icon/icon.component';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  responseObj?: StructuredAIResponse | AgentRunResult;
}

@Component({
  selector: 'app-chat-window',
  standalone: true,
  imports: [CommonModule, FormsModule, IconComponent],
  template: `
    <div class="flex flex-col h-full bg-[#0b0f17] border-l border-slate-800">
      <!-- Header -->
      <div class="h-14 border-b border-slate-800 px-4 flex items-center justify-between shrink-0">
        <div class="flex items-center gap-2">
          <app-icon name="bot" class="w-5 h-5 text-blue-400"></app-icon>
          <h2 class="font-semibold text-sm text-slate-200">Repository Copilot Chat</h2>
        </div>

        <div class="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-lg p-1 text-xs">
          <button
            type="button"
            (click)="useAgent = false"
            [ngClass]="!useAgent ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-200'"
            class="px-2.5 py-1 rounded-md font-medium transition-all"
          >
            RAG Fast
          </button>
          <button
            type="button"
            (click)="useAgent = true"
            [ngClass]="useAgent ? 'bg-purple-600 text-white' : 'text-slate-400 hover:text-slate-200'"
            class="px-2.5 py-1 rounded-md font-medium transition-all flex items-center gap-1"
          >
            <app-icon name="cpu" class="w-3.5 h-3.5"></app-icon> Agent Mode
          </button>
        </div>
      </div>

      <!-- Messages -->
      <div class="flex-1 overflow-y-auto p-4 space-y-6">
        <div *ngIf="messages.length === 0" class="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto">
          <div class="w-12 h-12 rounded-2xl bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-400 mb-3">
            <app-icon name="sparkles" class="w-6 h-6"></app-icon>
          </div>
          <h3 class="font-semibold text-slate-200 text-base mb-1">Ask CodePilot AI about your repository</h3>
          <p class="text-xs text-slate-400 mb-4">Select a question or type your prompt to retrieve indexed AST context and citations.</p>

          <div class="w-full space-y-2 text-left">
            <button
              *ngFor="let q of sampleQuestions"
              (click)="onSendSample(q)"
              class="w-full text-xs text-slate-300 bg-slate-900/60 hover:bg-slate-800 border border-slate-800 p-2.5 rounded-lg transition-all text-left flex items-center justify-between"
            >
              <span>"{{ q }}"</span>
              <app-icon name="chevron-down" class="w-3.5 h-3.5 text-slate-500 -rotate-90"></app-icon>
            </button>
          </div>
        </div>

        <div
          *ngFor="let m of messages"
          [ngClass]="m.role === 'user' ? 'justify-end' : 'justify-start'"
          class="flex gap-3"
        >
          <!-- Assistant Avatar -->
          <div
            *ngIf="m.role === 'assistant'"
            class="w-8 h-8 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 shrink-0"
          >
            <app-icon name="bot" class="w-4 h-4"></app-icon>
          </div>

          <div
            [ngClass]="m.role === 'user' ? 'bg-blue-600 text-white rounded-2xl rounded-tr-none px-4 py-3 text-sm' : ''"
            class="max-w-[85%] space-y-3"
          >
            <div
              *ngIf="m.role === 'assistant'"
              class="bg-slate-900/80 border border-slate-800 rounded-2xl rounded-tl-none p-4 text-sm text-slate-200 shadow-sm space-y-3"
            >
              <!-- Copy button & content -->
              <div class="flex justify-between items-start gap-3">
                <div class="whitespace-pre-wrap font-sans leading-relaxed">{{ m.content }}</div>
                <button
                  (click)="handleCopy(m.content, m.id)"
                  class="text-slate-400 hover:text-white p-1 shrink-0"
                  title="Copy answer"
                >
                  <app-icon [name]="copiedId === m.id ? 'check' : 'copy'" [class]="'w-4 h-4 ' + (copiedId === m.id ? 'text-emerald-400' : '')"></app-icon>
                </button>
              </div>

              <!-- Citations -->
              <div *ngIf="m.responseObj?.citations && m.responseObj!.citations.length > 0" class="pt-2 border-t border-slate-800/80">
                <div class="text-xs font-semibold text-slate-400 mb-2 flex items-center gap-1.5">
                  <app-icon name="file-code" class="w-3.5 h-3.5 text-blue-400"></app-icon>
                  <span>Referenced Files ({{ m.responseObj!.citations.length }})</span>
                </div>
                <div class="flex flex-wrap gap-2">
                  <button
                    *ngFor="let c of m.responseObj!.citations"
                    (click)="onJumpToCitation(c)"
                    class="text-xs bg-slate-800 hover:bg-slate-700 text-blue-300 border border-slate-700 px-2.5 py-1 rounded-md font-mono flex items-center gap-1.5 transition-all"
                  >
                    <span>{{ c.file }}:{{ c.start_line }}-{{ c.end_line }}</span>
                    <span class="text-[10px] text-emerald-400 bg-emerald-500/10 px-1 rounded">
                      {{ Math.round(c.relevance * 100) }}%
                    </span>
                  </button>
                </div>
              </div>

              <!-- Reasoning Accordion -->
              <div *ngIf="m.responseObj?.reasoning_summary" class="pt-2 border-t border-slate-800/80">
                <button
                  (click)="toggleReasoning(m.id)"
                  class="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1.5 font-medium"
                >
                  <app-icon [name]="showReasoning[m.id] ? 'chevron-up' : 'chevron-down'" class="w-3.5 h-3.5"></app-icon>
                  <span>Analysis Summary</span>
                </button>
                <div
                  *ngIf="showReasoning[m.id]"
                  class="mt-2 text-xs text-slate-400 bg-slate-950 p-3 rounded-lg border border-slate-800 font-mono"
                >
                  {{ m.responseObj!.reasoning_summary }}
                </div>
              </div>
            </div>

            <div *ngIf="m.role === 'user'">{{ m.content }}</div>
          </div>

          <!-- User Avatar -->
          <div
            *ngIf="m.role === 'user'"
            class="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 shrink-0"
          >
            <app-icon name="user" class="w-4 h-4"></app-icon>
          </div>
        </div>

        <!-- Loading spinner -->
        <div *ngIf="isLoading" class="flex items-center gap-2 text-xs text-slate-400 bg-slate-900 border border-slate-800 p-3 rounded-xl w-fit">
          <app-icon name="sparkles" class="w-4 h-4 text-blue-400 animate-spin"></app-icon>
          <span>CodePilot AI is analyzing indexed repository context...</span>
        </div>
      </div>

      <!-- Input Form -->
      <form (ngSubmit)="handleSubmit()" class="p-4 border-t border-slate-800 bg-[#0f172a]/60 shrink-0">
        <div class="flex gap-2">
          <input
            type="text"
            [(ngModel)]="input"
            name="chatInput"
            [placeholder]="useAgent ? 'Ask agent to analyze, find callers, review...' : 'Ask questions about auth, order flow, APIs...'"
            class="flex-1 bg-slate-900 border border-slate-800 rounded-lg px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
          <button
            type="submit"
            [disabled]="!input.trim() || isLoading"
            class="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white px-4 py-2.5 rounded-lg transition-all shadow-md shadow-blue-600/20 flex items-center gap-1.5 font-medium text-sm"
          >
            <app-icon name="send" class="w-4 h-4"></app-icon>
            <span>Send</span>
          </button>
        </div>
      </form>
    </div>
  `
})
export class ChatWindowComponent {
  private repoService = inject(RepositoryService);

  @Input() messages: ChatMessage[] = [];
  @Input() isLoading: boolean = false;
  @Output() sendMessage = new EventEmitter<{ message: string; useAgent: boolean }>();

  input = '';
  useAgent = false;
  showReasoning: Record<string, boolean> = {};
  copiedId: string | null = null;
  Math = Math;

  sampleQuestions = [
    'Where is authentication implemented?',
    'Find potential security issues in auth routes.',
    'How does order creation and idempotency work?',
    'Which module handles payment processing?'
  ];

  handleSubmit(): void {
    if (!this.input.trim() || this.isLoading) return;
    this.sendMessage.emit({ message: this.input, useAgent: this.useAgent });
    this.input = '';
  }

  onSendSample(q: string): void {
    if (this.isLoading) return;
    this.sendMessage.emit({ message: q, useAgent: this.useAgent });
  }

  handleCopy(text: string, id: string): void {
    navigator.clipboard.writeText(text);
    this.copiedId = id;
    setTimeout(() => {
      this.copiedId = null;
    }, 2000);
  }

  toggleReasoning(id: string): void {
    this.showReasoning[id] = !this.showReasoning[id];
  }

  onJumpToCitation(citation: Citation): void {
    this.repoService.jumpToCitation(citation);
  }
}
