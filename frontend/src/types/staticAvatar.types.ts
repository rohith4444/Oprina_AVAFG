// src/types/staticAvatar.types.ts
export interface AvatarData {
  avatar_id: string;
  avatar_name: string;
  gender: string;
  preview_image_url: string;
  preview_video_url: string;
  premium?: boolean;
}

export interface HeyGenAvatarsResponse {
  error: string | null;
  data: {
    avatars: AvatarData[];
    talking_photos: TalkingPhoto[];
  };
}

export interface TalkingPhoto {
  talking_photo_id: string;
  talking_photo_name: string;
  preview_image_url: string;
}

export interface StreamingAvatarData {
  avatar_id: string;
  created_at: number;
  is_public: boolean;
  status: string;
}

export interface StreamingAvatarsResponse {
  code: number;
  data: StreamingAvatarData[];
  message: string;
}

export interface AvatarConfig {
  useStaticAvatar: boolean;
  primaryAvatarId: string;
  fallbackAvatarId: string;
  enableAvatarSelector: boolean;
  cacheAvatarImages: boolean;
}

export interface AvatarState {
  isReady: boolean;
  isLoading: boolean;
  error: string | null;
  connectionStatus: 'connecting' | 'connected' | 'error' | 'disconnected';
  selectedAvatar: AvatarData | null;
}

// Common interface for both avatar types
export interface AvatarProps {
  isListening: boolean;
  isSpeaking: boolean;
  onAvatarReady?: () => void;
  onAvatarError?: (error: string) => void;
  onAvatarStartTalking?: () => void;
  onAvatarStopTalking?: () => void;
}

// Common interface for avatar refs
export interface AvatarRef {
  speak: (text: string) => Promise<void>;
}