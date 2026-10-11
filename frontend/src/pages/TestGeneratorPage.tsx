import React, { useState } from 'react';
import { useRepository } from '../context/RepositoryContext';
import { api } from '../services/api';
import { TestGenerationResponse } from '../types';
import { TestTube2, Copy, Check, Sparkles, Loader2, Download } from 'lucide-react';
import Editor from '@monaco-editor/react';

export const TestGeneratorPage: React.FC = () => {
  const { activeRepository } = useRepository();
  const [filePath, setFilePath] = useState('backend/routes/order_routes.py');
  const [framework, setFramework] = useState<'pytest' | 'vitest' | 'jest'>('pytest');
  const [result, setResult] = useState<TestGenerationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeRepository) return;
    setIsLoading(true);

    try {
      const res = await api.generateTests(activeRepository.id, {
        file_path: filePath,
        framework
      });
      setResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = () => {
    if (result) {
      navigator.clipboard.writeText(result.test_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownload = () => {
    if (!result) return;
    const blob = new Blob([result.test_code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `test_${filePath.split('/').pop() || 'suite'}.py`;
    a.click();
  };

  return (
    <div className="p-8 space-y-6 max-w-6xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-slate-100 tracking-tight flex items-center gap-2">
          <TestTube2 className="w-6 h-6 text-emerald-400" /> Automated Test Suite Generator
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Generate comprehensive Pytest, Vitest, or Jest unit test suites covering happy path, edge cases, and exception handling.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <form onSubmit={handleGenerate} className="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4 shadow-sm lg:col-span-1">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Target File</label>
            <input
              type="text"
              required
              value={filePath}
              onChange={(e) => setFilePath(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 font-mono"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Testing Framework</label>
            <select
              value={framework}
              onChange={(e) => setFramework(e.target.value as any)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 font-mono cursor-pointer"
            >
              <option value="pytest">Pytest (Python)</option>
              <option value="vitest">Vitest (TypeScript/React)</option>
              <option value="jest">Jest (JavaScript)</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-medium py-3 rounded-lg text-sm transition-all shadow-md shadow-emerald-600/20 flex items-center justify-center gap-2"
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            <span>{isLoading ? 'Generating Tests...' : 'Generate Test Suite'}</span>
          </button>
        </form>

        <div className="lg:col-span-2 h-96 bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden flex flex-col shadow-sm">
          <div className="h-10 bg-[#0f172a] border-b border-slate-800 px-4 flex items-center justify-between">
            <span className="text-xs font-mono text-slate-300">Generated Tests ({framework})</span>
            {result && (
              <div className="flex items-center gap-2">
                <button onClick={handleCopy} className="text-xs text-slate-400 hover:text-white flex items-center gap-1">
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copied ? 'Copied' : 'Copy'}</span>
                </button>
                <button onClick={handleDownload} className="text-xs text-blue-400 hover:underline flex items-center gap-1">
                  <Download className="w-3.5 h-3.5" /> Download
                </button>
              </div>
            )}
          </div>
          <div className="flex-1">
            {result ? (
              <Editor
                height="100%"
                language={framework === 'pytest' ? 'python' : 'typescript'}
                value={result.test_code}
                theme="vs-dark"
                options={{ readOnly: true, fontSize: 13, minimap: { enabled: false } }}
              />
            ) : (
              <div className="h-full flex items-center justify-center text-slate-500 text-xs">
                Select target file and framework to generate test suites.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
