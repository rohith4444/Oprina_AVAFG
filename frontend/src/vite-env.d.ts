/// <reference types="vite/client" />

interface ImportMetaEnv {
  // Backend Connection
  readonly VITE_BACKEND_URL: string

  // NEW: Add this line
  readonly VITE_SITE_URL: string

  // Supabase Configuration
  readonly VITE_SUPABASE_URL: string
  readonly VITE_SUPABASE_ANON_KEY: string

  // HeyGen Avatar Configuration
  readonly VITE_HEYGEN_API_KEY: string
  readonly VITE_HEYGEN_API_URL: string
  readonly VITE_HEYGEN_AVATAR_ID: string

  // Avatar Feature Flags (boolean strings)
  readonly VITE_USE_STATIC_AVATAR: string
  readonly VITE_ENABLE_AVATAR_SELECTOR: string
  readonly VITE_CACHE_AVATAR_IMAGES: string

  // Development/Debug Settings (boolean strings)
  readonly VITE_SHOW_AVATAR_TOGGLE: string
  readonly VITE_DEBUG_AVATAR_API: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}