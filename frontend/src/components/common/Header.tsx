import React, { useState } from 'react';
import { useRepository } from '../../context/RepositoryContext';
import { useWorkspace } from '../../context/WorkspaceContext';
import { api } from '../../services/api';
import { FolderGit2, RefreshCw, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';

export const Header: React.FC = () => {
  const { repositories, activeRepository, setActiveRepository, refreshRepositories } = useRepository();
  const { activeWorkspace } = useWorkspace();
  const [isIndexing, setIsIndexing] = useState(false);

  const isStatusIndexing =
    !!activeRepository &&
    ['DOWNLOADING', 'PARSING', 'CHUNKING', 'EMBEDDING'].includes(activeRepository.status);
  const isBusy = isIndexing || isStatusIndexing;

  const handleTriggerIndexing = async () => {
    if (!activeRepository || isBusy) return;
    setIsIndexing(true);
    try {
      await api.triggerIndexing(activeRepository.id);
      await refreshRepositories();
    } catch (err) {
      console.error(err);
    } finally {
      setIsIndexing(false);
    }
  };

  return (
    <header className="h-16 border-b border-slate-800 bg-[#0b0f17]/90 backdrop-blur px-6 flex items-center justify-between sticky top-0 z-20">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-sm text-slate-300">
          <FolderGit2 className="w-4 h-4 text-blue-400" />
          <select
            value={activeRepository?.id || ''}
            onChange={(e) => {
              const selected = repositories.find((r) => r.id === e.target.value);
              if (selected) setActiveRepository(selected);
            }}
            className="bg-transparent border-none outline-none text-slate-200 font-medium cursor-pointer"
          >
            {repositories.map((repo) => (
              <option key={repo.id} value={repo.id} className="bg-slate-900 text-slate-200">
                {repo.name} ({repo.default_branch})
              </option>
            ))}
          </select>
        </div>

        {activeRepository && (
          <div className="flex items-center gap-2 text-xs">
            {activeRepository.status === 'COMPLETED' ? (
              <span className="flex items-center gap-1.5 text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20 font-medium">
                <CheckCircle2 className="w-3.5 h-3.5" /> Indexed ({activeRepository.indexed_files_count} files)
              </span>
            ) : activeRepository.status === 'FAILED' ? (
              <span className="flex items-center gap-1.5 text-rose-400 bg-rose-500/10 px-2.5 py-1 rounded-full border border-rose-500/20 font-medium">
                <AlertCircle className="w-3.5 h-3.5" /> Indexing Failed
              </span>
            ) : (
              <span className="flex items-center gap-1.5 text-amber-400 bg-amber-500/10 px-2.5 py-1 rounded-full border border-amber-500/20 font-medium">
                <Loader2 className="w-3.5 h-3.5 animate-spin" /> {activeRepository.status}
              </span>
            )}
          </div>
        )}
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={handleTriggerIndexing}
          disabled={isBusy || !activeRepository}
          className="flex items-center gap-2 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-all shadow-md shadow-blue-600/20"
        >
          <RefreshCw className={`w-4 h-4 ${isBusy ? 'animate-spin' : ''}`} />
          <span>{isBusy ? (isStatusIndexing ? `${activeRepository.status}...` : 'Starting Index...') : 'Re-index Repository'}</span>
        </button>

        <div className="h-8 w-px bg-slate-800" />

        <div className="flex items-center gap-2 text-sm text-slate-400">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>{activeWorkspace?.name || 'Main Workspace'}</span>
        </div>
      </div>
    </header>
  );
};
