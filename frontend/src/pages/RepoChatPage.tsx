import React, { useState, useEffect } from 'react';
import { useRepository } from '../context/RepositoryContext';
import { api } from '../services/api';
import { FileDetail, StructuredAIResponse, AgentRunResult } from '../types';
import { ChatWindow } from '../components/chat/ChatWindow';
import { MonacoViewer } from '../components/repository/MonacoViewer';

export const RepoChatPage: React.FC = () => {
  const { activeRepository, activeSelection } = useRepository();
  const [messages, setMessages] = useState<Array<{
    id: string;
    role: 'user' | 'assistant';
    content: string;
    responseObj?: StructuredAIResponse | AgentRunResult;
  }>>([]);
  const [isLoading, setIsLoading] = useState(false);

  const [activeFileDetail, setActiveFileDetail] = useState<FileDetail | null>(null);

  useEffect(() => {
    if (activeRepository && activeSelection?.filePath) {
      api.getFileDetail(activeRepository.id, activeSelection.filePath)
        .then(setActiveFileDetail)
        .catch(console.error);
    }
  }, [activeRepository?.id, activeSelection?.filePath]);

  const handleSendMessage = async (msg: string, useAgent: boolean) => {
    if (!activeRepository) return;

    const userMsgId = `msg_${Date.now()}`;
    setMessages((prev) => [...prev, { id: userMsgId, role: 'user', content: msg }]);
    setIsLoading(true);

    try {
      if (useAgent) {
        const res = await api.runAgent(activeRepository.id, msg);
        setMessages((prev) => [
          ...prev,
          { id: `agent_${Date.now()}`, role: 'assistant', content: res.answer, responseObj: res }
        ]);
        if (res.citations && res.citations.length > 0) {
          const topCitation = res.citations[0];
          api.getFileDetail(activeRepository.id, topCitation.file).then(setActiveFileDetail).catch(console.error);
        }
      } else {
        const res = await api.chat(activeRepository.id, msg);
        setMessages((prev) => [
          ...prev,
          { id: `chat_${Date.now()}`, role: 'assistant', content: res.answer, responseObj: res }
        ]);
        if (res.citations && res.citations.length > 0) {
          const topCitation = res.citations[0];
          api.getFileDetail(activeRepository.id, topCitation.file).then(setActiveFileDetail).catch(console.error);
        }
      }
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        { id: `err_${Date.now()}`, role: 'assistant', content: `Error: ${err.message || 'Failed to process AI query'}` }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 h-[calc(100vh-4rem)] overflow-hidden">
      {/* Left: Chat Window */}
      <ChatWindow onSendMessage={handleSendMessage} messages={messages} isLoading={isLoading} />

      {/* Right: Code Citation Monaco Viewer */}
      <div className="h-full border-l border-slate-800 bg-[#0b0f17]">
        {activeFileDetail ? (
          <MonacoViewer
            content={activeFileDetail.content}
            language={activeFileDetail.language}
            filePath={activeFileDetail.path}
            highlightRange={
              activeSelection
                ? { startLine: activeSelection.startLine || 1, endLine: activeSelection.endLine || 20 }
                : null
            }
          />
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-slate-500 text-xs p-6 text-center">
            <p className="font-medium text-slate-400 mb-1">Code Citation Viewer</p>
            <p className="max-w-xs">Click any citation chip in an AI response to open the exact source file and highlight the line range.</p>
          </div>
        )}
      </div>
    </div>
  );
};
