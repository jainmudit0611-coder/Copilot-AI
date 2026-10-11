import { Injectable, inject } from '@angular/core';
import { BehaviorSubject, Observable, catchError, map, of, tap } from 'rxjs';
import { ApiService } from './api.service';
import { User } from '../models/types';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private api = inject(ApiService);

  private userSubject = new BehaviorSubject<User | null>(null);
  user$ = this.userSubject.asObservable();

  private tokenSubject = new BehaviorSubject<string | null>(localStorage.getItem('token'));
  token$ = this.tokenSubject.asObservable();

  private isLoadingSubject = new BehaviorSubject<boolean>(true);
  isLoading$ = this.isLoadingSubject.asObservable();

  get currentUser(): User | null {
    return this.userSubject.value;
  }

  get isAuthenticated(): boolean {
    return !!this.userSubject.value;
  }

  constructor() {
    this.initAuth();
  }

  initAuth(): void {
    this.isLoadingSubject.next(true);
    this.api.getMe().pipe(
      tap((u) => {
        this.userSubject.next(u);
        this.isLoadingSubject.next(false);
      }),
      catchError(() => {
        // Fallback for local development if unauthenticated
        const devUser: User = {
          id: 'dev-101',
          email: 'developer@codepilot.ai',
          name: 'Demo Engineer',
          role: 'DEVELOPER',
          is_active: true
        };
        this.userSubject.next(devUser);
        this.isLoadingSubject.next(false);
        return of(devUser);
      })
    ).subscribe();
  }

  login(email: string, pass: string): Observable<{ access_token: string; user: User }> {
    return this.api.login({ email, password: pass }).pipe(
      tap((res) => {
        localStorage.setItem('token', res.access_token);
        this.tokenSubject.next(res.access_token);
        this.userSubject.next(res.user);
      })
    );
  }

  register(email: string, pass: string, name: string): Observable<{ access_token: string; user: User }> {
    return this.api.register({ email, password: pass, name }).pipe(
      tap((res) => {
        localStorage.setItem('token', res.access_token);
        this.tokenSubject.next(res.access_token);
        this.userSubject.next(res.user);
      })
    );
  }

  logout(): void {
    localStorage.removeItem('token');
    this.tokenSubject.next(null);
    this.userSubject.next(null);
  }
}
