export interface ChatUser {
  id: number;
  username: string;
  full_name?: string;
  avatar_url?: string;
  email?: string;
  auth_provider?: string;
  created_at?: string;
}

export interface Message {
  id: number;
  content: string;
  created_at: string;
  sender_id: number;
  receiver_id: number;
  is_read: boolean;
  sender?: ChatUser;
}
export interface SearchUser {
  id: number;
  username: string;
  full_name?: string;
  avatar_url?: string;
  email?: string;
}
