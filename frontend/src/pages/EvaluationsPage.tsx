import React, { useEffect, useState } from 'react';
import { useRepository } from '../context/RepositoryContext';
import { api } from '../services/api';
import { EvaluationSummary } from '../types';
import { BarChart3, RefreshCw, CheckCircle2, ShieldCheck, Zap } from 'lucide-react';

export const EvaluationsPage: React.FC = () => {
  const { activeRepository } = useRepository();
  const [evalData, setEvalData] = useState<EvaluationSummary | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const fetchEval = async () => {
    if (!activeRepository) return;
    setIsLoading(true);
    try {
      const data = await api.getEvaluation(activeRepository.id);
      setEvalData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchEval();
  }, [activeRepository?.id]);

  const handleRunEval = async () => {
    if (!activeRepository) return;
    setIsLoading(true);
    try {
      const data = await api.triggerEvaluation(activeRepository.id);
      setEvalData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-8 space-y-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-emerald-400" /> RAG Retrieval & Evaluation Quality Framework
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Empirical benchmark metrics evaluating context precision, recall, groundedness, and citation accuracy.
          </p>
        </div>

        <button
          onClick={handleRunEval}
          disabled={isLoading || !activeRepository}
          className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg font-medium text-sm transition-all shadow-md shadow-emerald-600/20"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          <span>{isLoading ? 'Running Benchmark...' : 'Run Evaluation Benchmark'}</span>
        </button>
      </div>

      {evalData && (
        <>
          {/* Metric Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
            <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-1">
              <div className="text-xs text-slate-400 font-medium">Context Precision</div>
              <div className="text-3xl font-bold text-blue-400">{Math.round(evalData.precision_score * 100)}%</div>
              <div className="text-[11px] text-slate-500">Relevant chunks retrieved</div>
            </div>

            <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-1">
              <div className="text-xs text-slate-400 font-medium">Context Recall</div>
              <div className="text-3xl font-bold text-emerald-400">{Math.round(evalData.recall_score * 100)}%</div>
              <div className="text-[11px] text-slate-500">Coverage of standard expected files</div>
            </div>

            <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-1">
              <div className="text-xs text-slate-400 font-medium">Answer Groundedness</div>
              <div className="text-3xl font-bold text-purple-400">{Math.round(evalData.groundedness_score * 100)}%</div>
              <div className="text-[11px] text-slate-500">Zero hallucination score</div>
            </div>

            <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-1">
              <div className="text-xs text-slate-400 font-medium">Citation Accuracy</div>
              <div className="text-3xl font-bold text-amber-400">{Math.round(evalData.citation_accuracy * 100)}%</div>
              <div className="text-[11px] text-slate-500">Source line resolution</div>
            </div>
          </div>

          {/* Question Benchmark Results Table */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="font-bold text-slate-100 text-base">Benchmark Question Test Suite</h3>
            <div className="space-y-3">
              {evalData.results.map((res: any, idx: number) => (
                <div key={idx} className="bg-slate-950 border border-slate-800 p-4 rounded-xl space-y-2">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium text-slate-200 text-sm">{res.question}</h4>
                    <span className="text-xs text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded font-mono">
                      Precision: {Math.round(res.precision * 100)}% | Recall: {Math.round(res.recall * 100)}%
                    </span>
                  </div>

                  <div className="text-xs text-slate-400 space-y-1 font-mono">
                    <div>Expected: {res.expected.join(', ')}</div>
                    <div>Retrieved: {res.retrieved.join(', ')}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};
