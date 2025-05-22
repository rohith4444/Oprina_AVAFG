import React, { useState, useEffect } from 'react';
import { Mic, MicOff, Volume2, VolumeX } from 'lucide-react';

interface AvatarContainerProps {
  onMicToggle: (isActive: boolean) => void;
  onSpeakerToggle: (isActive: boolean) => void;
}

const AvatarContainer: React.FC<AvatarContainerProps> = ({ 
  onMicToggle,
  onSpeakerToggle 
}) => {
  const [micActive, setMicActive] = useState(false);
  const [speakerActive, setSpeakerActive] = useState(true);
  const [animationState, setAnimationState] = useState('idle');

  const toggleMic = () => {
    const newState = !micActive;
    setMicActive(newState);
    onMicToggle(newState);
    
    if (newState) {
      setAnimationState('listening');
    } else {
      setAnimationState('idle');
    }
  };

  const toggleSpeaker = () => {
    const newState = !speakerActive;
    setSpeakerActive(newState);
    onSpeakerToggle(newState);
  };

  // Simulated avatar animation
  useEffect(() => {
    let timeoutId: number;
    
    if (animationState === 'listening') {
      // Simulate processing after a few seconds of listening
      timeoutId = window.setTimeout(() => {
        setAnimationState('processing');
        
        // Simulate response after processing
        const responseTimeoutId = window.setTimeout(() => {
          setAnimationState('speaking');
          
          // Return to idle state after speaking
          const idleTimeoutId = window.setTimeout(() => {
            setAnimationState('idle');
            setMicActive(false);
            onMicToggle(false);
          }, 3000);
          
          return () => clearTimeout(idleTimeoutId);
        }, 1500);
        
        return () => clearTimeout(responseTimeoutId);
      }, 2000);
    }
    
    return () => clearTimeout(timeoutId);
  }, [animationState, onMicToggle]);

  return (
    <div className="relative w-full h-full rounded-lg bg-gray-50 overflow-hidden">
      <div className="absolute inset-0 flex items-center justify-center">
        {/* Placeholder for the avatar - in a real app, this would be a 3D model or animation */}
        <div className={`w-48 h-48 rounded-full bg-gradient-to-r from-[#5B7CFF] via-[#4FD1C5] to-[#4ADE80] flex items-center justify-center transition-all duration-300 ${
          animationState === 'idle' ? 'scale-90' : 
          animationState === 'listening' ? 'scale-100 animate-pulse' : 
          animationState === 'processing' ? 'scale-95' : 
          'scale-100'
        }`}>
          <div className="w-40 h-40 rounded-full bg-white flex items-center justify-center">
            <div className="text-4xl font-bold bg-gradient-to-r from-[#5B7CFF] via-[#4FD1C5] to-[#4ADE80] text-transparent bg-clip-text">
              Oprina
            </div>
          </div>
        </div>
      </div>
      
      {/* Voice visualization waves */}
      {(animationState === 'listening' || animationState === 'speaking') && (
        <div className="absolute bottom-0 left-0 w-full h-16 flex items-center justify-center space-x-1">
          {[...Array(12)].map((_, index) => (
            <div 
              key={index}
              className="bg-gradient-to-t from-[#5B7CFF] to-[#4ADE80] w-1.5 rounded-full"
              style={{
                height: `${Math.random() * 50 + 10}%`,
                animation: `waveAnimation ${Math.random() * 0.8 + 0.6}s infinite alternate`
              }}
            />
          ))}
        </div>
      )}
      
      {/* Controls */}
      <div className="absolute bottom-4 right-4 flex space-x-4">
        <button 
          onClick={toggleMic}
          className={`w-12 h-12 rounded-full flex items-center justify-center ${
            micActive ? 'bg-red-500 text-white' : 'bg-black text-white'
          } transition-colors`}
        >
          {micActive ? <MicOff size={20} /> : <Mic size={20} />}
        </button>
        
        <button 
          onClick={toggleSpeaker}
          className={`w-12 h-12 rounded-full flex items-center justify-center ${
            speakerActive ? 'bg-black text-white' : 'bg-gray-300 text-gray-700'
          } transition-colors`}
        >
          {speakerActive ? <Volume2 size={20} /> : <VolumeX size={20} />}
        </button>
      </div>
      
      {/* Status indicator */}
      <div className="absolute top-4 left-4 flex items-center">
        <div className={`w-3 h-3 rounded-full mr-2 ${
          animationState === 'idle' ? 'bg-gray-400' : 
          animationState === 'listening' ? 'bg-red-500 animate-pulse' : 
          animationState === 'processing' ? 'bg-yellow-500' : 
          'bg-green-500'
        }`} />
        <span className="text-sm text-gray-600">
          {animationState === 'idle' ? 'Ready' : 
           animationState === 'listening' ? 'Listening...' : 
           animationState === 'processing' ? 'Processing...' : 
           'Speaking...'}
        </span>
      </div>
      
      <style jsx>{`
        @keyframes waveAnimation {
          0% { height: 10%; }
          100% { height: 80%; }
        }
      `}</style>
    </div>
  );
};

export default AvatarContainer;