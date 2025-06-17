import React, { useState } from 'react';
import { Mic, MicOff, Volume2, Volume1, VolumeX } from 'lucide-react';
import '../styles/VoiceControls.css';

interface VoiceControlsProps {
  onStartListening: () => void;
  onStopListening: () => void;
  onToggleMute: () => void;
  isMuted: boolean;
  isListening: boolean;
}

const VoiceControls: React.FC<VoiceControlsProps> = ({
  onStartListening,
  onStopListening,
  onToggleMute,
  isMuted,
  isListening,
}) => {
  const [volume, setVolume] = useState(75);
  
  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newVolume = parseInt(e.target.value);
    setVolume(newVolume);
    // Additional logic to adjust actual volume would go here
  };
  
  return (
    <div className="voice-controls">
      <button 
        className={`voice-button ${isListening ? 'active' : ''}`}
        onClick={isListening ? onStopListening : onStartListening}
        aria-label={isListening ? 'Stop listening' : 'Start listening'}
      >
        {isListening ? <MicOff size={24} /> : <Mic size={24} />}
      </button>
      
      <div className="volume-control">
        <button 
          className={`voice-button ${isMuted ? 'muted' : ''}`}
          onClick={onToggleMute}
          aria-label={isMuted ? 'Unmute' : 'Mute'}
        >
          {isMuted ? (
            <VolumeX size={24} />
          ) : volume < 50 ? (
            <Volume1 size={24} />
          ) : (
            <Volume2 size={24} />
          )}
        </button>
        
        <input
          type="range"
          min="0"
          max="100"
          value={volume}
          onChange={handleVolumeChange}
          className="volume-slider"
          disabled={isMuted}
        />
      </div>
      
      <div className="voice-visualizer">
        {isListening && (
          <>
            <div className="bar"></div>
            <div className="bar"></div>
            <div className="bar"></div>
            <div className="bar"></div>
            <div className="bar"></div>
          </>
        )}
      </div>
    </div>
  );
};

export default VoiceControls;