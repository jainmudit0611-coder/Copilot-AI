import React, { useState } from 'react';
import { Check, X, Code2 } from 'lucide-react';

interface DiffViewerProps {
  patch: string;
  onApprove?: () => void;
  onReject?: () => void;
}

export const DiffViewer: React.FC<DiffViewerProps> = ({ patch, onApprove, onReject }) => {
  const [status, setStatus] = useState<'IDLE' | 'APPROVED' | 'REJECTED'>('IDLE');

  const handleApprove = () => {
    setStatus('APPROVED');
    if (onApprove) onApprove();
  };

  const handleReject = () => {
    setStatus('REJECTED');
    if (onReject) onReject();
  };

  const diffLines = patch.split('\n');

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
      <div className="h-10 bg-[#0f172a] border-b border-slate-800 px-4 flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
          <Code2 className="w-4 h-4 text-blue-400" /> Proposed Unified Diff Patch
        </div>

        {status === 'IDLE' ? (
          <div className="flex items-center gap-2">
            <button
              onClick={handleReject}
              className="flex items-center gap-1 text-xs bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 px-2.5 py-1 rounded font-medium transition-all"
            >
              <X className="w-3.5 h-3.5" /> Reject
            </button>
            <button
              onClick={handleApprove}
              className="flex items-center gap-1 text-xs bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-2.5 py-1 rounded font-medium transition-all"
            >
              <Check className="w-3.5 h-3.5" /> Approve Patch
            </button>
          </div>
        ) : (
          <span
            className={`text-xs px-2.5 py-1 rounded font-medium ${
              status === 'APPROVED' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
            }`}
          >
            {status === 'APPROVED' ? 'Patch Approved (Pending User Write Confirmation)' : 'Patch Rejected'}
          </span>
        )}
      </div>

      <div className="p-4 font-mono text-xs overflow-x-auto bg-[#0b0f17] max-h-96">
        {diffLines.map((line: string, idx: number) => {
          let bgClass = 'text-slate-400';
          if (line.startsWith('+')) bgClass = 'bg-emerald-500/10 text-emerald-400 font-semibold px-2 py-0.5 rounded-sm';
          else if (line.startsWith('-')) bgClass = 'bg-rose-500/10 text-rose-400 font-semibold px-2 py-0.5 rounded-sm';
          else if (line.startsWith('@')) bgClass = 'text-blue-400 font-bold';

          return (
            <div key={idx} className={`${bgClass} whitespace-pre`}>
              {line}
            </div>
          );
        })}
      </div>
    </div>
  );
};
