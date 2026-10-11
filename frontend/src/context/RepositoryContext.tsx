import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Repository, Citation } from '../types';
import { api } from '../services/api';
import { useWorkspace } from './WorkspaceContext';

interface ActiveFileSelection {
  filePath: string;
  startLine?: number;
  endLine?: number;
}

interface RepositoryContextType {
  repositories: Repository[];
  activeRepository: Repository | null;
  setActiveRepository: (repo: Repository) => void;
  activeSelection: ActiveFileSelection | null;
  setActiveSelection: (selection: ActiveFileSelection | null) => void;
  jumpToCitation: (citation: Citation) => void;
  refreshRepositories: () => Promise<void>;
  isLoading: boolean;
}

const RepositoryContext = createContext<RepositoryContextType | undefined>(undefined);

export const RepositoryProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { activeWorkspace } = useWorkspace();
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [activeRepository, setActiveRepository] = useState<Repository | null>(null);
  const [activeSelection, setActiveSelection] = useState<ActiveFileSelection | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const refreshRepositories = async () => {
    try {
      const data = await api.getRepositories(activeWorkspace?.id);
      setRepositories(data);
      if (data.length > 0) {
        if (!activeRepository) {
          setActiveRepository(data[0]);
        } else {
          const current = data.find((r) => r.id === activeRepository.id);
          if (current) {
            setActiveRepository(current);
          }
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshRepositories();
  }, [activeWorkspace?.id]);

  // Robust polling for indexing status transitions
  useEffect(() => {
    const isIndexing =
      activeRepository &&
      ['DOWNLOADING', 'PARSING', 'CHUNKING', 'EMBEDDING'].includes(activeRepository.status);

    if (!isIndexing) return;

    const intervalId = setInterval(() => {
      refreshRepositories();
    }, 2000);

    return () => clearInterval(intervalId);
  }, [activeRepository?.id, activeRepository?.status, activeWorkspace?.id]);

  const jumpToCitation = (citation: Citation) => {
    setActiveSelection({
      filePath: citation.file,
      startLine: citation.start_line,
      endLine: citation.end_line
    });
  };

  return (
    <RepositoryContext.Provider
      value={{
        repositories,
        activeRepository,
        setActiveRepository,
        activeSelection,
        setActiveSelection,
        jumpToCitation,
        refreshRepositories,
        isLoading
      }}
    >
      {children}
    </RepositoryContext.Provider>
  );
};

export const useRepository = () => {
  const context = useContext(RepositoryContext);
  if (!context) throw new Error('useRepository must be used within RepositoryProvider');
  return context;
};
