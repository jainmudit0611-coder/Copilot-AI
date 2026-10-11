import React, { useState } from 'react';
import { Settings as SettingsIcon, Save, Key, Database, Shield } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const [provider, setProvider] = useState('azure');
  const [endpoint, setEndpoint] = useState('https://my-azure-openai.openai.azure.com/');
  const [apiKey, setApiKey] = useState('••••••••••••••••••••••••');
  const [deployment, setDeployment] = useState('gpt-4o');
  const [embeddingDeployment, setEmbeddingDeployment] = useState('text-embedding-3-small');
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="p-8 space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-slate-100 tracking-tight flex items-center gap-2">
          <SettingsIcon className="w-6 h-6 text-slate-400" /> Platform Settings
        </h1>
        <p className="text-sm text-slate-400 mt-1">Configure LLM providers, vector indexing parameters, and security limits.</p>
      </div>

      <form onSubmit={handleSave} className="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-6 shadow-sm">
        <div className="space-y-4">
          <h3 className="font-bold text-slate-200 text-sm flex items-center gap-2 border-b border-slate-800 pb-2">
            <Key className="w-4 h-4 text-blue-400" /> LLM Provider Settings
          </h3>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Provider Mode</label>
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 font-mono"
            >
              <option value="azure">Azure OpenAI</option>
              <option value="openai">Standard OpenAI</option>
              <option value="mock">Local Development Mock</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Azure Endpoint</label>
            <input
              type="text"
              value={endpoint}
              onChange={(e) => setEndpoint(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 font-mono"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">API Key</label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 font-mono"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">LLM Deployment Name</label>
              <input
                type="text"
                value={deployment}
                onChange={(e) => setDeployment(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Embedding Deployment</label>
              <input
                type="text"
                value={embeddingDeployment}
                onChange={(e) => setEmbeddingDeployment(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 font-mono"
              />
            </div>
          </div>
        </div>

        <button
          type="submit"
          className="bg-blue-600 hover:bg-blue-500 text-white font-medium px-6 py-2.5 rounded-lg text-sm transition-all shadow-md shadow-blue-600/20 flex items-center gap-2"
        >
          <Save className="w-4 h-4" />
          <span>{saved ? 'Settings Saved!' : 'Save Settings'}</span>
        </button>
      </form>
    </div>
  );
};
