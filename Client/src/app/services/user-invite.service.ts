import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  PublicUserInviteConsume,
  PublicUserInviteContext,
  UserInviteCreate,
  UserInviteListResponse,
  UserInviteResponse,
} from '../models/user-invite.model';

@Injectable({ providedIn: 'root' })
export class UserInviteService {
  private readonly http = inject(HttpClient);

  createInvite(data: UserInviteCreate): Observable<UserInviteResponse> {
    return this.http.post<UserInviteResponse>('/api/user-invites', data);
  }

  listActiveInvites(): Observable<UserInviteListResponse> {
    return this.http.get<UserInviteListResponse>('/api/user-invites');
  }

  getPublicInvite(token: string): Observable<PublicUserInviteContext> {
    return this.http.get<PublicUserInviteContext>(`/api/user-invites/${token}`);
  }

  consumeInvite(token: string, data: PublicUserInviteConsume): Observable<void> {
    return this.http.post<void>(`/api/user-invites/${token}`, data);
  }
}
