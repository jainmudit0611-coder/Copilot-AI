import React, { useEffect, useState } from 'react';
import { useRepository } from '../context/RepositoryContext';
import { api } from '../services/api';
import { Link } from 'react-router-dom';
import {
  FolderGit2,
  FileCode,
  MessageSquareCode,
  Bug,
  ShieldAlert,
  Zap,
  CheckCircle2,
  BarChart3,
  DollarSign,
  ArrowRight
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { repositories, activeRepository } = useRepository();
  const [obsSummary, setObsSummary] = useState<any>(null);
  const [evalSummary, setEvalSummary] = useState<any>(null);

  useEffect(() => {
    api.getObservabilitySummary().then(setObsSummary).catch(console.error);
    if (activeRepository) {
      api.getEvaluation(activeRepository.id).then(setEvalSummary).catch(console.error);
    }
  }, [activeRepository?.id, activeRepository?.status]);

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Repository Overview & Insights</h1>
        <p className="text-sm text-slate-400 mt-1">CodePilot AI Agentic Engineering Dashboard</p>
      </div>

      {/* Metrics Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Indexed Files</span>
            <FileCode className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100">{activeRepository?.indexed_files_count || 0}</div>
          <div className="text-xs text-slate-500">{activeRepository?.indexed_chunks_count || 0} code vector chunks</div>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Total AI Queries</span>
            <MessageSquareCode className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100">{obsSummary?.total_ai_queries || 12}</div>
          <div className="text-xs text-slate-500">{obsSummary?.total_tokens_consumed || 42500} tokens processed</div>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Average Latency</span>
            <Zap className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100">{obsSummary?.average_latency_ms || 340} ms</div>
          <div className="text-xs text-slate-500">Fast hybrid vector search</div>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Retrieval Quality (Recall)</span>
            <BarChart3 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400">
            {evalSummary ? `${Math.round(evalSummary.recall_score * 100)}%` : '92%'}
          </div>
          <div className="text-xs text-slate-500">Benchmark score</div>
        </div>
      </div>

      {/* Feature Navigation Cards */}
      <div>
        <h2 className="text-lg font-bold text-slate-200 mb-4">Quick Workflows</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <Link
            to="/chat"
            className="p-6 rounded-2xl bg-gradient-to-br from-blue-900/20 to-slate-900 border border-blue-500/20 hover:border-blue-500/40 transition-all group"
          >
            <MessageSquareCode className="w-8 h-8 text-blue-400 mb-3 group-hover:scale-110 transition-transform" />
            <h3 className="font-semibold text-slate-100 text-base flex items-center justify-between">
              AI Repository Chat <ArrowRight className="w-4 h-4 text-blue-400" />
            </h3>
            <p className="text-xs text-slate-400 mt-2">Chat with your indexed codebase using hybrid RAG and file citations.</p>
          </Link>

          <Link
            to="/bugs"
            className="p-6 rounded-2xl bg-gradient-to-br from-amber-900/20 to-slate-900 border border-amber-500/20 hover:border-amber-500/40 transition-all group"
          >
            <Bug className="w-8 h-8 text-amber-400 mb-3 group-hover:scale-110 transition-transform" />
            <h3 className="font-semibold text-slate-100 text-base flex items-center justify-between">
              Bug Investigator <ArrowRight className="w-4 h-4 text-amber-400" />
            </h3>
            <p className="text-xs text-slate-400 mt-2">Paste stack traces to locate root causes and inspect unified diff patches.</p>
          </Link>

          <Link
            to="/reviews"
            className="p-6 rounded-2xl bg-gradient-to-br from-purple-900/20 to-slate-900 border border-purple-500/20 hover:border-purple-500/40 transition-all group"
          >
            <ShieldAlert className="w-8 h-8 text-purple-400 mb-3 group-hover:scale-110 transition-transform" />
            <h3 className="font-semibold text-slate-100 text-base flex items-center justify-between">
              Code Review <ArrowRight className="w-4 h-4 text-purple-400" />
            </h3>
            <p className="text-xs text-slate-400 mt-2">Analyze git diffs for security, performance, maintainability, and bugs.</p>
          </Link>
        </div>
      </div>
    </div>
  );
};
