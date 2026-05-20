/**
 * AuthProvider — React Context that manages global authentication state.
 *
 * Wraps the entire app to provide:
 *   - Current user state (user, isAuthenticated, isLoading)
 *   - Auth actions (login, signup, logout)
 *   - Automatic session restoration on app startup
 *
 * Usage in App.tsx:
 *   import { AuthProvider } from './auth/AuthProvider';
 *
 *   export default function App() {
 *     return (
 *       <AuthProvider>
 *         <NavigationContainer>
 *           <RootNavigator />
 *         </NavigationContainer>
 *       </AuthProvider>
 *     );
 *   }
 *
 * Usage in screens:
 *   import { useAuth } from './auth/useAuth';
 *
 *   function ProfileScreen() {
 *     const { user, logout } = useAuth();
 *     return <Text>{user?.email}</Text>;
 *   }
 */

import React, { createContext, useState, useEffect, useCallback } from 'react';
import { authService, UserProfile, AuthResponse } from './authService';
import {
  saveTokens,
  clearTokens,
  getAccessToken,
  saveUserProfile,
  getUserProfile,
} from './storage';

// ---------------------------------------------------------------------------
// Context Type Definition
// ---------------------------------------------------------------------------

export interface AuthContextType {
  /** The currently authenticated user, or null if not logged in. */
  user: UserProfile | null;

  /** True while the initial session restoration is in progress. */
  isLoading: boolean;

  /** Convenience boolean: true if user is authenticated. */
  isAuthenticated: boolean;

  /** Sign up a new user. Stores tokens and updates state on success. */
  signup: (
    email: string,
    password: string,
    role?: 'user' | 'provider' | 'admin'
  ) => Promise<void>;

  /** Log in an existing user. Stores tokens and updates state on success. */
  login: (email: string, password: string) => Promise<void>;

  /** Log out the current user. Clears tokens and resets state. */
  logout: () => Promise<void>;
}

// ---------------------------------------------------------------------------
// Context Creation
// ---------------------------------------------------------------------------

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

// ---------------------------------------------------------------------------
// Provider Component
// ---------------------------------------------------------------------------

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // ---- Session Restoration (runs once on app mount) ----
  useEffect(() => {
    restoreSession();
  }, []);

  /**
   * Attempt to restore the user session from secure storage.
   *
   * Flow:
   * 1. Check if an access token exists in SecureStore.
   * 2. If yes, call GET /auth/me to validate it.
   * 3. If valid, set user state. If expired/invalid, clear stored tokens.
   * 4. If no token, show cached profile briefly while loading.
   */
  async function restoreSession(): Promise<void> {
    try {
      const token = await getAccessToken();

      if (!token) {
        // No token stored — user is not logged in
        setIsLoading(false);
        return;
      }

      // Show cached profile instantly (avoids blank screen flicker)
      const cachedProfile = await getUserProfile();
      if (cachedProfile) {
        setUser(cachedProfile as UserProfile);
      }

      // Validate token with the backend
      const profile = await authService.getMe();
      setUser(profile);
      await saveUserProfile(profile);
    } catch (error) {
      // Token is invalid or expired — clean up
      console.warn('Session restoration failed:', error);
      await clearTokens();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }

  // ---- Auth Actions ----

  /**
   * Handle the response from signup or login:
   * store tokens and update user state.
   */
  async function handleAuthResponse(response: AuthResponse): Promise<void> {
    await saveTokens(response.access_token, response.refresh_token);
    await saveUserProfile(response.user);
    setUser(response.user);
  }

  const signup = useCallback(
    async (
      email: string,
      password: string,
      role: 'user' | 'provider' | 'admin' = 'user'
    ): Promise<void> => {
      const response = await authService.signup(email, password, role);
      await handleAuthResponse(response);
    },
    []
  );

  const login = useCallback(
    async (email: string, password: string): Promise<void> => {
      const response = await authService.login(email, password);
      await handleAuthResponse(response);
    },
    []
  );

  const logout = useCallback(async (): Promise<void> => {
    try {
      await authService.logout();
    } catch (error) {
      // Even if server-side logout fails, clear local state
      console.warn('Server logout failed (clearing local state):', error);
    } finally {
      await clearTokens();
      setUser(null);
    }
  }, []);

  // ---- Context Value ----

  const contextValue: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    signup,
    login,
    logout,
  };

  return (
    <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>
  );
}
