import { Injectable, inject, OnDestroy } from '@angular/core';
import { BehaviorSubject, Observable, Subscription, catchError, interval, of, switchMap, tap } from 'rxjs';
import { ApiService } from './api.service';
import { WorkspaceService } from './workspace.service';
import { Repository, Citation, ActiveFileSelection } from '../models/types';

@Injectable({
  providedIn: 'root'
})
export class RepositoryService implements OnDestroy {
  private api = inject(ApiService);
  private workspaceService = inject(WorkspaceService);

  private repositoriesSubject = new BehaviorSubject<Repository[]>([]);
  repositories$ = this.repositoriesSubject.asObservable();

  private activeRepositorySubject = new BehaviorSubject<Repository | null>(null);
  activeRepository$ = this.activeRepositorySubject.asObservable();

  private activeSelectionSubject = new BehaviorSubject<ActiveFileSelection | null>(null);
  activeSelection$ = this.activeSelectionSubject.asObservable();

  private isLoadingSubject = new BehaviorSubject<boolean>(true);
  isLoading$ = this.isLoadingSubject.asObservable();

  private pollSubscription: Subscription | null = null;
  private wsSubscription: Subscription | null = null;

  get activeRepository(): Repository | null {
    return this.activeRepositorySubject.value;
  }

  get repositories(): Repository[] {
    return this.repositoriesSubject.value;
  }

  get activeSelection(): ActiveFileSelection | null {
    return this.activeSelectionSubject.value;
  }

  constructor() {
    this.wsSubscription = this.workspaceService.activeWorkspace$.subscribe((ws) => {
      this.refreshRepositories(ws?.id).subscribe();
    });

    // Check if active repository enters or leaves indexing states
    this.activeRepository$.subscribe((repo) => {
      this.handleIndexingPolling(repo);
    });
  }

  ngOnDestroy(): void {
    this.pollSubscription?.unsubscribe();
    this.wsSubscription?.unsubscribe();
  }

  setActiveRepository(repo: Repository): void {
    this.activeRepositorySubject.next(repo);
  }

  setActiveSelection(selection: ActiveFileSelection | null): void {
    this.activeSelectionSubject.next(selection);
  }

  jumpToCitation(citation: Citation): void {
    this.setActiveSelection({
      filePath: citation.file,
      startLine: citation.start_line,
      endLine: citation.end_line
    });
  }

  refreshRepositories(workspaceId?: string): Observable<Repository[]> {
    const wsId = workspaceId || this.workspaceService.activeWorkspace?.id;
    return this.api.getRepositories(wsId).pipe(
      tap((data) => {
        this.repositoriesSubject.next(data);
        if (data.length > 0) {
          const current = this.activeRepositorySubject.value;
          if (!current) {
            this.activeRepositorySubject.next(data[0]);
          } else {
            const found = data.find((r) => r.id === current.id);
            if (found) {
              this.activeRepositorySubject.next(found);
            }
          }
        }
        this.isLoadingSubject.next(false);
      }),
      catchError((err) => {
        console.error('Error refreshing repositories:', err);
        this.isLoadingSubject.next(false);
        return of([]);
      })
    );
  }

  private handleIndexingPolling(repo: Repository | null): void {
    const isIndexing =
      !!repo &&
      ['DOWNLOADING', 'PARSING', 'CHUNKING', 'EMBEDDING'].includes(repo.status);

    if (isIndexing) {
      if (!this.pollSubscription || this.pollSubscription.closed) {
        this.pollSubscription = interval(2000).pipe(
          switchMap(() => this.refreshRepositories())
        ).subscribe();
      }
    } else {
      if (this.pollSubscription && !this.pollSubscription.closed) {
        this.pollSubscription.unsubscribe();
        this.pollSubscription = null;
      }
    }
  }
}
