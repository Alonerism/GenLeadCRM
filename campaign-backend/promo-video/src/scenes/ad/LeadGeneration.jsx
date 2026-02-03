import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from 'remotion';

export const LeadGeneration = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Smooth zoom animation on maps
  const zoomProgress = spring({
    frame,
    fps,
    config: {
      damping: 200,
      stiffness: 100,
    },
  });

  const mapScale = interpolate(zoomProgress, [0, 1], [1, 2.5]);
  const mapOpacity = interpolate(frame, [0, 20], [0, 1]);

  // Pins drop and multiply with delay
  const pins = [...Array(24)].map((_, i) => {
    const startFrame = 40 + i * 3; // Staggered appearance
    const pinSpring = spring({
      frame: frame - startFrame,
      fps,
      config: {
        damping: 200,
        stiffness: 100,
      },
    });

    const y = interpolate(pinSpring, [0, 1], [-100, 0]);
    const opacity = frame >= startFrame ? pinSpring : 0;

    // Grid positions
    const col = i % 6;
    const row = Math.floor(i / 6);
    const x = -400 + col * 160;
    const baseY = -200 + row * 160;

    return { x, y: baseY + y, opacity, scale: pinSpring };
  });

  // Text fade in
  const textOpacity = interpolate(frame, [60, 90], [0, 1], { extrapolateRight: 'clamp' });

  // Particle effects - subtle background
  const particles = [...Array(30)].map((_, i) => {
    const angle = (i / 30) * Math.PI * 2;
    const distance = 300 + (frame * 2 + i * 10) % 500;
    const x = Math.cos(angle) * distance;
    const y = Math.sin(angle) * distance;
    const size = 2 + (i % 3);

    return { x, y, size, opacity: 0.3 };
  });

  return (
    <AbsoluteFill
      style={{
        background: 'radial-gradient(ellipse at center, #1a1f4d 0%, #0a0e27 100%)',
        justifyContent: 'center',
        alignItems: 'center',
        overflow: 'hidden',
      }}
    >
      {/* Subtle particle background */}
      {particles.map((p, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            left: '50%',
            top: '50%',
            transform: `translate(${p.x}px, ${p.y}px)`,
            width: p.size,
            height: p.size,
            borderRadius: '50%',
            background: '#00d4ff',
            opacity: p.opacity,
            boxShadow: '0 0 4px #00d4ff',
          }}
        />
      ))}

      {/* Simulated Google Maps view */}
      <div
        style={{
          position: 'absolute',
          width: 800,
          height: 600,
          transform: `scale(${mapScale})`,
          opacity: mapOpacity,
          background: 'linear-gradient(135deg, #1e2a4a 0%, #0f1729 100%)',
          borderRadius: 20,
          border: '1px solid rgba(0, 212, 255, 0.2)',
          overflow: 'hidden',
        }}
      >
        {/* Grid overlay for map effect */}
        <svg width="100%" height="100%" style={{ position: 'absolute', opacity: 0.1 }}>
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#00d4ff" strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>

        {/* Location pins dropping */}
        {pins.map((pin, i) => (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: '50%',
              top: '50%',
              transform: `translate(${pin.x}px, ${pin.y}px) scale(${pin.scale})`,
              opacity: pin.opacity,
            }}
          >
            {/* Custom pin with glow */}
            <div
              style={{
                width: 16,
                height: 16,
                borderRadius: '50% 50% 50% 0',
                transform: 'rotate(-45deg)',
                background: 'linear-gradient(135deg, #00d4ff 0%, #a855f7 100%)',
                boxShadow: '0 0 10px #00d4ff, 0 0 20px rgba(0, 212, 255, 0.5)',
              }}
            />
          </div>
        ))}
      </div>

      {/* Text overlay */}
      <div
        style={{
          position: 'absolute',
          bottom: 150,
          opacity: textOpacity,
          textAlign: 'center',
        }}
      >
        <div
          style={{
            fontSize: 72,
            fontWeight: 600,
            background: 'linear-gradient(90deg, #00d4ff 0%, #a855f7 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            fontFamily: 'system-ui, -apple-system, sans-serif',
            letterSpacing: -1,
          }}
        >
          Find leads. Automatically.
        </div>
      </div>

      {/* Sound design comment */}
      <div style={{ position: 'absolute', opacity: 0 }}>
        {/* 🎵 SOUND: Subtle sci-fi ambient hum, digital "ping" for each pin drop */}
      </div>
    </AbsoluteFill>
  );
};
