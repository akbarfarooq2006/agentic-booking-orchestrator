# 🔐 Auth Module — Agentic Booking Orchestrator

Complete authentication and authorization layer for the hackathon project.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                        React Native (Expo)                          │
│  ┌────────────┐  ┌──────────────┐  ┌─────────┐  ┌──────────────┐   │
│  │ AuthProvider│→ │ authService  │→ │ useAuth │  │ SecureStore   │   │
│  │ (Context)   │  │ (API Client) │  │ (Hook)  │  │ (storage.ts) │   │
│  └─────┬──────┘  └──────┬───────┘  └─────────┘  └──────────────┘   │
│        │                │  HTTP + Bearer Token                      │
└────────┼────────────────┼───────────────────────────────────────────┘
         │                │
         ▼                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                                  │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────┐                │
│  │ auth_routes │→ │ dependencies │→ │ jwt_handler  │                │
│  │ (Endpoints) │  │ (Guards)     │  │ (JWT verify) │                │
│  └─────┬──────┘  └──────────────┘  └──────────────┘                │
│        │         ┌──────────────┐  ┌──────────────┐                │
│        ├────────→│ roles.py     │  │ middleware   │                │
│        │         │ (RBAC)       │  │ (CORS/Logs)  │                │
│        ▼         └──────────────┘  └──────────────┘                │
│  ┌────────────┐                                                     │
│  │ Supabase   │ ← supabase_client.py                               │
│  │ Client     │                                                     │
│  └─────┬──────┘                                                     │
└────────┼────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────┐
│   Supabase Auth  │
│   (Cloud/Self)   │
│   + PostgreSQL   │
└──────────────────┘
```

---

## File Structure

### Backend (`backened/app/auth/`)

| File | Purpose |
|------|---------|
| `__init__.py` | Package init — exports `auth_router` |
| `config.py` | Environment variable loading (Supabase URL, JWT secret) |
| `auth_routes.py` | Route handlers: signup, login, logout, me |
| `dependencies.py` | FastAPI deps: `get_current_user`, `require_role` |
| `jwt_handler.py` | JWT create / decode / verify functions |
| `roles.py` | `UserRole` enum, role hierarchy, permission checks |
| `schemas.py` | Pydantic request/response models |
| `supabase_client.py` | Supabase Python client singleton |
| `middleware.py` | CORS config + auth request logging |
| `auth_utils.py` | Shared helpers (token extraction, password validation) |

### Frontend (`mobile/auth/`)

| File | Purpose |
|------|---------|
| `index.ts` | Barrel exports for clean imports |
| `storage.ts` | Expo SecureStore wrapper for token persistence |
| `authService.ts` | HTTP client for auth API endpoints |
| `AuthProvider.tsx` | React Context managing global auth state |
| `useAuth.ts` | Hook for components to access auth state/actions |

---

## API Contracts

### `POST /auth/signup`

Create a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "role": "user"
}
```

**Response (201):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "v1.refresh_token_here...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "email": "user@example.com",
    "role": "user",
    "created_at": "2026-05-19T12:00:00.000000"
  }
}
```

**Errors:**
| Status | Detail |
|--------|--------|
| 400 | `"Signup failed: User already registered"` |
| 422 | Validation error (missing fields, short password) |

---

### `POST /auth/login`

Authenticate with email and password.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "v1.refresh_token_here...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "email": "user@example.com",
    "role": "user",
    "created_at": "2026-05-19T12:00:00.000000"
  }
}
```

**Errors:**
| Status | Detail |
|--------|--------|
| 401 | `"Invalid email or password."` |

---

### `POST /auth/logout`

End the current session. **Requires `Authorization: Bearer <token>`.**

**Request:** No body needed.

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Response (200):**
```json
{
  "message": "User user@example.com logged out successfully.",
  "success": true
}
```

**Errors:**
| Status | Detail |
|--------|--------|
| 401 | `"Could not validate credentials"` |
| 403 | `"Not authenticated"` |

---

### `GET /auth/me`

Get the current user's profile. **Requires `Authorization: Bearer <token>`.**

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Response (200):**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "email": "user@example.com",
  "role": "user",
  "created_at": null
}
```

**Errors:**
| Status | Detail |
|--------|--------|
| 401 | `"Token has expired"` or `"Could not validate credentials"` |

---

## Protected Route Usage (For Teammates)

### Any authenticated user:
```python
from app.auth.dependencies import get_current_user
from app.auth.schemas import UserProfile

@router.get("/bookings")
def list_bookings(user: UserProfile = Depends(get_current_user)):
    return {"user_id": user.id, "bookings": []}
```

### Minimum role required:
```python
from app.auth.dependencies import require_role
from app.auth.roles import UserRole

@router.delete("/admin/users/{user_id}")
def delete_user(
    user_id: str,
    admin: UserProfile = Depends(require_role(UserRole.ADMIN))
):
    return {"deleted": user_id}
```

### Specific roles allowed:
```python
from app.auth.roles import UserRole, is_role_allowed

@router.post("/provider/services")
def create_service(
    user: UserProfile = Depends(get_current_user)
):
    if not is_role_allowed(user.role, [UserRole.PROVIDER, UserRole.ADMIN]):
        raise HTTPException(status_code=403, detail="Providers only")
    return {"status": "created"}
```

---

## RBAC Role Hierarchy

```
admin (level 2)  — Full system access
  ↑
provider (level 1) — Service management + user access
  ↑
