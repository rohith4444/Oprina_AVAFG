export interface User {
  id?: string;
  email: string;
  name?: string;
  avatar?: string;
}

export interface Conversation {
  id: string;
  title: string;
  timestamp: number;
  messages: Message[];
}

export interface Message {
  id: string;
  sender: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}