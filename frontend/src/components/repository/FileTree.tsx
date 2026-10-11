import React from 'react';
import { FileNode } from '../../types';
import { FileCode, FileJson, FileText, ChevronRight, Hash } from 'lucide-react';

interface FileTreeProps {
  files: FileNode[];
  selectedFile: string | null;
  onSelectFile: (filePath: string) => void;
}

export const FileTree: React.FC<FileTreeProps> = ({ files, selectedFile, onSelectFile }) => {
  const getFileIcon = (lang: string) => {
    switch (lang.toLowerCase()) {
      case 'typescript':
      case 'javascript':
        return <FileCode className="w-4 h-4 text-blue-400" />;
      case 'python':
        return <FileCode className="w-4 h-4 text-amber-400" />;
      case 'json':
      case 'yaml':
        return <FileJson className="w-4 h-4 text-emerald-400" />;
      case 'markdown':
        return <FileText className="w-4 h-4 text-purple-400" />;
      default:
        return <FileText className="w-4 h-4 text-slate-400" />;
    }
  };

  return (
    <div className="w-64 bg-[#0f172a]/80 border-r border-slate-800 h-full overflow-y-auto p-2">
      <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider px-3 py-2">
        Repository Files ({files.length})
      </div>
      <div className="space-y-0.5">
        {files.map((file) => {
          const isSelected = selectedFile === file.path;
          return (
            <button
              key={file.id}
              onClick={() => onSelectFile(file.path)}
              className={`w-full text-left px-3 py-2 rounded-md text-xs font-mono flex items-center justify-between transition-all ${
                isSelected
                  ? 'bg-blue-600/20 text-blue-300 font-semibold border border-blue-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <div className="flex items-center gap-2 truncate">
                {getFileIcon(file.language)}
                <span className="truncate">{file.path}</span>
              </div>
              <span className="text-[10px] text-slate-500 shrink-0 ml-1">{Math.round(file.size_bytes / 1024)}k</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
