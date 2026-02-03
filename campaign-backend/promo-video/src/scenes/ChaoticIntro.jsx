import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from 'remotion';

export const ChaoticIntro = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // EXPLOSIVE logo animation with INSANE spring physics
  const logoScale = spring({
    frame,
    fps,
    config: {
      damping: 10, // Super bouncy!
      stiffness: 300, // Fast and aggressive
    },
  });

  // Logo EXPLODES from 0.5x to 1.2x then settles
  const logoScaleExaggerated = interpolate(
    logoScale,
    [0, 1],
    [0.5, 1.2]
  );

  // Crazy rotation
  const logoRotation = spring({
    frame,
    fps,
    config: {
      damping: 12,
      stiffness: 200,
    },
  });

  const logoRotate = interpolate(logoRotation, [0, 1], [-720, 0]);

  // Tagline bounces in with rubber-band effect (delayed)
  const taglineDelay = 30; // Start after 1 second
  const taglineSpring = spring({
    frame: frame - taglineDelay,
    fps,
    config: {
      damping: 8,
      stiffness: 300,
    },
  });

  const taglineY = interpolate(
    taglineSpring,
    [0, 1],
    [1080, 0] // Bounces from bottom
  );

  const taglineScale = interpolate(
    taglineSpring,
    [0, 1],
    [0.5, 1.2]
  );

  // Background pulse effect
  const bgPulse = Math.sin(frame * 0.3) * 20 + 100;

  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(circle, rgb(${bgPulse}, 50, 200), rgb(20, 20, 50))`,
        justifyContent: 'center',
        alignItems: 'center',
        overflow: 'hidden',
      }}
    >
      {/* EXPLOSIVE LOGO */}
      <div
        style={{
          transform: `scale(${logoScaleExaggerated}) rotate(${logoRotate}deg)`,
          fontSize: 180,
          fontWeight: 900,
          background: 'linear-gradient(45deg, #FFD700, #FFA500, #FF6347)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          textShadow: '0 0 40px rgba(255,215,0,0.8)',
          fontFamily: 'Impact, sans-serif',
          letterSpacing: 10,
        }}
      >
        ☀️ SUNBEAM
      </div>

      {/* BOUNCING TAGLINE */}
      {frame > taglineDelay && (
        <div
          style={{
            position: 'absolute',
            bottom: 200,
            transform: `translateY(${taglineY}px) scale(${taglineScale}) rotate(${Math.sin(frame * 0.2) * 5}deg)`,
            fontSize: 48,
            fontWeight: 700,
            color: '#FFD700',
            textShadow: '0 0 20px rgba(255,215,0,0.6), 0 0 40px rgba(255,215,0,0.4)',
            textAlign: 'center',
            fontFamily: 'Impact, sans-serif',
            padding: '0 40px',
          }}
        >
          LIKE THE MASK, BUT FOR SOLAR SALES! 😎
        </div>
      )}

      {/* Particle explosion effects */}
      {[...Array(20)].map((_, i) => {
        const angle = (i / 20) * Math.PI * 2;
        const distance = logoScale * 400;
        const x = Math.cos(angle) * distance;
        const y = Math.sin(angle) * distance;

        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: '50%',
              top: '50%',
              transform: `translate(${x}px, ${y}px) scale(${logoScale})`,
              width: 20,
              height: 20,
              borderRadius: '50%',
              background: `hsl(${i * 18}, 100%, 60%)`,
              opacity: 1 - logoScale,
            }}
          />
        );
      })}

      {/* Sound effect comment */}
      {frame === 0 && (
        <div style={{ position: 'absolute', top: 0, left: 0, opacity: 0 }}>
          {/* 🎵 SOUND: Massive "BOOM" explosion + "WHOOOOSH" whoosh */}
        </div>
      )}
    </AbsoluteFill>
  );
};
