import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from 'remotion';

export const DramaticProblem = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Text SCREAMS onto screen
  const screamScale = spring({
    frame,
    fps,
    config: {
      damping: 5, // VERY bouncy
      stiffness: 400, // SUPER fast
    },
  });

  const textScale = interpolate(screamScale, [0, 1], [0, 1.3]);

  // Shaking effect for everything
  const shakeX = Math.sin(frame * 0.5) * 15;
  const shakeY = Math.cos(frame * 0.7) * 12;

  // Papers flying effect
  const papers = [...Array(15)].map((_, i) => {
    const startDelay = i * 5;
    const paperFrame = frame - startDelay;

    const fallY = paperFrame * 8;
    const rotateSpeed = (i % 2 === 0 ? 1 : -1) * paperFrame * 5;
    const driftX = Math.sin(paperFrame * 0.1) * 100;

    return {
      y: fallY,
      x: driftX + (i * 120) - 900,
      rotate: rotateSpeed,
      opacity: paperFrame > 0 ? Math.max(0, 1 - fallY / 1200) : 0,
    };
  });

  // Glitch effect
  const glitchOffset = frame % 10 === 0 ? Math.random() * 20 - 10 : 0;

  return (
    <AbsoluteFill
      style={{
        background: 'linear-gradient(135deg, #8B0000, #000000)',
        justifyContent: 'center',
        alignItems: 'center',
        overflow: 'hidden',
        transform: `translate(${shakeX}px, ${shakeY}px)`,
      }}
    >
      {/* SCREAMING TEXT */}
      <div
        style={{
          transform: `scale(${textScale}) rotate(${Math.sin(frame * 0.2) * 3}deg)`,
          fontSize: 160,
          fontWeight: 900,
          color: '#FF0000',
          textShadow: `
            0 0 40px rgba(255,0,0,0.8),
            ${glitchOffset}px 0 20px rgba(0,255,255,0.5),
            -${glitchOffset}px 0 20px rgba(255,255,0,0.5)
          `,
          fontFamily: 'Impact, sans-serif',
          letterSpacing: 8,
          textAlign: 'center',
          padding: '0 40px',
          lineHeight: 1.2,
        }}
      >
        SPREADSHEETS?!
        <br />
        REALLY?! 😱
      </div>

      {/* Flying papers with cartoon physics */}
      {papers.map((paper, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            left: paper.x,
            top: -100 + paper.y,
            transform: `rotate(${paper.rotate}deg)`,
            opacity: paper.opacity,
            width: 80,
            height: 100,
            background: 'white',
            border: '2px solid #333',
            boxShadow: '4px 4px 12px rgba(0,0,0,0.5)',
          }}
        >
          <div
            style={{
              fontSize: 8,
              padding: 4,
              color: '#333',
              fontFamily: 'monospace',
            }}
          >
            ████ ████<br />
            ████ ████<br />
            ████ ████
          </div>
        </div>
      ))}

      {/* DRAMATIC red vignette */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: 'radial-gradient(circle, transparent 30%, rgba(139,0,0,0.7) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Sad trombone text (bottom) */}
      {frame > 60 && (
        <div
          style={{
            position: 'absolute',
            bottom: 100,
            fontSize: 32,
            color: '#FFD700',
            fontFamily: 'Impact, sans-serif',
            textShadow: '2px 2px 8px rgba(0,0,0,0.8)',
            opacity: interpolate(frame, [60, 80], [0, 1]),
          }}
        >
          🎺 *sad trombone noises*
        </div>
      )}

      {/* Sound effect comments */}
      <div style={{ position: 'absolute', top: 0, left: 0, opacity: 0 }}>
        {/* 🎵 SOUND: Record scratch + sad trombone "wah wah waaah" */}
        {/* 🎵 SOUND: Papers rustling frantically */}
      </div>
    </AbsoluteFill>
  );
};
