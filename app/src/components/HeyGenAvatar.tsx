import { useState, useEffect, useRef, forwardRef, useImperativeHandle } from 'react';
import StreamingAvatar, { 
  AvatarQuality, 
  StreamingEvents, 
  TaskType,
  VoiceEmotion
} from '@heygen/streaming-avatar';
import '../styles/HeyGenAvatar.css';

interface HeyGenAvatarProps {
  isListening: boolean;
  isSpeaking: boolean;
  onAvatarReady?: () => void;
  onAvatarError?: (error: string) => void;
  onAvatarStartTalking?: () => void;
  onAvatarStopTalking?: () => void;
}

interface AvatarSession {
  streamingAvatar: StreamingAvatar;
  sessionId: string;
  isReady: boolean;
}

// Define the methods that will be exposed via ref
export interface HeyGenAvatarRef {
  speak: (text: string) => Promise<void>;
}

const HeyGenAvatar = forwardRef<HeyGenAvatarRef, HeyGenAvatarProps>(({
  isListening,
  isSpeaking,
  onAvatarReady,
  onAvatarError,
  onAvatarStartTalking,
  onAvatarStopTalking
}, ref) => {
  const [avatarSession, setAvatarSession] = useState<AvatarSession | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<string>('disconnected');
  const [isAvatarTalking, setIsAvatarTalking] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  // Get configuration from environment
  const HEYGEN_API_KEY = import.meta.env.VITE_HEYGEN_API_KEY;
  const HEYGEN_AVATAR_ID = import.meta.env.VITE_HEYGEN_AVATAR_ID;

  useEffect(() => {
    if (HEYGEN_API_KEY && HEYGEN_AVATAR_ID) {
      initializeAvatar();
    } else {
      setError('HeyGen API key or Avatar ID not configured in .env file');
    }

    // Cleanup on unmount
    return () => {
      cleanup();
    };
  }, []);

  // Use isSpeaking prop to avoid unused warning
  useEffect(() => {
    if (isSpeaking !== isAvatarTalking) {
      console.log('Speaking state sync:', { external: isSpeaking, internal: isAvatarTalking });
    }
  }, [isSpeaking, isAvatarTalking]);

  // ✅ NEW: Create session token from API key
  const createSessionToken = async (): Promise<string> => {
    try {
      console.log('🎫 Creating session token with API key...');
      
      const response = await fetch('https://api.heygen.com/v1/streaming.create_token', {
        method: 'POST',
        headers: {
          'x-api-key': HEYGEN_API_KEY,
          'Content-Type': 'application/json'
        }
      });

      console.log('📡 Token creation response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Token creation failed:', response.status, errorText);
        throw new Error(`Failed to create token: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      console.log('✅ Session token created successfully');
      
      return data.token;
    } catch (error) {
      console.error('❌ Error creating session token:', error);
      throw error;
    }
  };

  const initializeAvatar = async () => {
    try {
      setIsLoading(true);
      setError(null);
      setConnectionStatus('connecting');

      // Debug environment variables
      console.log('🔍 DEBUGGING - Environment Check:');
      console.log('- API Key exists:', !!HEYGEN_API_KEY);
      console.log('- API Key length:', HEYGEN_API_KEY?.length);
      console.log('- API Key first 10 chars:', HEYGEN_API_KEY?.substring(0, 10));
      console.log('- Avatar ID exists:', !!HEYGEN_AVATAR_ID);
      console.log('- Avatar ID value:', HEYGEN_AVATAR_ID);

      // ✅ STEP 1: Create session token from API key
      console.log('🎫 Creating session token...');
      const sessionToken = await createSessionToken();
      console.log('✅ Session token obtained');

      // ✅ STEP 2: Create StreamingAvatar with session token (not API key)
      console.log('🚀 Initializing HeyGen Streaming Avatar with session token...');
      const streamingAvatar = new StreamingAvatar({
        token: sessionToken  // Use session token, not API key!
      });

      console.log('✅ StreamingAvatar instance created');

      // Set up event handlers BEFORE creating session
      setupAvatarEvents(streamingAvatar);

      console.log('📝 Creating avatar session with config:', {
        quality: AvatarQuality.High,
        avatarName: HEYGEN_AVATAR_ID,
        voice: {
          voiceId: 'ff8c5120ac8b4b86bf00bcf896cd8bdd',
          rate: 1.0,
          emotion: VoiceEmotion.FRIENDLY
        },
        language: 'en'
      });

      // ✅ STEP 3: Create avatar session
      const sessionInfo = await streamingAvatar.createStartAvatar({
        quality: AvatarQuality.High,
        avatarName: HEYGEN_AVATAR_ID,
        voice: {
          voiceId: 'ff8c5120ac8b4b86bf00bcf896cd8bdd',
          rate: 1.0,
          emotion: VoiceEmotion.FRIENDLY
        },
        language: 'en'
      });

      console.log('✅ Avatar session created:', sessionInfo.session_id);

      // ✅ STEP 4: Set avatar session state
      setAvatarSession({
        streamingAvatar,
        sessionId: sessionInfo.session_id,
        isReady: true
      });

      setConnectionStatus('connected');
      setIsLoading(false);

      // ✅ STEP 5: Notify parent component
      if (onAvatarReady) {
        onAvatarReady();
      }

      console.log('🎉 Avatar ready for interaction!');

    } catch (err) {
      console.error('❌ Avatar initialization failed - DETAILED ERROR:');
      console.error('- Error type:', typeof err);
      console.error('- Error message:', err instanceof Error ? err.message : 'Unknown error');
      console.error('- Full error object:', err);
      
      // Check if it's a fetch/API error
      if (err && typeof err === 'object' && 'response' in err) {
        console.error('- API Response Status:', (err as any).response?.status);
        console.error('- API Response Data:', (err as any).response?.data);
      }
      
      const errorMessage = err instanceof Error ? err.message : 'Failed to initialize avatar';
      setError(errorMessage);
      setIsLoading(false);
      setConnectionStatus('error');
      
      if (onAvatarError) {
        onAvatarError(errorMessage);
      }
    }
  };

  const setupAvatarEvents = (streamingAvatar: StreamingAvatar) => {
    console.log('📡 Setting up avatar events...');

    // Stream ready event - when video stream is available
    streamingAvatar.on(StreamingEvents.STREAM_READY, (event) => {
      console.log('🎥 Stream ready event received');
      if (event && event.detail && videoRef.current) {
        const stream = event.detail;
        videoRef.current.srcObject = stream;
        videoRef.current.play().catch(console.error);
      }
    });

    // Avatar start talking event
    streamingAvatar.on(StreamingEvents.AVATAR_START_TALKING, () => {
      console.log('🗣️ Avatar started talking');
      setIsAvatarTalking(true);
      if (onAvatarStartTalking) {
        onAvatarStartTalking();
      }
    });

    // Avatar stop talking event
    streamingAvatar.on(StreamingEvents.AVATAR_STOP_TALKING, () => {
      console.log('🤐 Avatar stopped talking');
      setIsAvatarTalking(false);
      if (onAvatarStopTalking) {
        onAvatarStopTalking();
      }
    });

    // Stream disconnected event
    streamingAvatar.on(StreamingEvents.STREAM_DISCONNECTED, () => {
      console.log('📡 Stream disconnected');
      setConnectionStatus('disconnected');
      setError('Stream disconnected');
    });

    // User start talking (if voice chat is enabled)
    streamingAvatar.on(StreamingEvents.USER_START, () => {
      console.log('🎤 User started talking');
    });

    // User stop talking (if voice chat is enabled)
    streamingAvatar.on(StreamingEvents.USER_STOP, () => {
      console.log('🎤 User stopped talking');
    });
  };

  const cleanup = async () => {
    try {
      if (avatarSession?.streamingAvatar) {
        console.log('🧹 Cleaning up avatar session...');
        await avatarSession.streamingAvatar.stopAvatar();
      }

      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
    } catch (err) {
      console.error('Error during cleanup:', err);
    }
  };

  // Method to make avatar speak (will be used by parent component)
  const speak = async (text: string) => {
    if (avatarSession?.streamingAvatar && avatarSession.isReady && text.trim()) {
      try {
        console.log('💬 Avatar speaking:', text);
        await avatarSession.streamingAvatar.speak({
          text: text,
          task_type: TaskType.REPEAT // Use REPEAT to just say the text
        });
      } catch (err) {
        console.error('Error making avatar speak:', err);
        setError('Failed to make avatar speak');
      }
    } else {
      console.warn('Avatar not ready or empty text provided');
    }
  };

  // Test function for Day 1 testing
  const testAvatarSpeech = () => {
    const testText = "Hello! I'm your Oprina voice assistant. I'm ready to help you with your emails and calendar. This is a test of my speech capabilities with perfect lip synchronization.";
    speak(testText);
  };

  // Expose speak method to parent component via ref
  useImperativeHandle(ref, () => ({
    speak
  }));

  return (
    <div className={`heygen-avatar ${isListening ? 'listening' : ''} ${isAvatarTalking ? 'speaking' : ''}`}>
      {/* Connection Status Header */}
      <div className="avatar-header">
        <div className={`connection-status ${connectionStatus}`}>
          <div className={`status-dot ${connectionStatus}`}></div>
          <span className="status-text">
            {connectionStatus === 'connecting' && 'Connecting to avatar...'}
            {connectionStatus === 'connected' && 'Avatar ready'}
            {connectionStatus === 'error' && 'Connection failed'}
            {connectionStatus === 'disconnected' && 'Disconnected'}
          </span>
        </div>
        
        {/* Test Button for Day 1 testing */}
        {avatarSession?.isReady && (
          <button 
            className="test-speech-button"
            onClick={testAvatarSpeech}
            title="Test avatar speech"
            disabled={isAvatarTalking}
          >
            {isAvatarTalking ? '🗣️ Speaking...' : '🧪 Test Speech'}
          </button>
        )}
      </div>

      {/* Main Avatar Video Container */}
      <div className="avatar-container">
        {/* Loading State */}
        {isLoading && (
          <div className="loading-overlay">
            <div className="spinner"></div>
            <p>Initializing avatar...</p>
            <small>Creating session token and WebRTC connection...</small>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="error-overlay">
            <div className="error-content">
              <h3>Avatar Error</h3>
              <p>{error}</p>
              <button onClick={initializeAvatar} className="retry-button">
                Retry Connection
              </button>
            </div>
          </div>
        )}

        {/* Avatar Video Stream */}
        <video
          ref={videoRef}
          className="avatar-video"
          autoPlay
          playsInline
          muted={false}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            borderRadius: '1rem',
            background: '#f5f5f5'
          }}
        />

        {/* Listening Animation Rings */}
        {isListening && avatarSession?.isReady && (
          <div className="listening-rings">
            <div className="ring ring-1"></div>
            <div className="ring ring-2"></div>
            <div className="ring ring-3"></div>
          </div>
        )}

        {/* Speaking Indicator */}
        {isAvatarTalking && (
          <div className="speaking-indicator">
            <div className="sound-waves">
              <div className="wave"></div>
              <div className="wave"></div>
              <div className="wave"></div>
            </div>
            <span>Speaking...</span>
          </div>
        )}

        {/* Avatar Status Indicator */}
        {avatarSession?.isReady && !isLoading && !error && (
          <div className="avatar-ready-indicator">
            <span className="ready-icon">✓</span>
          </div>
        )}
      </div>

      {/* Bottom Status Display */}
      <div className="avatar-status">
        <div className={`status-indicator ${isListening ? 'listening' : isAvatarTalking ? 'speaking' : 'idle'}`}>
          {isListening 
            ? '🎤 Listening' 
            : isAvatarTalking 
            ? '🗣️ Speaking' 
            : avatarSession?.isReady 
            ? '😊 Ready' 
            : '⏳ Loading'
          }
        </div>
      </div>

      {/* Debug Info (development only) */}
      {process.env.NODE_ENV === 'development' && avatarSession && (
        <div className="debug-info">
          <small>Session: {avatarSession.sessionId}</small>
          <br />
          <small>Status: {connectionStatus}</small>
          <br />
          <small>Talking: {isAvatarTalking ? 'Yes' : 'No'}</small>
        </div>
      )}
    </div>
  );
});

export default HeyGenAvatar;