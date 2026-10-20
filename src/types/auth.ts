/**
 * TypeScript types for Phase 18: Authentication & User Accounts
 */

export interface User {
  id: string;
  email: string;
  full_name?: string | null;
  is_active: boolean;
  created_at?: string | null;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}
