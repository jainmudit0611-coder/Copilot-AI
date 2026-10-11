import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { AIRunMetric } from '../types';
import { Activity, DollarSign, Zap, Cpu, Database } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

export const ObservabilityPage: React.FC = () => {
  const [runs, setRuns] = useState<AIRunMetric[]>([]);
  const [summary, setSummary] = useState<any>(null);

  useEffect(() => {
    api.getAIRuns().then(setRuns).catch(console.error);
    api.getObservabilitySummary().then(setSummary).catch(console.error);
  }, []);

  const chartData = runs.slice(0, 15).reverse().map((r, i) => ({
    name: `Q${i + 1}`,
    latency: Math.round(r.latency_ms),
    tokens: r.prompt_tokens + r.completion_tokens,
    cost: r.estimated_cost_usd
  }));

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-slate-100 tracking-tight flex items-center gap-2">
          <Activity className="w-6 h-6 text-blue-400" /> Observability & AI Cost Analytics
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Track latency, prompt token usage, completion token usage, and estimated LLM expenditure per feature.
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-1">
          <div className="text-xs text-slate-400 font-medium">Total AI Executions</div>
          <div className="text-2xl font-bold text-slate-100">{summary?.total_ai_queries || 0}</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-1">
          <div className="text-xs text-slate-400 font-medium">Total Tokens Consumed</div>
          <div className="text-2xl font-bold text-purple-400">{summary?.total_tokens_consumed || 0}</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-1">
          <div className="text-xs text-slate-400 font-medium">Average Latency</div>
          <div className="text-2xl font-bold text-amber-400">{summary?.average_latency_ms || 0} ms</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-1">
          <div className="text-xs text-slate-400 font-medium">Estimated LLM Cost</div>
          <div className="text-2xl font-bold text-emerald-400">${summary?.total_cost_usd || '0.0000'}</div>
        </div>
      </div>

      {/* Recharts Latency and Tokens Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4">
          <h3 className="font-bold text-slate-200 text-sm">Query Latency Trend (ms)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorLatency" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip contentStyle={{ background: '#0f172a', borderColor: '#1e293b', borderRadius: '8px' }} />
                <Area type="monotone" dataKey="latency" stroke="#3b82f6" fillOpacity={1} fill="url(#colorLatency)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4">
          <h3 className="font-bold text-slate-200 text-sm">Token Consumption per Query</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip contentStyle={{ background: '#0f172a', borderColor: '#1e293b', borderRadius: '8px' }} />
                <Bar dataKey="tokens" fill="#a855f7" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
        <h3 className="font-bold text-slate-100 text-base">Execution Logs Table</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400">
                <th className="py-2.5 px-3">Feature</th>
                <th className="py-2.5 px-3">Model</th>
                <th className="py-2.5 px-3">Prompt Tokens</th>
                <th className="py-2.5 px-3">Completion Tokens</th>
                <th className="py-2.5 px-3">Latency (ms)</th>
                <th className="py-2.5 px-3">Cost ($)</th>
                <th className="py-2.5 px-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r) => (
                <tr key={r.id} className="border-b border-slate-800/60 hover:bg-slate-850">
                  <td className="py-2.5 px-3 text-slate-200 font-semibold">{r.feature}</td>
                  <td className="py-2.5 px-3 text-slate-400">{r.model}</td>
                  <td className="py-2.5 px-3 text-slate-400">{r.prompt_tokens}</td>
                  <td className="py-2.5 px-3 text-slate-400">{r.completion_tokens}</td>
                  <td className="py-2.5 px-3 text-amber-400">{Math.round(r.latency_ms)}</td>
                  <td className="py-2.5 px-3 text-emerald-400">${r.estimated_cost_usd.toFixed(6)}</td>
                  <td className="py-2.5 px-3 text-emerald-400">{r.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
