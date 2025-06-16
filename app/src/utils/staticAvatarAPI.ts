// src/utils/staticAvatarAPI.ts
interface AvatarData {
  avatar_id: string;
  avatar_name: string;
  gender: string;
  preview_image_url: string;
  preview_video_url: string;
  premium?: boolean;
}

interface HeyGenAvatarsResponse {
  error: string | null;
  data: {
    avatars: AvatarData[];
    talking_photos: any[];
  };
}

class StaticAvatarAPI {
  private cache: Map<string, AvatarData> = new Map();
  private avatarsList: AvatarData[] = [];

  constructor() {
    // No need to store API key - we get it from environment when needed
  }

  /**
   * Get API key from environment variables
   */
  private getApiKey(): string {
    const apiKey = import.meta.env.VITE_HEYGEN_API_KEY;
    if (!apiKey) {
      throw new Error('VITE_HEYGEN_API_KEY not found in environment variables');
    }
    return apiKey;
  }

  /**
   * Fetch all available avatars from HeyGen
   */
  async fetchAvatarsList(): Promise<AvatarData[]> {
    try {
      const apiKey = this.getApiKey();
      
      const response = await fetch('https://api.heygen.com/v2/avatars', {
        method: 'GET',
        headers: {
          'X-Api-Key': apiKey,
          'Accept': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HeyGen API error: ${response.status}`);
      }

      const data: HeyGenAvatarsResponse = await response.json();
      
      if (data.error) {
        throw new Error(`HeyGen API error: ${data.error}`);
      }

      this.avatarsList = data.data.avatars;
      
      // Cache all avatars for quick lookup
      this.avatarsList.forEach(avatar => {
        this.cache.set(avatar.avatar_id, avatar);
      });

      console.log('✅ Fetched', this.avatarsList.length, 'avatars from HeyGen');
      return this.avatarsList;
    } catch (error) {
      console.error('❌ Error fetching avatars list:', error);
      throw error;
    }
  }

  /**
   * Get specific avatar by ID
   */
  async getAvatarById(avatarId: string): Promise<AvatarData | null> {
    try {
      // Check cache first
      if (this.cache.has(avatarId)) {
        return this.cache.get(avatarId)!;
      }

      // Fetch avatars list if not already loaded
      if (this.avatarsList.length === 0) {
        await this.fetchAvatarsList();
      }

      // Try to find the avatar
      const avatar = this.avatarsList.find(a => a.avatar_id === avatarId);
      
      if (avatar) {
        console.log('✅ Found avatar:', avatarId, '-', avatar.avatar_name);
        return avatar;
      } else {
        console.warn('⚠️ Avatar not found:', avatarId);
        return null;
      }
    } catch (error) {
      console.error('❌ Error getting avatar by ID:', error);
      return null;
    }
  }

  /**
   * Validate avatar availability and get fallback if needed
   */
  async getAvailableAvatar(
    primaryId: string, 
    fallbackId: string = 'Angela-inblackskirt-20220820'
  ): Promise<AvatarData | null> {
    try {
      console.log('🔍 Checking avatar availability...');
      
      // Try primary avatar first
      const primaryAvatar = await this.getAvatarById(primaryId);
      if (primaryAvatar?.preview_image_url) {
        console.log('✅ Using primary avatar:', primaryId);
        return primaryAvatar;
      }

      console.log('⚠️ Primary avatar not available, trying fallback...');
      
      // Try fallback avatar
      const fallbackAvatar = await this.getAvatarById(fallbackId);
      if (fallbackAvatar?.preview_image_url) {
        console.log('✅ Using fallback avatar:', fallbackId);
        return fallbackAvatar;
      }

      console.error('❌ No avatars available');
      return null;
    } catch (error) {
      console.error('❌ Error in getAvailableAvatar:', error);
      return null;
    }
  }

  /**
   * Preload avatar image for faster display
   */
  async preloadAvatarImage(imageUrl: string): Promise<boolean> {
    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => {
        console.log('✅ Avatar image preloaded');
        resolve(true);
      };
      img.onerror = () => {
        console.error('❌ Failed to preload avatar image');
        resolve(false);
      };
      img.src = imageUrl;
    });
  }

  /**
   * Get public avatars only (filter out premium/custom ones)
   */
  getPublicAvatars(): AvatarData[] {
    return this.avatarsList.filter(avatar => !avatar.premium);
  }

  /**
   * Search avatars by name or ID
   */
  searchAvatars(query: string): AvatarData[] {
    const searchTerm = query.toLowerCase();
    return this.avatarsList.filter(avatar => 
      avatar.avatar_name.toLowerCase().includes(searchTerm) ||
      avatar.avatar_id.toLowerCase().includes(searchTerm)
    );
  }
}

// Export singleton instance
let staticAvatarAPI: StaticAvatarAPI | null = null;

export const getStaticAvatarAPI = (): StaticAvatarAPI => {
  if (!staticAvatarAPI) {
    staticAvatarAPI = new StaticAvatarAPI();
  }
  return staticAvatarAPI;
};

export type { AvatarData };
export default StaticAvatarAPI;