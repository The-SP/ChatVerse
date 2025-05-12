export interface ChatUser {
  id: number;
  username: string;
  full_name?: string;
  avatar_url?: string;
}

export interface Message {
  id: number;
  content: string;
  created_at: string;
  sender_id: number;
  receiver_id: number;
  is_read: boolean;
  sender?: {
    id: number;
    username: string;
    avatar_url?: string;
    full_name?: string;
  };
}
