import React, { useState } from 'react';
import { useRepository } from '../context/RepositoryContext';
import { api } from '../services/api';
import { CodeReviewResponse, ReviewFinding } from '../types';
import { ShieldAlert, FileDiff, Sparkles, Loader2, AlertCircle, CheckCircle } from 'lucide-react';

export const CodeReviewPage: React.FC = () => {
  const { activeRepository, jumpToCitation } = useRepository();
  const [gitDiff, setGitDiff] = useState(`--- a/backend/routes/auth_routes.py
+++ b/backend/routes/auth_routes.py
@@ -22,6 +22,8 @@ async def update_user_profile(user_id: str, payload: UserProfileUpdate):
     user = USERS_DB[user_id]
     if payload.name:
         user["name"] = payload.name
     return user`);
  const [review, setReview] = useState<CodeReviewResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleRunReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeRepository) return;
    setIsLoading(true);

    try {
      const res = await api.reviewCode(activeRepository.id, { git_diff: gitDiff });
      setReview(res);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity.toUpperCase()) {
      case 'HIGH':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/30';
      case 'MEDIUM':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/30';
      default:
        return 'bg-blue-500/20 text-blue-300 border-blue-500/30';
    }
  };

  return (
    <div className="p-8 space-y-6 max-w-6xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-slate-100 tracking-tight flex items-center gap-2">
          <ShieldAlert className="w-6 h-6 text-purple-400" /> Automated Code Review Agent
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Perform actionable pull request diff analysis for security vulnerabilities, bugs, performance flaws, and type safety.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <form onSubmit={handleRunReview} className="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4 shadow-sm">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
              <FileDiff className="w-4 h-4 text-blue-400" /> Git Diff / PR Code Snippet
            </label>
            <textarea
              rows={12}
              required
              value={gitDiff}
              onChange={(e) => setGitDiff(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-slate-300 font-mono"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white font-medium py-3 rounded-lg text-sm transition-all shadow-md shadow-purple-600/20 flex items-center justify-center gap-2"
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            <span>{isLoading ? 'Performing AI Review...' : 'Run Code Review'}</span>
          </button>
        </form>

        <div className="space-y-4">
          {review ? (
            <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4 shadow-sm">
              <div className="border-b border-slate-800 pb-3">
                <h3 className="font-bold text-slate-100 text-base">Review Summary</h3>
                <p className="text-xs text-slate-300 mt-1">{review.summary}</p>
              </div>

              <div className="space-y-3">
                {review.findings.map((f, idx) => (
                  <div key={idx} className="bg-slate-950 border border-slate-800 p-4 rounded-xl space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className={`text-xs px-2.5 py-0.5 rounded border font-semibold ${getSeverityBadge(f.severity)}`}>
                          {f.severity}
                        </span>
                        <span className="text-xs text-slate-400 font-medium">{f.category}</span>
                      </div>
                      <button
                        onClick={() => jumpToCitation({ file: f.file, start_line: f.line, end_line: f.line + 5, relevance: f.confidence })}
                        className="text-xs text-blue-400 font-mono hover:underline"
                      >
                        {f.file}:{f.line}
                      </button>
                    </div>

                    <h4 className="font-medium text-slate-200 text-xs">{f.description}</h4>
                    <p className="text-xs text-slate-400 leading-relaxed"><span className="text-slate-300 font-semibold">Recommendation:</span> {f.recommendation}</p>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="h-full bg-slate-900/40 border border-dashed border-slate-800 rounded-2xl flex flex-col items-center justify-center text-slate-500 p-8 text-center text-xs">
              <AlertCircle className="w-8 h-8 text-slate-600 mb-2" />
              <p>Paste git diff output to receive categorical severity findings and line recommendations.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
