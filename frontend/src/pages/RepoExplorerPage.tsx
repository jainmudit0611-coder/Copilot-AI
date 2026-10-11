import React, { useState, useEffect } from 'react';
import { useRepository } from '../context/RepositoryContext';
import { api } from '../services/api';
import { FileNode, FileDetail } from '../types';
import { FileTree } from '../components/repository/FileTree';
import { MonacoViewer } from '../components/repository/MonacoViewer';
import { FileCode, Layers, Info } from 'lucide-react';

export const RepoExplorerPage: React.FC = () => {
  const { activeRepository, activeSelection } = useRepository();
  const [files, setFiles] = useState<FileNode[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileDetail, setFileDetail] = useState<FileDetail | null>(null);

  useEffect(() => {
    if (activeRepository) {
      api.getFiles(activeRepository.id).then((data) => {
        setFiles(data);
        if (data.length > 0 && !selectedFile) {
          setSelectedFile(data[0].path);
        }
      });
    }
  }, [activeRepository?.id]);

  useEffect(() => {
    if (activeSelection?.filePath) {
      setSelectedFile(activeSelection.filePath);
    }
  }, [activeSelection]);

  useEffect(() => {
    if (activeRepository && selectedFile) {
      api.getFileDetail(activeRepository.id, selectedFile).then(setFileDetail).catch(console.error);
    }
  }, [activeRepository?.id, selectedFile]);

  return (
    <div className="flex h-[calc(100vh-4rem)] overflow-hidden">
      {/* Left: File Tree */}
      <FileTree
        files={files}
        selectedFile={selectedFile}
        onSelectFile={(path) => setSelectedFile(path)}
      />

      {/* Center: Monaco Viewer */}
      <div className="flex-1 h-full">
        {fileDetail ? (
          <MonacoViewer
            content={fileDetail.content}
            language={fileDetail.language}
            filePath={fileDetail.path}
            highlightRange={
              activeSelection?.filePath === fileDetail.path
                ? { startLine: activeSelection.startLine || 1, endLine: activeSelection.endLine || 10 }
                : null
            }
          />
        ) : (
          <div className="h-full flex items-center justify-center text-slate-500 text-sm">
            Select a file from the repository tree to inspect.
          </div>
        )}
      </div>

      {/* Right: Metadata Panel */}
      <div className="w-72 bg-[#0f172a] border-l border-slate-800 p-4 space-y-4 overflow-y-auto">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-300 uppercase tracking-wider">
          <Info className="w-4 h-4 text-blue-400" /> File Context
        </div>

        {fileDetail && (
          <div className="space-y-3 text-xs">
            <div className="bg-slate-900 border border-slate-800 p-3 rounded-lg space-y-1 font-mono text-slate-300">
              <div>Path: {fileDetail.path}</div>
              <div>Language: {fileDetail.language}</div>
              <div>Size: {Math.round(fileDetail.size_bytes / 1024)} KB</div>
            </div>

            <div className="bg-slate-900 border border-slate-800 p-3 rounded-lg space-y-2">
              <div className="font-semibold text-slate-300 flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-purple-400" /> RAG Chunk Info
              </div>
              <p className="text-slate-400 text-[11px]">Indexed with symbol boundaries and AST signatures in pgvector.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
