import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Observable, tap } from 'rxjs';

import {
  LoginRequest,
  TokenResponse,
  UserCreate,
  UserListResponse,
  UserResponse,
  UserUpdate,
} from '../models/auth.model';

const TOKEN_KEY = 'access_token';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);

  private readonly token = signal<string | null>(localStorage.getItem(TOKEN_KEY));

  readonly isAuthenticated = computed(() => !!this.token());

  login(data: LoginRequest): Observable<TokenResponse> {
    return this.http.post<TokenResponse>('/api/auth/login', data).pipe(
      tap((res) => {
        localStorage.setItem(TOKEN_KEY, res.access_token);
        this.token.set(res.access_token);
      }),
    );
  }

  logout(): void {
    localStorage.removeItem(TOKEN_KEY);
    this.token.set(null);
  }

  getToken(): string | null {
    return this.token();
  }

  createUser(data: UserCreate): Observable<UserResponse> {
    return this.http.post<UserResponse>('/api/users', data);
  }

  updateUser(id: string, data: UserUpdate): Observable<UserResponse> {
    return this.http.patch<UserResponse>(`/api/users/${id}`, data);
  }

  listUsers(): Observable<UserListResponse> {
    return this.http.get<UserListResponse>('/api/users');
  }
}
