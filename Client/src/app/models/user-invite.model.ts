export interface UserInviteCreate {
  email: string;
}

export interface UserInviteResponse {
  id: string;
  token: string;
  email: string;
  expires_at: string;
  used_at: string | null;
  created_at: string;
}

export interface UserInviteListResponse {
  items: UserInviteResponse[];
  total: number;
}

export interface PublicUserInviteContext {
  expires_at: string;
}

export interface PublicUserInviteConsume {
  email: string;
  username: string;
  password: string;
}
