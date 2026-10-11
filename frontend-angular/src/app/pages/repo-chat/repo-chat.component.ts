import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RepositoryService } from '../../services/repository.service';
import { ApiService } from '../../services/api.service';
import { FileDetail, StructuredAIResponse, AgentRunResult } from '../../models/types';
import { ChatWindowComponent, ChatMessage } from '../../components/chat/chat-window/chat-window.component';
import { CodeViewerComponent } from '../../components/repository/code-viewer/code-viewer.component';

@Component({
  selector: 'app-repo-chat',
  standalone: true,
  imports: [CommonModule, ChatWindowComponent, CodeViewerComponent],
  template: `
    <div class="grid grid-cols-1 lg:grid-cols-2 h-[calc(100vh-4rem)] overflow-hidden">
      <!-- Left: Chat Window -->
      <app-chat-window
        [messages]="messages"
        [isLoading]="isLoading"
        (sendMessage)="handleSendMessage($event.message, $event.useAgent)"
      ></app-chat-window>

      <!-- Right: Code Citation Viewer -->
      <div class="h-full border-l border-slate-800 bg-[#0b0f17]">
        <app-code-viewer
          *ngIf="activeFileDetail"
          [content]="activeFileDetail.content"
          [language]="activeFileDetail.language"
          [filePath]="activeFileDetail.path"
          [highlightRange]="getHighlightRange()"
        ></app-code-viewer>

        <div
          *ngIf="!activeFileDetail"
          class="h-full flex flex-col items-center justify-center text-slate-500 text-xs p-6 text-center"
        >
          <p class="font-medium text-slate-400 mb-1">Code Citation Viewer</p>
          <p class="max-w-xs">Click any citation chip in an AI response to open the exact source file and highlight the line range.</p>
        </div>
      </div>
    </div>
  `
})
export class RepoChatComponent implements OnInit {
  private repoService = inject(RepositoryService);
  private api = inject(ApiService);

  messages: ChatMessage[] = [];
  isLoading = false;
  activeFileDetail: FileDetail | null = null;

  get activeRepository() {
    return this.repoService.activeRepository;
  }

  get activeSelection() {
    return this.repoService.activeSelection;
  }

  ngOnInit(): void {
    this.repoService.activeSelection$.subscribe((sel) => {
      const repo = this.activeRepository;
      if (repo && sel?.filePath) {
        this.api.getFileDetail(repo.id, sel.filePath).subscribe({
          next: (detail) => (this.activeFileDetail = detail),
          error: (err) => console.error(err)
        });
      }
    });
  }

  handleSendMessage(msg: string, useAgent: boolean): void {
    const repo = this.activeRepository;
    if (!repo) return;

    const userMsgId = `msg_${Date.now()}`;
    this.messages = [...this.messages, { id: userMsgId, role: 'user', content: msg }];
    this.isLoading = true;

    if (useAgent) {
      this.api.runAgent(repo.id, msg).subscribe({
        next: (res) => {
          this.messages = [
            ...this.messages,
            { id: `agent_${Date.now()}`, role: 'assistant', content: res.answer, responseObj: res }
          ];
          if (res.citations && res.citations.length > 0) {
            this.loadFileForCitation(res.citations[0].file);
          }
          this.isLoading = false;
        },
        error: (err) => {
          this.messages = [
            ...this.messages,
            { id: `err_${Date.now()}`, role: 'assistant', content: `Error: ${err.message || 'Failed to process AI query'}` }
          ];
          this.isLoading = false;
        }
      });
    } else {
      this.api.chat(repo.id, msg).subscribe({
        next: (res) => {
          this.messages = [
            ...this.messages,
            { id: `chat_${Date.now()}`, role: 'assistant', content: res.answer, responseObj: res }
          ];
          if (res.citations && res.citations.length > 0) {
            this.loadFileForCitation(res.citations[0].file);
          }
          this.isLoading = false;
        },
        error: (err) => {
          this.messages = [
            ...this.messages,
            { id: `err_${Date.now()}`, role: 'assistant', content: `Error: ${err.message || 'Failed to process AI query'}` }
          ];
          this.isLoading = false;
        }
      });
    }
  }

  private loadFileForCitation(filePath: string): void {
    const repo = this.activeRepository;
    if (repo) {
      this.api.getFileDetail(repo.id, filePath).subscribe({
        next: (detail) => (this.activeFileDetail = detail),
        error: (err) => console.error(err)
      });
    }
  }

  getHighlightRange() {
    if (this.activeSelection) {
      return {
        startLine: this.activeSelection.startLine || 1,
        endLine: this.activeSelection.endLine || 20
      };
    }
    return null;
  }
}
