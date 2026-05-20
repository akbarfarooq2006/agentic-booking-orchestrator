/**
 * Auth Module — Public API for the mobile auth layer.
 *
 * Re-exports everything needed by the rest of the app.
 *
 * Usage:
 *   import { AuthProvider, useAuth, authService } from './auth';
 */

// Context and Provider
export { AuthProvider, AuthContext } from './AuthProvider';
export type { AuthContextType } from './AuthProvider';

// Hook
export { useAuth } from './useAuth';

// API Service
export { authService } from './authService';
export type { UserProfile, AuthResponse, MessageResponse, AuthError } from './authService';

// Storage utilities (rarely needed directly, but exported for testing)
export {
  saveTokens,
  getAccessToken,
  getRefreshToken,
  clearTokens,
  saveUserProfile,
  getUserProfile,
} from './storage';
