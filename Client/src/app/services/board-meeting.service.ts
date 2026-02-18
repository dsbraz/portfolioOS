import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  BoardMeeting,
  BoardMeetingCreate,
  BoardMeetingListResponse,
  BoardMeetingUpdate,
} from '../models/board-meeting.model';

@Injectable({ providedIn: 'root' })
export class BoardMeetingService {
  private readonly http = inject(HttpClient);

  private baseUrl(startupId: string): string {
    return `/api/startups/${startupId}/meetings`;
  }

  list(startupId: string): Observable<BoardMeetingListResponse> {
    return this.http.get<BoardMeetingListResponse>(this.baseUrl(startupId));
  }

  getById(startupId: string, meetingId: string): Observable<BoardMeeting> {
    return this.http.get<BoardMeeting>(`${this.baseUrl(startupId)}/${meetingId}`);
  }

  create(startupId: string, data: BoardMeetingCreate): Observable<BoardMeeting> {
    return this.http.post<BoardMeeting>(this.baseUrl(startupId), data);
  }

  update(
    startupId: string,
    meetingId: string,
    data: BoardMeetingUpdate,
  ): Observable<BoardMeeting> {
    return this.http.patch<BoardMeeting>(
      `${this.baseUrl(startupId)}/${meetingId}`,
      data,
    );
  }

  delete(startupId: string, meetingId: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl(startupId)}/${meetingId}`);
  }
}
