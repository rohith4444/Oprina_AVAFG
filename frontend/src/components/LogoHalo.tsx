import React from 'react';

interface LogoHaloProps {
  className?: string;
  size?: number;
}

const LogoHalo: React.FC<LogoHaloProps> = ({ className = '', size = 40 }) => {
  // Parameters for the ring and elements
  const center = size / 2;
  const radius = size * 0.4;
  const stroke = size * 0.11;
  const dotRadius = size * 0.13;
  // Angular wedge cut (flat, not rounded)
  const cutAngle = Math.PI / 10; // ~18 degrees
  const startAngle = -Math.PI / 4; // Top right
  const endAngle = 2 * Math.PI - cutAngle + startAngle;
  // Wedge width
  const wedgeWidth = size * 0.13;

  // Helper to get (x, y) from angle and radius
  const polar = (r: number, angle: number) => [center + r * Math.cos(angle), center + r * Math.sin(angle)];

  // Main ring path (from after wedge to before wedge)
  const [arcStartX, arcStartY] = polar(radius, startAngle + cutAngle);
  const [arcEndX, arcEndY] = polar(radius, endAngle);
  const largeArc = endAngle - (startAngle + cutAngle) > Math.PI ? 1 : 0;

  // Wedge (angular cut) points
  const [wedgeOuter1X, wedgeOuter1Y] = polar(radius, startAngle);
  const [wedgeOuter2X, wedgeOuter2Y] = polar(radius, startAngle + cutAngle);
  const [wedgeInner1X, wedgeInner1Y] = polar(radius - stroke, startAngle);
  const [wedgeInner2X, wedgeInner2Y] = polar(radius - stroke, startAngle + cutAngle);

  return (
    <div className={`logo ${className}`} style={{ width: size, height: size }}>
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient id="halo-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#3B82F6" />
            <stop offset="100%" stopColor="#10B981" />
          </linearGradient>
          <radialGradient id="dot-gradient" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#2563EB" />
            <stop offset="100%" stopColor="#059669" />
          </radialGradient>
        </defs>
        {/* Main ring with flat angular wedge cut */}
        <path
          d={`M ${arcStartX} ${arcStartY}
              A ${radius} ${radius} 0 ${largeArc} 1 ${arcEndX} ${arcEndY}`}
          stroke="url(#halo-gradient)"
          strokeWidth={stroke}
          strokeLinecap="butt"
          fill="none"
        />
        {/* Flat wedge cut (angular, not rounded) */}
        <polygon
          points={`
            ${wedgeOuter1X},${wedgeOuter1Y}
            ${wedgeOuter2X},${wedgeOuter2Y}
            ${wedgeInner2X},${wedgeInner2Y}
            ${wedgeInner1X},${wedgeInner1Y}
          `}
          fill="url(#halo-gradient)"
        />
        {/* Centered inner dot */}
        <circle cx={center} cy={center} r={dotRadius} fill="url(#dot-gradient)" />
      </svg>
    </div>
  );
};

export default LogoHalo; 