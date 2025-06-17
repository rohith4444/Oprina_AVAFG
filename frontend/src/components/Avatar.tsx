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
    
    canvas.width = 300;
    canvas.height = 300;
    
    let animationFrame: number;
    
    const drawAvatar = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      // Draw placeholder human avatar
      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;
      
      // Head
      ctx.beginPath();
      ctx.arc(centerX, centerY - 30, 60, 0, Math.PI * 2);
      ctx.fillStyle = '#E2E8F0';
      ctx.fill();
      ctx.strokeStyle = '#5B7CFF';
      ctx.lineWidth = 3;
      ctx.stroke();
      
      // Body
      ctx.beginPath();
      ctx.moveTo(centerX - 40, centerY + 30);
      ctx.quadraticCurveTo(centerX, centerY + 120, centerX + 40, centerY + 30);
      ctx.fillStyle = '#E2E8F0';
      ctx.fill();
      ctx.strokeStyle = '#5B7CFF';
      ctx.stroke();
      
      // Face features
      if (isSpeaking) {
        // Animated mouth when speaking
        ctx.beginPath();
        ctx.ellipse(centerX, centerY + 10, 20, 10 + Math.sin(Date.now() / 200) * 5, 0, 0, Math.PI * 2);
        ctx.stroke();
      } else {
        // Regular smile
        ctx.beginPath();
        ctx.arc(centerX, centerY, 30, 0.1 * Math.PI, 0.9 * Math.PI);
        ctx.stroke();
      }
      
      // Eyes
      ctx.beginPath();
      ctx.arc(centerX - 20, centerY - 20, 5, 0, Math.PI * 2);
      ctx.arc(centerX + 20, centerY - 20, 5, 0, Math.PI * 2);
      ctx.fillStyle = '#000000';
      ctx.fill();
      
      // Listening animation
      if (isListening) {
        const radius = 80 + Math.sin(Date.now() / 500) * 10;
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(79, 209, 197, ${0.5 + Math.sin(Date.now() / 500) * 0.5})`;
        ctx.lineWidth = 2;
        ctx.stroke();
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
      <canvas ref={canvasRef} className="avatar-canvas" />
    </div>
  );
};

export default Avatar;