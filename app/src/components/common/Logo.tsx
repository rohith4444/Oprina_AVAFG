import React from 'react';

interface LogoProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const Logo: React.FC<LogoProps> = ({ size = 'md', className = '' }) => {
  const sizeStyles = {
    sm: 'w-8 h-8',
    md: 'w-10 h-10',
    lg: 'w-16 h-16',
  };

  return (
    <div className={`relative ${sizeStyles[size]} ${className}`}>
      <div className="absolute inset-0 bg-white rounded-full border-4 border-black"></div>
      <div className="absolute inset-2 bg-black rounded-full"></div>
      <div className="absolute inset-4 bg-white rounded-full"></div>
    </div>
  );
};

export default Logo;