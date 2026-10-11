import React, { useRef, useEffect } from 'react';
import Editor, { OnMount } from '@monaco-editor/react';

interface MonacoViewerProps {
  content: string;
  language: string;
  filePath: string;
  highlightRange?: { startLine: number; endLine: number } | null;
}

export const MonacoViewer: React.FC<MonacoViewerProps> = ({ content, language, filePath, highlightRange }) => {
  const editorRef = useRef<any>(null);

  const getMonacoLang = (lang: string) => {
    switch (lang.toLowerCase()) {
      case 'typescript':
        return 'typescript';
      case 'javascript':
        return 'javascript';
      case 'python':
        return 'python';
      case 'json':
        return 'json';
      case 'markdown':
        return 'markdown';
      case 'sql':
        return 'sql';
      case 'css':
        return 'css';
      case 'html':
        return 'html';
      default:
        return 'plaintext';
    }
  };

  const handleEditorDidMount: OnMount = (editor) => {
    editorRef.current = editor;
  };

  useEffect(() => {
    if (editorRef.current && highlightRange && highlightRange.startLine) {
      const editor = editorRef.current;
      editor.revealLineInCenter(highlightRange.startLine);
      editor.setSelection({
        startLineNumber: highlightRange.startLine,
        startColumn: 1,
        endLineNumber: highlightRange.endLine || highlightRange.startLine,
        endColumn: 100
      });
    }
  }, [highlightRange]);

  return (
    <div className="h-full w-full flex flex-col bg-[#0b0f17]">
      <div className="h-10 bg-[#0f172a] border-b border-slate-800 px-4 flex items-center justify-between text-xs text-slate-400">
        <span className="font-mono text-slate-200">{filePath}</span>
        {highlightRange && (
          <span className="bg-blue-600/20 text-blue-400 px-2 py-0.5 rounded border border-blue-500/30">
            Highlighted: Lines {highlightRange.startLine}-{highlightRange.endLine}
          </span>
        )}
      </div>
      <div className="flex-1">
        <Editor
          height="100%"
          language={getMonacoLang(language)}
          value={content}
          theme="vs-dark"
          onMount={handleEditorDidMount}
          options={{
            readOnly: true,
            fontSize: 13,
            minimap: { enabled: true },
            scrollBeyondLastLine: false,
            automaticLayout: true,
            fontFamily: "'Fira Code', monospace",
          }}
        />
      </div>
    </div>
  );
};
