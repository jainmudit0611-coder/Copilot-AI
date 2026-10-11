import React, { useState } from 'react';
import { useRepository } from '../context/RepositoryContext';
import { api } from '../services/api';
import { DocGenerationResponse } from '../types';
import { FileText, Sparkles, Loader2, Copy, Check } from 'lucide-react';

export const DocGeneratorPage: React.FC = () => {
  const { activeRepository } = useRepository();
  const [docType, setDocType] = useState<string>('architecture');
  const [docResult, setDocResult] = useState<DocGenerationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeRepository) return;
    setIsLoading(true);

    try {
      const res = await api.generateDoc(activeRepository.id, { doc_type: docType });
      setDocResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-8 space-y-6 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-slate-100 tracking-tight flex items-center gap-2">
          <FileText className="w-6 h-6 text-blue-400" /> Automated Repository Documentation
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Synthesize architecture overviews, module breakdowns, data flows, and README documentation using indexed AST evidence.
        </p>
      </div>

      <form onSubmit={handleGenerate} className="bg-slate-900 border border-slate-800 p-6 rounded-2xl flex items-center gap-4">
        <select
          value={docType}
          onChange={(e) => setDocType(e.target.value)}
          className="bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 font-medium cursor-pointer"
        >
          <option value="architecture">System Architecture & Data Flow</option>
          <option value="readme">Repository README.md</option>
          <option value="api">API Endpoints Specification</option>
          <option value="module">Module Dependencies & Services</option>
        </select>

        <button
          type="submit"
          disabled={isLoading}
          className="bg-blue-600 hover:bg-blue-500 text-white font-medium px-6 py-3 rounded-lg text-sm transition-all flex items-center gap-2 shadow-md shadow-blue-600/20"
        >
          {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
          <span>{isLoading ? 'Synthesizing Documentation...' : 'Generate Documentation'}</span>
        </button>
      </form>

      {docResult && (
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="font-bold text-slate-100 text-base uppercase">Documentation ({docResult.doc_type})</h3>
            <button
              onClick={() => {
                navigator.clipboard.writeText(docResult.content);
                setCopied(true);
                setTimeout(() => setCopied(false), 2000);
              }}
              className="text-xs text-slate-400 hover:text-white flex items-center gap-1"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copied' : 'Copy Markdown'}</span>
            </button>
          </div>
          <div className="bg-slate-950 p-6 rounded-xl border border-slate-800 font-mono text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">
            {docResult.content}
          </div>
        </div>
      )}
    </div>
  );
};
