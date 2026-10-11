import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { IconComponent } from '../../components/common/icon/icon.component';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, IconComponent],
  template: `
    <div class="min-h-screen bg-[#0b0f17] flex items-center justify-center p-4">
      <div class="max-w-md w-full bg-slate-900 border border-slate-800 p-8 rounded-2xl shadow-xl space-y-6">
        <div class="text-center space-y-2">
          <div class="w-12 h-12 rounded-xl bg-blue-600 flex items-center justify-center text-white font-bold mx-auto shadow-lg shadow-blue-500/20">
            <app-icon name="sparkles" class="w-6 h-6 text-white"></app-icon>
          </div>
          <h2 class="text-2xl font-bold text-slate-100 tracking-tight">Create Workspace</h2>
          <p class="text-xs text-slate-400">Join CodePilot AI Software Engineering Copilot</p>
        </div>

        <div *ngIf="error" class="p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg text-xs text-rose-400">
          {{ error }}
        </div>

        <form (ngSubmit)="handleSubmit()" class="space-y-4">
          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-1">Full Name</label>
            <input
              type="text"
              required
              [(ngModel)]="name"
              name="name"
              placeholder="e.g. Jane Developer"
              class="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-1">Work Email</label>
            <input
              type="email"
              required
              [(ngModel)]="email"
              name="email"
              placeholder="name@company.com"
              class="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-1">Password</label>
            <input
              type="password"
              required
              [(ngModel)]="password"
              name="password"
              placeholder="••••••••••••"
              class="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 focus:outline-none focus:border-blue-500"
            />
          </div>

          <button
            type="submit"
            [disabled]="isLoading"
            class="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-semibold py-3 rounded-lg text-sm transition-all shadow-md shadow-blue-600/20 flex items-center justify-center gap-2"
          >
            <span>{{ isLoading ? 'Creating Account...' : 'Create Account' }}</span>
            <app-icon name="arrow-right" class="w-4 h-4"></app-icon>
          </button>
        </form>

        <div class="text-center text-xs text-slate-400">
          Already have an account?
          <a routerLink="/login" class="text-blue-400 hover:underline ml-1">
            Sign In
          </a>
        </div>
      </div>
    </div>
  `
})
export class RegisterComponent {
  private authService = inject(AuthService);
  private router = inject(Router);

  name = '';
  email = '';
  password = '';
  error = '';
  isLoading = false;

  handleSubmit(): void {
    this.isLoading = true;
    this.error = '';

    this.authService.register(this.email, this.password, this.name).subscribe({
      next: () => {
        this.isLoading = false;
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.isLoading = false;
        this.error = err.error?.detail?.message || err.error?.detail || err.message || 'Registration failed';
      }
    });
  }
}
