import React, { useState } from 'react';
import { StructuredAIResponse, Citation, AgentRunResult } from '../../types';
import { useRepository } from '../../context/RepositoryContext';
import { Send, Bot, User, FileCode, Sparkles, ChevronDown, ChevronUp, Cpu, Copy, Check } from 'lucide-react';

interface ChatWindowProps {
  onSendMessage: (msg: string, useAgent: boolean) => Promise<void>;
  messages: Array<{
    id: string;
    role: 'user' | 'assistant';
    content: string;
    responseObj?: StructuredAIResponse | AgentRunResult;
  }>;
  isLoading: boolean;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({ onSendMessage, messages, isLoading }) => {
  const { jumpToCitation } = useRepository();
  const [input, setInput] = useState('');
  const [useAgent, setUseAgent] = useState(false);
  const [showReasoning, setShowReasoning] = useState<Record<string, boolean>>({});
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSendMessage(input, useAgent);
    setInput('');
  };

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="flex flex-col h-full bg-[#0b0f17] border-l border-slate-800">
      {/* Header */}
      <div className="h-14 border-b border-slate-800 px-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-blue-400" />
          <h2 className="font-semibold text-sm text-slate-200">Repository Copilot Chat</h2>
        </div>

        <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-lg p-1 text-xs">
          <button
            type="button"
            onClick={() => setUseAgent(false)}
            className={`px-2.5 py-1 rounded-md font-medium transition-all ${
              !useAgent ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            RAG Fast
          </button>
          <button
            type="button"
            onClick={() => setUseAgent(true)}
            className={`px-2.5 py-1 rounded-md font-medium transition-all flex items-center gap-1 ${
              useAgent ? 'bg-purple-600 text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Cpu className="w-3.5 h-3.5" /> Agent Mode
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto">
            <div className="w-12 h-12 rounded-2xl bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-400 mb-3">
              <Sparkles className="w-6 h-6" />
            </div>
            <h3 className="font-semibold text-slate-200 text-base mb-1">Ask CodePilot AI about your repository</h3>
            <p className="text-xs text-slate-400 mb-4">Select a question or type your prompt to retrieve indexed AST context and citations.</p>

            <div className="w-full space-y-2 text-left">
              {[
                "Where is authentication implemented?",
                "Find potential security issues in auth routes.",
                "How does order creation and idempotency work?",
                "Which module handles payment processing?"
              ].map((q, i) => (
                <button
                  key={i}
                  onClick={() => onSendMessage(q, useAgent)}
                  className="w-full text-xs text-slate-300 bg-slate-900/60 hover:bg-slate-800 border border-slate-800 p-2.5 rounded-lg transition-all text-left flex items-center justify-between"
                >
                  <span>"{q}"</span>
                  <ChevronDown className="w-3.5 h-3.5 text-slate-500 -rotate-90" />
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m) => {
          const isUser = m.role === 'user';
          return (
            <div key={m.id} className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
              {!isUser && (
                <div className="w-8 h-8 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 shrink-0">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div className={`max-w-[85%] space-y-3 ${isUser ? 'bg-blue-600 text-white rounded-2xl rounded-tr-none px-4 py-3 text-sm' : ''}`}>
                {!isUser ? (
                  <div className="bg-slate-900/80 border border-slate-800 rounded-2xl rounded-tl-none p-4 text-sm text-slate-200 shadow-sm space-y-3">
                    {/* Copy Answer button */}
                    <div className="flex justify-between items-start">
                      <div className="whitespace-pre-wrap font-sans leading-relaxed">{m.content}</div>
                      <button
                        onClick={() => handleCopy(m.content, m.id)}
                        className="text-slate-400 hover:text-white p-1"
                        title="Copy answer"
                      >
                        {copiedId === m.id ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                      </button>
                    </div>

                    {/* Citations section */}
                    {m.responseObj?.citations && m.responseObj.citations.length > 0 && (
                      <div className="pt-2 border-t border-slate-800/80">
                        <div className="text-xs font-semibold text-slate-400 mb-2 flex items-center gap-1.5">
                          <FileCode className="w-3.5 h-3.5 text-blue-400" /> Referenced Files ({m.responseObj.citations.length})
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {m.responseObj.citations.map((c, idx) => (
                            <button
                              key={idx}
                              onClick={() => jumpToCitation(c)}
                              className="text-xs bg-slate-800 hover:bg-slate-700 text-blue-300 border border-slate-700 px-2.5 py-1 rounded-md font-mono flex items-center gap-1.5 transition-all"
                            >
                              <span>{c.file}:{c.start_line}-{c.end_line}</span>
                              <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-1 rounded">
                                {Math.round(c.relevance * 100)}%
                              </span>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Reasoning Accordion */}
                    {m.responseObj?.reasoning_summary && (
                      <div className="pt-2 border-t border-slate-800/80">
                        <button
                          onClick={() => setShowReasoning((prev) => ({ ...prev, [m.id]: !prev[m.id] }))}
                          className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1.5 font-medium"
                        >
                          {showReasoning[m.id] ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                          <span>Analysis Summary</span>
                        </button>
                        {showReasoning[m.id] && (
                          <div className="mt-2 text-xs text-slate-400 bg-slate-950 p-3 rounded-lg border border-slate-800 font-mono">
                            {m.responseObj.reasoning_summary}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ) : (
                  <div>{m.content}</div>
                )}
              </div>

              {isUser && (
                <div className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 shrink-0">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          );
        })}

        {isLoading && (
          <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-900 border border-slate-800 p-3 rounded-xl w-fit">
            <Sparkles className="w-4 h-4 text-blue-400 animate-spin" />
            <span>CodePilot AI is analyzing indexed repository context...</span>
          </div>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-slate-800 bg-[#0f172a]/60">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={useAgent ? "Ask agent to analyze, find callers, review..." : "Ask questions about auth, order flow, APIs..."}
            className="flex-1 bg-slate-900 border border-slate-800 rounded-lg px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white px-4 py-2.5 rounded-lg transition-all shadow-md shadow-blue-600/20 flex items-center gap-1.5 font-medium text-sm"
          >
            <Send className="w-4 h-4" />
            <span>Send</span>
          </button>
        </div>
      </form>
    </div>
  );
};
