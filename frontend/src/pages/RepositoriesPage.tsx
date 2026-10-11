import React, { useState } from 'react';
import { useRepository } from '../context/RepositoryContext';
import { api } from '../services/api';
import { FolderGit2, Plus, Github, Upload, CheckCircle2, RefreshCw, AlertCircle, Loader2 } from 'lucide-react';

export const RepositoriesPage: React.FC = () => {
  const { repositories, refreshRepositories } = useRepository();
  const [showModal, setShowModal] = useState(false);
  const [name, setName] = useState('');
  const [githubUrl, setGithubUrl] = useState('');
  const [description, setDescription] = useState('');

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const repo = await api.createRepository({
        workspace_id: 'default-ws',
        name,
        github_url: githubUrl,
        description
      });
      await api.triggerIndexing(repo.id);
      await refreshRepositories();
      setShowModal(false);
      setName('');
      setGithubUrl('');
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Repositories</h1>
          <p className="text-sm text-slate-400 mt-1">Connect GitHub repositories or upload project archives for indexing.</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg font-medium text-sm transition-all shadow-md shadow-blue-600/20"
        >
          <Plus className="w-4 h-4" /> Add Repository
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {repositories.map((repo) => (
          <div key={repo.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-sm flex flex-col justify-between">
            <div>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <FolderGit2 className="w-5 h-5 text-blue-400" />
                  <h3 className="font-semibold text-slate-100 text-base">{repo.name}</h3>
                </div>
                {repo.status === 'COMPLETED' ? (
                  <span className="text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded-full font-medium">
                    Indexed
                  </span>
                ) : (
                  <span className="text-xs bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2 py-0.5 rounded-full font-medium flex items-center gap-1">
                    <Loader2 className="w-3 h-3 animate-spin" /> {repo.status}
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-2 line-clamp-2">{repo.description || 'No description'}</p>
            </div>

            <div className="pt-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400 font-mono">
              <span>{repo.indexed_files_count} Files</span>
              <span>{repo.indexed_chunks_count} Chunks</span>
              <button
                onClick={async () => {
                  await api.triggerIndexing(repo.id);
                  await refreshRepositories();
                }}
                className="text-blue-400 hover:underline font-sans"
              >
                Re-index
              </button>
            </div>
          </div>
        ))}
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <form onSubmit={handleCreate} className="bg-slate-900 border border-slate-800 p-6 rounded-2xl max-w-md w-full space-y-4">
            <h3 className="text-lg font-bold text-slate-100">Connect Repository</h3>
            <input
              type="text"
              required
              placeholder="Repository Name (e.g. My Next.js Backend)"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 placeholder-slate-500"
            />
            <input
              type="url"
              placeholder="GitHub Repository URL (e.g. https://github.com/org/repo)"
              value={githubUrl}
              onChange={(e) => setGithubUrl(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 placeholder-slate-500"
            />
            <textarea
              placeholder="Description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 placeholder-slate-500 h-24"
            />
            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowModal(false)}
                className="px-4 py-2 bg-slate-800 text-slate-300 rounded-lg text-sm"
              >
                Cancel
              </button>
              <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium">
                Connect & Index
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
