import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { IconComponent } from '../icon/icon.component';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterModule, IconComponent],
  template: `
    <aside class="w-64 bg-[#0f172a] border-r border-slate-800 flex flex-col justify-between h-screen sticky top-0 shrink-0">
      <div>
        <div class="h-16 px-6 flex items-center gap-3 border-b border-slate-800">
          <div class="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold shadow-lg shadow-blue-500/20">
            <app-icon name="sparkles" class="w-5 h-5 text-white"></app-icon>
          </div>
          <div>
            <h1 class="font-bold text-white text-base tracking-tight flex items-center gap-1.5">
              CodePilot <span class="text-xs px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 font-mono border border-blue-500/30">AI</span>
            </h1>
            <p class="text-[11px] text-slate-400">Agentic Code Copilot</p>
          </div>
        </div>

        <nav class="p-3 space-y-1">
          <a
            *ngFor="let item of navItems"
            [routerLink]="item.path"
            routerLinkActive="bg-blue-600/15 text-blue-400 border border-blue-500/30 shadow-sm"
            [routerLinkActiveOptions]="{ exact: false }"
            class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
          >
            <app-icon [name]="item.icon" class="w-4 h-4 shrink-0"></app-icon>
            <span>{{ item.label }}</span>
          </a>
        </nav>
      </div>

      <div class="p-4 border-t border-slate-800">
        <div class="p-3 rounded-lg bg-slate-900/60 border border-slate-800/80">
          <div class="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>RAG Engine</span>
            <span class="text-emerald-400 font-medium">pgvector</span>
          </div>
          <div class="flex items-center justify-between text-xs text-slate-400">
            <span>LLM Model</span>
            <span class="text-blue-400 font-medium">gpt-4o</span>
          </div>
        </div>
      </div>
    </aside>
  `
})
export class SidebarComponent {
  navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: 'dashboard' },
    { path: '/repositories', label: 'Repositories', icon: 'folder-git' },
    { path: '/explorer', label: 'Code Explorer', icon: 'code' },
    { path: '/chat', label: 'AI Repository Chat', icon: 'chat' },
    { path: '/bugs', label: 'Bug Analyzer', icon: 'bug' },
    { path: '/reviews', label: 'Code Review', icon: 'shield-alert' },
    { path: '/tests', label: 'Test Generator', icon: 'test-tube' },
    { path: '/docs', label: 'Documentation', icon: 'file-text' },
    { path: '/evaluations', label: 'AI Evaluations', icon: 'chart' },
    { path: '/observability', label: 'Observability & Costs', icon: 'activity' },
    { path: '/settings', label: 'Settings', icon: 'settings' },
  ];
}
