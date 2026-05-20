/**
 * Secure Token Storage — Uses Expo SecureStore for sensitive data.
 *
 * Expo SecureStore encrypts values using the device's keychain (iOS)
 * or Keystore (Android). This is the ONLY safe way to store JWTs
 * on a mobile device — never use AsyncStorage for tokens.
 *
 * Usage:
 *   import { saveTokens, getAccessToken, clearTokens } from './storage';
 */

import * as SecureStore from 'expo-secure-store';

// ---------------------------------------------------------------------------
// Storage Keys — Centralized to prevent typos
// ---------------------------------------------------------------------------

const STORAGE_KEYS = {
  ACCESS_TOKEN: 'auth_access_token',
  REFRESH_TOKEN: 'auth_refresh_token',
  USER_PROFILE: 'auth_user_profile',
} as const;

// ---------------------------------------------------------------------------
// Token Operations
// ---------------------------------------------------------------------------

/**
 * Save both access and refresh tokens securely.
 * Called after successful login or signup.
 */
export async function saveTokens(
  accessToken: string,
  refreshToken?: string | null
): Promise<void> {
  await SecureStore.setItemAsync(STORAGE_KEYS.ACCESS_TOKEN, accessToken);

  if (refreshToken) {
    await SecureStore.setItemAsync(STORAGE_KEYS.REFRESH_TOKEN, refreshToken);
  }
}

/**
 * Retrieve the stored access token.
 * Returns null if no token is stored (user is not logged in).
 */
export async function getAccessToken(): Promise<string | null> {
  return await SecureStore.getItemAsync(STORAGE_KEYS.ACCESS_TOKEN);
}

/**
 * Retrieve the stored refresh token.
 */
export async function getRefreshToken(): Promise<string | null> {
  return await SecureStore.getItemAsync(STORAGE_KEYS.REFRESH_TOKEN);
}

/**
 * Delete all stored tokens and user data.
 * Called during logout to ensure no sensitive data remains on device.
 */
export async function clearTokens(): Promise<void> {
  await SecureStore.deleteItemAsync(STORAGE_KEYS.ACCESS_TOKEN);
  await SecureStore.deleteItemAsync(STORAGE_KEYS.REFRESH_TOKEN);
  await SecureStore.deleteItemAsync(STORAGE_KEYS.USER_PROFILE);
}

// ---------------------------------------------------------------------------
// User Profile Cache
// ---------------------------------------------------------------------------

/**
 * Cache the user profile locally for instant UI rendering on app restart.
 * This avoids a loading spinner while the /auth/me call completes.
 */
export async function saveUserProfile(profile: object): Promise<void> {
  await SecureStore.setItemAsync(
    STORAGE_KEYS.USER_PROFILE,
    JSON.stringify(profile)
  );
}

/**
 * Retrieve the cached user profile.
 * Returns null if no profile is cached.
 */
export async function getUserProfile(): Promise<object | null> {
  const data = await SecureStore.getItemAsync(STORAGE_KEYS.USER_PROFILE);
  if (!data) return null;

  try {
    return JSON.parse(data);
  } catch {
    return null;
  }
}
