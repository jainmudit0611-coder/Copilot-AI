import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FolderGit2,
  Code2,
  MessageSquareCode,
  Bug,
  ShieldAlert,
  TestTube2,
  FileText,
  BarChart3,
  Activity,
  Settings,
  Sparkles
} from 'lucide-react';

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/repositories', label: 'Repositories', icon: FolderGit2 },
  { path: '/explorer', label: 'Code Explorer', icon: Code2 },
  { path: '/chat', label: 'AI Repository Chat', icon: MessageSquareCode },
  { path: '/bugs', label: 'Bug Analyzer', icon: Bug },
  { path: '/reviews', label: 'Code Review', icon: ShieldAlert },
  { path: '/tests', label: 'Test Generator', icon: TestTube2 },
  { path: '/docs', label: 'Documentation', icon: FileText },
  { path: '/evaluations', label: 'AI Evaluations', icon: BarChart3 },
  { path: '/observability', label: 'Observability & Costs', icon: Activity },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 bg-[#0f172a] border-r border-slate-800 flex flex-col justify-between h-screen sticky top-0 shrink-0">
      <div>
        <div className="h-16 px-6 flex items-center gap-3 border-b border-slate-800">
          <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold shadow-lg shadow-blue-500/20">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h1 className="font-bold text-white text-base tracking-tight flex items-center gap-1.5">
              CodePilot <span className="text-xs px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 font-mono border border-blue-500/30">AI</span>
            </h1>
            <p className="text-[11px] text-slate-400">Agentic Code Copilot</p>
          </div>
        </div>

        <nav className="p-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                    isActive
                      ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                  }`
                }
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>

      <div className="p-4 border-t border-slate-800">
        <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800/80">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>RAG Engine</span>
            <span className="text-emerald-400 font-medium">pgvector</span>
          </div>
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>LLM Model</span>
            <span className="text-blue-400 font-medium">gpt-4o</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
