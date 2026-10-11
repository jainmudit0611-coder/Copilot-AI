import { Routes } from '@angular/router';
import { authGuard } from './guards/auth.guard';
import { MainLayoutComponent } from './layouts/main-layout/main-layout.component';
import { LoginComponent } from './pages/login/login.component';
import { RegisterComponent } from './pages/register/register.component';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { RepositoriesComponent } from './pages/repositories/repositories.component';
import { RepoExplorerComponent } from './pages/repo-explorer/repo-explorer.component';
import { RepoChatComponent } from './pages/repo-chat/repo-chat.component';
import { BugAnalyzerComponent } from './pages/bug-analyzer/bug-analyzer.component';
import { CodeReviewComponent } from './pages/code-review/code-review.component';
import { TestGeneratorComponent } from './pages/test-generator/test-generator.component';
import { DocGeneratorComponent } from './pages/doc-generator/doc-generator.component';
import { EvaluationsComponent } from './pages/evaluations/evaluations.component';
import { ObservabilityComponent } from './pages/observability/observability.component';
import { SettingsComponent } from './pages/settings/settings.component';

export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: 'register', component: RegisterComponent },
  {
    path: '',
    component: MainLayoutComponent,
    canActivate: [authGuard],
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      { path: 'dashboard', component: DashboardComponent },
      { path: 'repositories', component: RepositoriesComponent },
      { path: 'explorer', component: RepoExplorerComponent },
      { path: 'chat', component: RepoChatComponent },
      { path: 'bugs', component: BugAnalyzerComponent },
      { path: 'reviews', component: CodeReviewComponent },
      { path: 'tests', component: TestGeneratorComponent },
      { path: 'docs', component: DocGeneratorComponent },
      { path: 'evaluations', component: EvaluationsComponent },
      { path: 'observability', component: ObservabilityComponent },
      { path: 'settings', component: SettingsComponent },
    ]
  },
  { path: '**', redirectTo: 'dashboard' }
];
