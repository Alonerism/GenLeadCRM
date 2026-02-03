import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from 'remotion';

export const RidiculousCTA = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Text wobbles and grows
  const textSpring = spring({
    frame,
    fps,
    config: {
      damping: 6,
      stiffness: 300,
    },
  });

  const textScale = interpolate(textSpring, [0, 1], [0, 1.2]);

  // Wobble effect - like jello!
  const wobbleX = Math.sin(frame * 0.3) * 30;
  const wobbleY = Math.cos(frame * 0.4) * 20;
  const wobbleRotate = Math.sin(frame * 0.25) * 8;

  // Everything spins and zooms out at the end (last 2 seconds)
  const spinFrame = frame - 90; // Start spinning at frame 90 (3s in)
  const spinRotate = spinFrame > 0 ? interpolate(spinFrame, [0, 60], [0, 1080]) : 0;
  const zoomOut = spinFrame > 0 ? interpolate(spinFrame, [0, 60], [1, 0.3], { extrapolateRight: 'clamp' }) : 1;

  // Lens flare effect (final moment)
  const flareOpacity = frame > 120 ? interpolate(frame, [120, 150], [0, 1]) : 0;

  return (
    <AbsoluteFill
      style={{
        background: 'linear-gradient(45deg, #FF1493, #00CED1, #FFD700, #FF6347)',
        backgroundSize: '400% 400%',
        animation: spinFrame < 0 ? 'gradient 3s ease infinite' : 'none',
        overflow: 'hidden',
      }}
    >
      <style>
        {`
          @keyframes gradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
          }
        `}
      </style>

      {/* Main CTA Container */}
      <div
        style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: `
            translate(-50%, -50%)
            translate(${wobbleX}px, ${wobbleY}px)
            rotate(${wobbleRotate + spinRotate}deg)
            scale(${textScale * zoomOut})
          `,
        }}
      >
        {/* MASSIVE WOBBLING TEXT */}
        <div
          style={{
            fontSize: 120,
            fontWeight: 900,
            color: '#FFFFFF',
            textShadow: `
              0 0 60px rgba(255,215,0,1),
              8px 8px 0 #000,
              -4px -4px 0 #FF1493,
              4px 4px 0 #00CED1
            `,
            fontFamily: 'Impact, sans-serif',
            textAlign: 'center',
            lineHeight: 1.1,
            letterSpacing: 4,
          }}
        >
          ALLLLLRIGHTY
          <br />
          THEN! 🎭
        </div>

        {/* Sub-text */}
        <div
          style={{
            fontSize: 64,
            fontWeight: 700,
            color: '#FFD700',
            textShadow: '0 0 30px rgba(0,0,0,0.8), 4px 4px 0 #000',
            fontFamily: 'Impact, sans-serif',
            textAlign: 'center',
            marginTop: 40,
            transform: `scale(${1 + Math.sin(frame * 0.4) * 0.1})`,
          }}
        >
          START CLOSING
          <br />
          DEALS! 💰☀️
        </div>
      </div>

      {/* Spinning elements around the edges */}
      {[...Array(12)].map((_, i) => {
        const angle = (i / 12) * Math.PI * 2 + frame * 0.05;
        const radius = 600;
        const x = Math.cos(angle) * radius;
        const y = Math.sin(angle) * radius;

        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: '50%',
              top: '50%',
              transform: `translate(${x}px, ${y}px) rotate(${frame * 3}deg) scale(${zoomOut})`,
              fontSize: 80,
            }}
          >
            {['☀️', '💰', '📞', '🎯'][i % 4]}
          </div>
        );
      })}

      {/* EXAGGERATED Lens Flare */}
      {flareOpacity > 0 && (
        <>
          <div
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: 2000,
              height: 2000,
              background: 'radial-gradient(circle, rgba(255,255,255,1) 0%, transparent 70%)',
              opacity: flareOpacity,
              pointerEvents: 'none',
            }}
          />
          <div
            style={{
              position: 'absolute',
              inset: 0,
              background: '#FFFFFF',
              opacity: flareOpacity * 0.8,
              pointerEvents: 'none',
            }}
          />
        </>
      )}

      {/* Freeze frame border (final moment) */}
      {frame > 140 && (
        <div
          style={{
            position: 'absolute',
            inset: 20,
            border: '20px solid #FFD700',
            borderRadius: 40,
            boxShadow: 'inset 0 0 100px rgba(0,0,0,0.5), 0 0 100px rgba(255,215,0,0.8)',
            pointerEvents: 'none',
          }}
        />
      )}

      {/* Sound effect annotations */}
      <div style={{ position: 'absolute', top: 0, left: 0, opacity: 0 }}>
        {/* 🎵 SOUND: Jim Carrey "Alrighty then!" sample */}
        {/* 🎵 SOUND: Cartoon spin whoosh */}
        {/* 🎵 SOUND: Cash register "CHA-CHING!" */}
        {/* 🎵 SOUND: Triumphant fanfare */}
      </div>
    </AbsoluteFill>
  );
};
