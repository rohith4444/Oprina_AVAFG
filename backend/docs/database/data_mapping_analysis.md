# Supabase ↔ Backend Data Mapping Analysis

## User Data Mapping

### Supabase Auth Tables
- **auth.users**: Supabase's built-in user authentication
  - `id`: Supabase user UUID 
  - `email`: User email address
  - `created_at`: Account creation timestamp
  - `email_confirmed_at`: Email verification timestamp

### Backend Custom Tables  
- **public.users**: Your application user data
  - `id`: Same UUID as auth.users.id (mapped 1:1)
  - `email`: Duplicated from auth.users
  - `gmail_tokens`: OAuth tokens for Gmail (encrypted)
  - `calendar_tokens`: OAuth tokens for Calendar (encrypted)
  - `full_name`, `preferred_name`: Profile data
  - `created_at`, `updated_at`: Timestamps

## Data Ownership Strategy

| Data Type | Primary Owner | Secondary | Notes |
|-----------|---------------|-----------|-------|
| Authentication | `auth.users` | None | Supabase handles auth |
| User Profile | `public.users` | None | Your app manages profiles |
| OAuth Tokens | `public.users` | None | Your app stores encrypted tokens |
| Session Data | `public.sessions` | None | Your app manages conversations |
| Messages | `public.messages` | None | Your app stores chat history |

## Sync Rules

1. **User Creation**: When Supabase user created → Auto-create in public.users
2. **Profile Updates**: Frontend updates public.users directly  
3. **Authentication**: Always validate via Supabase tokens
4. **OAuth Tokens**: Store only in public.users (encrypted)

## Migration Status
- ✅ No migration needed - using UUIDs consistently
- ✅ Supabase user ID = Backend user ID (same field)
- ✅ Email sync working via user sync service