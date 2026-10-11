import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './context/AuthContext';
import { WorkspaceProvider } from './context/WorkspaceContext';
import { RepositoryProvider } from './context/RepositoryContext';
import { MainLayout } from './layouts/MainLayout';

import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { RepositoriesPage } from './pages/RepositoriesPage';
import { RepoExplorerPage } from './pages/RepoExplorerPage';
import { RepoChatPage } from './pages/RepoChatPage';
import { BugAnalyzerPage } from './pages/BugAnalyzerPage';
import { CodeReviewPage } from './pages/CodeReviewPage';
import { TestGeneratorPage } from './pages/TestGeneratorPage';
import { DocGeneratorPage } from './pages/DocGeneratorPage';
import { EvaluationsPage } from './pages/EvaluationsPage';
import { ObservabilityPage } from './pages/ObservabilityPage';
import { SettingsPage } from './pages/SettingsPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <WorkspaceProvider>
          <RepositoryProvider>
            <BrowserRouter>
              <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />

                <Route element={<MainLayout />}>
                  <Route path="/" element={<Navigate to="/dashboard" replace />} />
                  <Route path="/dashboard" element={<DashboardPage />} />
                  <Route path="/repositories" element={<RepositoriesPage />} />
                  <Route path="/explorer" element={<RepoExplorerPage />} />
                  <Route path="/chat" element={<RepoChatPage />} />
                  <Route path="/bugs" element={<BugAnalyzerPage />} />
                  <Route path="/reviews" element={<CodeReviewPage />} />
                  <Route path="/tests" element={<TestGeneratorPage />} />
                  <Route path="/docs" element={<DocGeneratorPage />} />
                  <Route path="/evaluations" element={<EvaluationsPage />} />
                  <Route path="/observability" element={<ObservabilityPage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                </Route>
              </Routes>
            </BrowserRouter>
          </RepositoryProvider>
        </WorkspaceProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
};
