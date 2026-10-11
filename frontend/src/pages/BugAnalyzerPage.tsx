import React, { useState } from 'react';
import { useRepository } from '../context/RepositoryContext';
import { api } from '../services/api';
import { BugAnalysisResponse } from '../types';
import { Bug, AlertTriangle, ShieldAlert, Sparkles, Loader2, Code2 } from 'lucide-react';
import { DiffViewer } from '../components/bug/DiffViewer';

export const BugAnalyzerPage: React.FC = () => {
  const { activeRepository } = useRepository();
  const [errorMessage, setErrorMessage] = useState('TypeError: Cannot read properties of undefined (reading \'map\') in create_order idempotency check');
  const [stackTrace, setStackTrace] = useState(`Traceback (most recent call last):
  File "backend/routes/order_routes.py", line 28, in create_order
    if x_idempotency_key in PROCESSED_KEYS:
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "backend/services/payment_gateway.py", line 42, in charge
    response = await res.json()
UnhandledPromiseRejection: Cannot read properties of undefined`);
  const [filePath, setFilePath] = useState('backend/routes/order_routes.py');
  const [analysis, setAnalysis] = useState<BugAnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeRepository) return;
    setIsLoading(true);

    try {
      const res = await api.analyzeBug(activeRepository.id, {
        error_message: errorMessage,
        stack_trace: stackTrace,
        file_path: filePath
      });
      setAnalysis(res);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-8 space-y-6 max-w-6xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-slate-100 tracking-tight flex items-center gap-2">
          <Bug className="w-6 h-6 text-amber-400" /> Automated Bug Investigator
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Paste error logs or stack traces to isolate root causes, locate affected files, and generate proposed diff patches.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Form */}
        <form onSubmit={handleAnalyze} className="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4 shadow-sm">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Error Message</label>
            <input
              type="text"
              required
              value={errorMessage}
              onChange={(e) => setErrorMessage(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 font-mono"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Stack Trace</label>
            <textarea
              rows={6}
              value={stackTrace}
              onChange={(e) => setStackTrace(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-slate-300 font-mono"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Target File (Optional)</label>
            <input
              type="text"
              value={filePath}
              onChange={(e) => setFilePath(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 font-mono"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white font-medium py-3 rounded-lg text-sm transition-all shadow-md shadow-amber-600/20 flex items-center justify-center gap-2"
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            <span>{isLoading ? 'Investigating Repository...' : 'Investigate Bug'}</span>
          </button>
        </form>

        {/* Output Results */}
        <div className="space-y-4">
          {analysis ? (
            <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4 shadow-sm">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="font-bold text-slate-100 text-base">{analysis.error_summary}</h3>
                <span className="text-xs bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2.5 py-1 rounded-full font-medium">
                  Risk: {analysis.risk}
                </span>
              </div>

              <div className="space-y-2">
                <h4 className="text-xs font-semibold text-slate-300">Likely Root Cause</h4>
                <p className="text-xs text-slate-300 bg-slate-950 p-3 rounded-lg border border-slate-800 leading-relaxed">
                  {analysis.likely_root_cause}
                </p>
              </div>

              <div className="space-y-2">
                <h4 className="text-xs font-semibold text-slate-300">Suggested Fix Strategy</h4>
                <p className="text-xs text-slate-300 bg-slate-950 p-3 rounded-lg border border-slate-800 leading-relaxed">
                  {analysis.suggested_fix}
                </p>
              </div>

              {analysis.proposed_patch && (
                <div className="pt-2">
                  <DiffViewer patch={analysis.proposed_patch} />
                </div>
              )}
            </div>
          ) : (
            <div className="h-full bg-slate-900/40 border border-dashed border-slate-800 rounded-2xl flex flex-col items-center justify-center text-slate-500 p-8 text-center text-xs">
              <AlertTriangle className="w-8 h-8 text-slate-600 mb-2" />
              <p>Submit stack trace details to generate an empirical root-cause diagnosis and diff proposal.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
