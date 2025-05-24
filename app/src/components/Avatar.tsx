import React, { useEffect, useRef } from 'react';
import '../styles/Avatar.css';

interface AvatarProps {
  isListening: boolean;
  isSpeaking: boolean;
}

const Avatar: React.FC<AvatarProps> = ({ isListening, isSpeaking }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // Set up dimensions
    canvas.width = 300;
    canvas.height = 300;
    
    // Avatar state variables
    let animationFrame: number;
    let waveRadius = 0;
    
    const drawAvatar = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      // Draw face
      ctx.beginPath();
      ctx.arc(150, 150, 100, 0, Math.PI * 2);
      ctx.fillStyle = '#FFFFFF';
      ctx.fill();
      ctx.strokeStyle = '#5B7CFF';
      ctx.lineWidth = 3;
      ctx.stroke();
      
      // Draw eyes
      ctx.beginPath();
      ctx.arc(120, 130, 10, 0, Math.PI * 2);
      ctx.arc(180, 130, 10, 0, Math.PI * 2);
      ctx.fillStyle = '#000000';
      ctx.fill();
      
      // Draw mouth based on state
      ctx.beginPath();
      if (isSpeaking) {
        // Speaking mouth (oval shape)
        ctx.ellipse(150, 180, 20, 15, 0, 0, Math.PI * 2);
      } else {
        // Normal smile
        ctx.arc(150, 170, 30, 0.1 * Math.PI, 0.9 * Math.PI);
      }
      ctx.lineWidth = 3;
      ctx.stroke();
      
      // Draw sound waves when listening
      if (isListening) {
        waveRadius += 1;
        if (waveRadius > 50) waveRadius = 0;
        
        ctx.beginPath();
        ctx.arc(150, 150, 100 + waveRadius, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(79, 209, 197, ${1 - waveRadius / 50})`;
        ctx.lineWidth = 2;
        ctx.stroke();
        
        if (waveRadius > 25) {
          ctx.beginPath();
          ctx.arc(150, 150, 100 + waveRadius - 25, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(74, 222, 128, ${1 - (waveRadius - 25) / 50})`;
          ctx.lineWidth = 2;
          ctx.stroke();
        }
      }
      
      animationFrame = requestAnimationFrame(drawAvatar);
    };
    
    drawAvatar();
    
    return () => {
      cancelAnimationFrame(animationFrame);
    };
  }, [isListening, isSpeaking]);
  
  return (
    <div className={`avatar ${isListening ? 'listening' : ''} ${isSpeaking ? 'speaking' : ''}`}>
      <canvas ref={canvasRef} className="avatar-canvas"></canvas>
    </div>
  );
};

export default Avatar;