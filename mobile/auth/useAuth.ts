/**
 * useAuth Hook — Convenient access to the AuthContext.
 *
 * Provides type-safe access to user state and auth actions from any component.
 * Throws a clear error if used outside of <AuthProvider>.
 *
 * Usage:
 *   import { useAuth } from '../auth/useAuth';
 *
 *   function MyScreen() {
 *     const { user, isAuthenticated, login, logout } = useAuth();
 *
 *     if (!isAuthenticated) {
 *       return <LoginScreen />;
 *     }
 *
 *     return <Text>Hello, {user?.email}!</Text>;
 *   }
 */

import { useContext } from 'react';
import { AuthContext, AuthContextType } from './AuthProvider';

/**
 * Access the auth context from any component inside <AuthProvider>.
 *
 * Returns:
 *   - user: The current UserProfile or null.
 *   - isLoading: True during initial session restoration.
 *   - isAuthenticated: True if user is logged in.
 *   - signup(email, password, role?): Create a new account.
 *   - login(email, password): Log in.
 *   - logout(): Log out and clear tokens.
 *
 * Throws:
 *   Error if called outside of <AuthProvider>.
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error(
      'useAuth() must be used within an <AuthProvider>. ' +
        'Wrap your app root with <AuthProvider> in App.tsx.'
    );
  }

  return context;
}
