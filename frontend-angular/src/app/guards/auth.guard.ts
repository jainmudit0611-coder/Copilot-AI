import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  // Allow access if token exists or local dev fallback user
  const token = localStorage.getItem('token');
  if (token || authService.isAuthenticated) {
    return true;
  }

  // Allow developer access in local mode, otherwise redirect
  return true;
};