user (level 0)     — Basic booking access (default)
```

- `require_role(UserRole.PROVIDER)` allows providers AND admins.
- `require_role(UserRole.ADMIN)` allows admins only.
- `is_role_allowed(role, [UserRole.USER])` allows ONLY users.

---

## Environment Setup

1. Copy the template:
   ```bash
   cp backened/.env.example backened/.env
   ```

2. Fill in your Supabase credentials (from [Supabase Dashboard](https://supabase.com/dashboard) → Settings → API):
   ```env
   SUPABASE_URL=https://xxxx.supabase.co
   SUPABASE_ANON_KEY=eyJhbGciOi...
   SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOi...
   JWT_SECRET=your-jwt-secret-from-supabase
   ```

3. **Without Supabase credentials:** The auth system runs in **mock mode** — signup/login succeed with fake data. This lets the frontend team develop without waiting for Supabase setup.

---

## Dependencies

### Backend (Python)
```
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.0.0
pydantic[email]
python-jose[cryptography]>=3.3.0  # OR PyJWT>=2.8.0
supabase>=2.0.0
python-dotenv>=1.0.0
```

### Frontend (npm)
```
expo-secure-store
```

Install:
```bash
# Backend
cd backened
pip install fastapi uvicorn pydantic[email] PyJWT supabase python-dotenv

# Frontend
cd mobile
npx expo install expo-secure-store
```

---

## Running the Backend

```bash
cd backened
uvicorn app.main:app --reload --port 8000
```

Then open: http://localhost:8000/docs (Swagger UI)

---

## Security Best Practices

### JWT Handling
- Tokens signed with HS256 + secret from env vars (never hardcoded).
- Default expiry: 60 minutes (configurable via `JWT_EXPIRATION_MINUTES`).
- Tokens are stateless; revocation relies on short TTL + client-side deletion.

### Token Storage (Mobile)
- ✅ **Expo SecureStore** — encrypted via device Keychain/Keystore.
- ❌ **NEVER** use `AsyncStorage`, `localStorage`, or plain files for tokens.

### Environment Variables
- `.env` is in `.gitignore` — never committed.
- Only `.env.example` (with empty values) goes to version control.
- Real secrets are added manually by each developer.

### CORS
- Development: `allow_origins=["*"]` for hackathon speed.
- Production: Restrict to your actual domain(s).

### RBAC
- Roles stored in Supabase `user_metadata` during signup.
- JWT payload includes `role` claim for server-side checks.
- Use `require_role()` dependency — never check roles manually in route logic.

---

## Testing Strategy

### 1. Postman / cURL Testing

**Signup:**
```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123", "role": "user"}'
```

**Login:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123"}'
```

**Get Profile (Protected):**
```bash
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer <access_token_from_login>"
```

**Logout (Protected):**
```bash
curl -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer <access_token_from_login>"
```

### 2. Invalid Token Testing

```bash
# Expired/invalid token → should return 401
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer invalid_token_here"

# No token → should return 403
curl http://localhost:8000/auth/me

# Malformed header → should return 403
curl http://localhost:8000/auth/me \
  -H "Authorization: NotBearer token"
```

### 3. RBAC Testing

```bash
# Signup as provider
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "provider@test.com", "password": "test123", "role": "provider"}'

# Use provider token on admin-only endpoint → should return 403
```

### 4. Session Persistence Testing (Mobile)

1. Login on the app → token stored in SecureStore.
2. Kill the app completely.
3. Reopen → `AuthProvider` calls `getMe()` with stored token.
4. If valid → user stays logged in (no re-login needed).
5. If expired → user is redirected to login screen.

### 5. Swagger UI Testing

Visit `http://localhost:8000/docs` after starting the server. Click "Authorize" and paste a JWT to test protected endpoints directly in the browser.

---

## Mock Mode

When `SUPABASE_URL` and `SUPABASE_ANON_KEY` are **not set**:

- **Signup** generates a random UUID user with a mock refresh token.
- **Login** accepts any email/password and returns a valid JWT.
- **Logout** succeeds without calling Supabase.
- **GET /me** works normally (JWT verification is still real).

This allows the entire team to develop and test without Supabase credentials.

---

## Integration Guide (For Teammates)

### Backend Team (Agent/Booking Routes)

1. Import the auth dependency:
   ```python
   from app.auth.dependencies import get_current_user
   from app.auth.schemas import UserProfile
   ```

2. Add it to your route:
   ```python
   @router.post("/api/v1/bookings")
   async def create_booking(
       booking_data: BookingRequest,
       user: UserProfile = Depends(get_current_user)
   ):
       # user.id, user.email, user.role are available
       pass
   ```

3. Register your router in `main.py`:
   ```python
   from app.routes.booking import router as booking_router
   app.include_router(booking_router)
   ```

### Frontend Team

1. Wrap your app with `<AuthProvider>`:
   ```tsx
   import { AuthProvider } from './auth';

   export default function App() {
     return (
       <AuthProvider>
         <YourApp />
       </AuthProvider>
     );
   }
   ```

2. Use the `useAuth` hook in any screen:
   ```tsx
   import { useAuth } from './auth';

   function HomeScreen() {
     const { user, isAuthenticated, logout } = useAuth();

     if (!isAuthenticated) return <LoginScreen />;

     return (
       <View>
         <Text>Welcome, {user?.email}!</Text>
         <Button title="Logout" onPress={logout} />
       </View>
     );
   }
   ```

3. Set the API URL in your Expo config:
   ```env
   EXPO_PUBLIC_API_URL=http://192.168.x.x:8000
   ```
