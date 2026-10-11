import { Injectable, inject } from '@angular/core';
import { BehaviorSubject, Observable, catchError, of, tap } from 'rxjs';
import { ApiService } from './api.service';
import { Workspace } from '../models/types';

@Injectable({
  providedIn: 'root'
})
export class WorkspaceService {
  private api = inject(ApiService);

  private workspacesSubject = new BehaviorSubject<Workspace[]>([]);
  workspaces$ = this.workspacesSubject.asObservable();

  private activeWorkspaceSubject = new BehaviorSubject<Workspace | null>(null);
  activeWorkspace$ = this.activeWorkspaceSubject.asObservable();

  private isLoadingSubject = new BehaviorSubject<boolean>(true);
  isLoading$ = this.isLoadingSubject.asObservable();

  get activeWorkspace(): Workspace | null {
    return this.activeWorkspaceSubject.value;
  }

  constructor() {
    this.refreshWorkspaces();
  }

  setActiveWorkspace(ws: Workspace): void {
    this.activeWorkspaceSubject.next(ws);
  }

  refreshWorkspaces(): Observable<Workspace[]> {
    this.isLoadingSubject.next(true);
    return this.api.getWorkspaces().pipe(
      tap((data) => {
        this.workspacesSubject.next(data);
        if (data.length > 0 && !this.activeWorkspaceSubject.value) {
          this.activeWorkspaceSubject.next(data[0]);
        }
        this.isLoadingSubject.next(false);
      }),
      catchError((err) => {
        console.error('Failed to load workspaces:', err);
        this.isLoadingSubject.next(false);
        return of([]);
      })
    );
  }
}
