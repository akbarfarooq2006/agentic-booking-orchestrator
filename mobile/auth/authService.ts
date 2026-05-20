/**
 * Auth Service — API client for authentication endpoints.
 *
 * Handles all HTTP communication with the backend auth endpoints.
 * Manages the Authorization header automatically for protected requests.
 *
 * Usage:
 *   import { authService } from './authService';
 *   const result = await authService.login('user@example.com', 'password');
 */

import { getAccessToken } from './storage';

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

/**
 * Base URL for the backend API.
 *
 * For local development with Expo Go:
 *   - iOS Simulator: http://localhost:8000
 *   - Android Emulator: http://10.0.2.2:8000
 *   - Physical device: http://<your-local-ip>:8000
 *
 * Replace with your production URL when deploying.
 */
const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** Matches backend's UserProfile schema */
export interface UserProfile {
  id: string;
  email: string;
  role: 'user' | 'provider' | 'admin';
  created_at?: string;
}

/** Matches backend's AuthResponse schema */
export interface AuthResponse {
  access_token: string;
  refresh_token: string | null;
  token_type: string;
  expires_in: number | null;
  user: UserProfile;
}

/** Matches backend's MessageResponse schema */
export interface MessageResponse {
  message: string;
  success: boolean;
}

/** Standardized error shape */
export interface AuthError {
  detail: string;
  error_code?: string;
}

// ---------------------------------------------------------------------------
// HTTP Helper
// ---------------------------------------------------------------------------

/**
 * Make an authenticated or unauthenticated request to the backend.
 *
 * Automatically attaches the Bearer token if one exists in secure storage.
 * Throws a structured error if the response is not OK.
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = await getAccessToken();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  // Attach Bearer token if available
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  // Parse response body
  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const error: AuthError = {
      detail: data?.detail || `Request failed with status ${response.status}`,
      error_code: data?.error_code,
    };
    throw error;
  }

  return data as T;
}

// ---------------------------------------------------------------------------
// Auth API Methods
// ---------------------------------------------------------------------------

export const authService = {
  /**
   * POST /auth/signup — Create a new user account.
   *
   * @param email - User's email address.
   * @param password - Password (min 6 characters).
   * @param role - Role to assign: 'user' | 'provider' | 'admin'. Defaults to 'user'.
   * @returns AuthResponse with access_token and user profile.
   */
  async signup(
    email: string,
    password: string,
    role: 'user' | 'provider' | 'admin' = 'user'
  ): Promise<AuthResponse> {
    return apiRequest<AuthResponse>('/auth/signup', {
      method: 'POST',
      body: JSON.stringify({ email, password, role }),
    });
  },

  /**
   * POST /auth/login — Authenticate with email and password.
   *
   * @param email - User's email address.
   * @param password - User's password.
   * @returns AuthResponse with access_token and user profile.
   */
  async login(email: string, password: string): Promise<AuthResponse> {
    return apiRequest<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  },

  /**
   * POST /auth/logout — End the current session.
   *
   * Requires a valid access token in secure storage.
   * After calling this, clear tokens from storage.
   *
   * @returns MessageResponse confirming logout.
   */
  async logout(): Promise<MessageResponse> {
    return apiRequest<MessageResponse>('/auth/logout', {
      method: 'POST',
    });
  },

  /**
   * GET /auth/me — Fetch the current user's profile.
   *
   * Used on app startup to validate the stored token and hydrate user state.
   * If the token is expired/invalid, this will throw (401).
   *
   * @returns UserProfile of the authenticated user.
   */
  async getMe(): Promise<UserProfile> {
    return apiRequest<UserProfile>('/auth/me', {
      method: 'GET',
    });
  },
};
