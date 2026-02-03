import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from 'remotion';

export const AICalling = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Fade in from previous scene
  const sceneOpacity = interpolate(frame, [0, 20], [0, 1]);

  // Waveform pulsing animation
  const waveformBars = [...Array(40)].map((_, i) => {
    // Create organic wave motion
    const frequency = 0.15;
    const phase = i * 0.3;
    const amplitude = Math.abs(Math.sin((frame * frequency) + phase)) * 150 + 30;

    // Gradient position for color variation
    const hue = interpolate(i, [0, 40], [200, 280]);

    return {
      height: amplitude,
      hue,
      opacity: 0.8 + Math.sin(frame * 0.1 + i * 0.2) * 0.2,
    };
  });

  // Phone dial animation (circular progress)
  const dialProgress = spring({
    frame: frame - 30,
    fps,
    config: {
      damping: 200,
      stiffness: 100,
    },
  });

  const dialAngle = interpolate(dialProgress, [0, 1], [0, 360]);

  // Text animations
  const titleOpacity = interpolate(frame, [40, 60], [0, 1], { extrapolateRight: 'clamp' });
  const subtitleOpacity = interpolate(frame, [70, 90], [0, 1], { extrapolateRight: 'clamp' });

  // Scan-line effect
  const scanLineY = (frame * 8) % 1080;

  return (
    <AbsoluteFill
      style={{
        background: 'radial-gradient(ellipse at center, #1a1f4d 0%, #0a0e27 100%)',
        justifyContent: 'center',
        alignItems: 'center',
        opacity: sceneOpacity,
        overflow: 'hidden',
      }}
    >
      {/* Voice waveform */}
      <div
        style={{
          display: 'flex',
          gap: 8,
          alignItems: 'center',
          justifyContent: 'center',
          marginTop: -100,
        }}
      >
        {waveformBars.map((bar, i) => (
          <div
            key={i}
            style={{
              width: 8,
              height: bar.height,
              background: `linear-gradient(180deg, hsl(${bar.hue}, 100%, 60%) 0%, hsl(${bar.hue}, 100%, 40%) 100%)`,
              borderRadius: 4,
              opacity: bar.opacity,
              boxShadow: `0 0 10px hsla(${bar.hue}, 100%, 60%, 0.5)`,
              transition: 'height 0.1s ease-out',
            }}
          />
        ))}
      </div>

      {/* Phone dial UI */}
      <div
        style={{
          position: 'absolute',
          top: '30%',
          right: 200,
          width: 200,
          height: 200,
        }}
      >
        {/* Circular progress ring */}
        <svg width="200" height="200" style={{ transform: 'rotate(-90deg)' }}>
          <circle
            cx="100"
            cy="100"
            r="90"
            fill="none"
            stroke="rgba(0, 212, 255, 0.2)"
            strokeWidth="4"
          />
          <circle
            cx="100"
            cy="100"
            r="90"
            fill="none"
            stroke="url(#dialGradient)"
            strokeWidth="4"
            strokeDasharray={`${2 * Math.PI * 90}`}
            strokeDashoffset={2 * Math.PI * 90 * (1 - dialProgress)}
            strokeLinecap="round"
            style={{ filter: 'drop-shadow(0 0 8px #00d4ff)' }}
          />
          <defs>
            <linearGradient id="dialGradient">
              <stop offset="0%" stopColor="#00d4ff" />
              <stop offset="100%" stopColor="#a855f7" />
            </linearGradient>
          </defs>
        </svg>

        {/* Phone icon in center */}
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            fontSize: 48,
            opacity: dialProgress,
          }}
        >
          📞
        </div>
      </div>

      {/* Text overlays */}
      <div
        style={{
          position: 'absolute',
          bottom: 200,
          textAlign: 'center',
          width: '100%',
        }}
      >
        <div
          style={{
            fontSize: 64,
            fontWeight: 600,
            color: '#ffffff',
            fontFamily: 'system-ui, -apple-system, sans-serif',
            opacity: titleOpacity,
            marginBottom: 20,
            letterSpacing: -1,
          }}
        >
          While you sleep,
        </div>
        <div
          style={{
            fontSize: 64,
            fontWeight: 700,
            background: 'linear-gradient(90deg, #00d4ff 0%, #a855f7 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            fontFamily: 'system-ui, -apple-system, sans-serif',
            opacity: subtitleOpacity,
            letterSpacing: -1,
          }}
        >
          AI closes deals
        </div>
      </div>

      {/* Scan-line effect */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          top: scanLineY,
          width: '100%',
          height: 2,
          background: 'linear-gradient(90deg, transparent 0%, rgba(0, 212, 255, 0.3) 50%, transparent 100%)',
          opacity: 0.5,
        }}
      />

      {/* Subtle grid overlay */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          opacity: 0.03,
          backgroundImage: `
            linear-gradient(0deg, transparent 24%, rgba(0, 212, 255, 0.5) 25%, rgba(0, 212, 255, 0.5) 26%, transparent 27%, transparent 74%, rgba(0, 212, 255, 0.5) 75%, rgba(0, 212, 255, 0.5) 76%, transparent 77%, transparent),
            linear-gradient(90deg, transparent 24%, rgba(0, 212, 255, 0.5) 25%, rgba(0, 212, 255, 0.5) 26%, transparent 27%, transparent 74%, rgba(0, 212, 255, 0.5) 75%, rgba(0, 212, 255, 0.5) 76%, transparent 77%, transparent)
          `,
          backgroundSize: '50px 50px',
        }}
      />

      {/* Sound design comment */}
      <div style={{ position: 'absolute', opacity: 0 }}>
        {/* 🎵 SOUND: Smooth electronic transition, subtle AI voice murmur, dial tone beeps */}
      </div>
    </AbsoluteFill>
  );
};
