export interface BoardMeeting {
  id: string;
  startup_id: string;
  meeting_date: string;
  participants: string | null;
  summary: string | null;
  attention_points: string | null;
  next_steps: string | null;
  created_at: string;
  updated_at: string;
}

export interface BoardMeetingListResponse {
  items: BoardMeeting[];
  total: number;
}

export interface BoardMeetingCreate {
  meeting_date: string;
  participants?: string | null;
  summary?: string | null;
  attention_points?: string | null;
  next_steps?: string | null;
}

export interface BoardMeetingUpdate {
  meeting_date?: string;
  participants?: string | null;
  summary?: string | null;
  attention_points?: string | null;
  next_steps?: string | null;
}
