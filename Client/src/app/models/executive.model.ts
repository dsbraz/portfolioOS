export interface Executive {
  id: string;
  startup_id: string;
  name: string;
  role: string | null;
  email: string | null;
  phone: string | null;
  linkedin: string | null;
  created_at: string;
  updated_at: string;
}

export interface ExecutiveListResponse {
  items: Executive[];
  total: number;
}

export interface ExecutiveCreate {
  name: string;
  role?: string | null;
  email?: string | null;
  phone?: string | null;
  linkedin?: string | null;
}

export interface ExecutiveUpdate {
  name?: string;
  role?: string | null;
  email?: string | null;
  phone?: string | null;
  linkedin?: string | null;
}
