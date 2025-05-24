import React from 'react';

interface LogoProps {
  className?: string;
  size?: number;
}

const Logo: React.FC<LogoProps> = ({ className = '', size = 40 }) => {
  return (
    <div className={`logo ${className}`} style={{ width: size, height: size }}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 40 40"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#5B7CFF" />
            <stop offset="50%" stopColor="#4FD1C5" />
            <stop offset="100%" stopColor="#4ADE80" />
          </linearGradient>
        </defs>
        <path
          d="M20 2C10.059 2 2 10.059 2 20C2 29.941 10.059 38 20 38C29.941 38 38 29.941 38 20C38 10.059 29.941 2 20 2ZM20 32C13.373 32 8 26.627 8 20C8 13.373 13.373 8 20 8C26.627 8 32 13.373 32 20C32 26.627 26.627 32 20 32Z"
          fill="url(#gradient)"
        />
        <path
          d="M32 20C32 13.373 26.627 8 20 8V2C29.941 2 38 10.059 38 20H32Z"
          fill="url(#gradient)"
        />
      </svg>
    </div>
  );
};

export default Logo;