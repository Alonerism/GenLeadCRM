import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from 'remotion';

export const TheSystem = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Panel slide-in animations
  const panelSpring = spring({
    frame,
    fps,
    config: {
      damping: 200,
      stiffness: 100,
    },
  });

  const leftPanelX = interpolate(panelSpring, [0, 1], [-800, 0]);
  const centerPanelY = interpolate(panelSpring, [0, 1], [600, 0]);
  const rightPanelX = interpolate(panelSpring, [0, 1], [800, 0]);

  // Connection lines appear after panels
  const connectionOpacity = interpolate(frame, [40, 60], [0, 1], { extrapolateRight: 'clamp' });

  // Glow pulse for connections
  const glowPulse = 0.5 + Math.sin(frame * 0.15) * 0.5;

  // CTA fade in
  const ctaOpacity = interpolate(frame, [80, 110], [0, 1], { extrapolateRight: 'clamp' });
  const ctaScale = spring({
    frame: frame - 80,
    fps,
    config: {
      damping: 200,
      stiffness: 100,
    },
  });

  // Logo fade in
  const logoOpacity = interpolate(frame, [140, 170], [0, 1], { extrapolateRight: 'clamp' });

  // Animated line drawing
  const lineProgress = interpolate(frame, [40, 80], [0, 1], { extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill
      style={{
        background: 'radial-gradient(ellipse at center, #1a1f4d 0%, #0a0e27 100%)',
        justifyContent: 'center',
        alignItems: 'center',
        overflow: 'hidden',
      }}
    >
      {/* Three panel container */}
      <div
        style={{
          display: 'flex',
          gap: 40,
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
          marginTop: -100,
        }}
      >
        {/* Left Panel: Lead Generation */}
        <div
          style={{
            width: 400,
            height: 300,
            background: 'rgba(15, 23, 42, 0.9)',
            borderRadius: 16,
            border: '1px solid rgba(0, 212, 255, 0.3)',
            boxShadow: `0 0 30px rgba(0, 212, 255, ${glowPulse * 0.3})`,
            transform: `translateX(${leftPanelX}px)`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 30,
            backdropFilter: 'blur(10px)',
          }}
        >
          <div style={{ fontSize: 64, marginBottom: 20 }}>🗺️</div>
          <div
            style={{
              fontSize: 28,
              fontWeight: 600,
              color: '#00d4ff',
              fontFamily: 'system-ui, -apple-system, sans-serif',
              textAlign: 'center',
            }}
          >
            Lead Generation
          </div>
          <div
            style={{
              fontSize: 16,
              color: 'rgba(255, 255, 255, 0.5)',
              fontFamily: 'system-ui, -apple-system, sans-serif',
              textAlign: 'center',
              marginTop: 10,
            }}
          >
            Google Maps scraping
          </div>
        </div>

        {/* Center Panel: AI Voice */}
        <div
          style={{
            width: 400,
            height: 300,
            background: 'rgba(15, 23, 42, 0.9)',
            borderRadius: 16,
            border: '1px solid rgba(168, 85, 247, 0.3)',
            boxShadow: `0 0 30px rgba(168, 85, 247, ${glowPulse * 0.3})`,
            transform: `translateY(${centerPanelY}px)`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 30,
            backdropFilter: 'blur(10px)',
          }}
        >
          <div style={{ fontSize: 64, marginBottom: 20 }}>🤖</div>
          <div
            style={{
              fontSize: 28,
              fontWeight: 600,
              color: '#a855f7',
              fontFamily: 'system-ui, -apple-system, sans-serif',
              textAlign: 'center',
            }}
          >
            AI Voice Agent
          </div>
          <div
            style={{
              fontSize: 16,
              color: 'rgba(255, 255, 255, 0.5)',
              fontFamily: 'system-ui, -apple-system, sans-serif',
              textAlign: 'center',
              marginTop: 10,
            }}
          >
            Autonomous calling
          </div>
        </div>

        {/* Right Panel: Dashboard */}
        <div
          style={{
            width: 400,
            height: 300,
            background: 'rgba(15, 23, 42, 0.9)',
            borderRadius: 16,
            border: '1px solid rgba(0, 255, 136, 0.3)',
            boxShadow: `0 0 30px rgba(0, 255, 136, ${glowPulse * 0.3})`,
            transform: `translateX(${rightPanelX}px)`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 30,
            backdropFilter: 'blur(10px)',
          }}
        >
          <div style={{ fontSize: 64, marginBottom: 20 }}>📊</div>
          <div
            style={{
              fontSize: 28,
              fontWeight: 600,
              color: '#00ff88',
              fontFamily: 'system-ui, -apple-system, sans-serif',
              textAlign: 'center',
            }}
          >
            Analytics
          </div>
          <div
            style={{
              fontSize: 16,
              color: 'rgba(255, 255, 255, 0.5)',
              fontFamily: 'system-ui, -apple-system, sans-serif',
              textAlign: 'center',
              marginTop: 10,
            }}
          >
            Real-time insights
          </div>
        </div>

        {/* Connection lines with glow */}
        <svg
          width="1300"
          height="400"
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            opacity: connectionOpacity,
            pointerEvents: 'none',
          }}
        >
          <defs>
            <linearGradient id="lineGradient1" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#00d4ff" />
              <stop offset="100%" stopColor="#a855f7" />
            </linearGradient>
            <linearGradient id="lineGradient2" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#a855f7" />
              <stop offset="100%" stopColor="#00ff88" />
            </linearGradient>
            <filter id="glow">
              <feGaussianBlur stdDeviation="4" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Line from left to center */}
          <line
            x1="250"
            y1="200"
            x2={250 + 450 * lineProgress}
            y2="200"
            stroke="url(#lineGradient1)"
            strokeWidth="3"
            strokeDasharray="10,5"
            filter="url(#glow)"
            opacity={glowPulse}
          />

          {/* Line from center to right */}
          <line
            x1="700"
            y1="200"
            x2={700 + 350 * lineProgress}
            y2="200"
            stroke="url(#lineGradient2)"
            strokeWidth="3"
            strokeDasharray="10,5"
            filter="url(#glow)"
            opacity={glowPulse}
          />

          {/* Animated dots traveling along lines */}
          {lineProgress > 0.5 && (
            <>
              <circle
                cx={250 + (450 * ((frame * 3) % 100)) / 100}
                cy="200"
                r="5"
                fill="#00d4ff"
                filter="url(#glow)"
              />
              <circle
                cx={700 + (350 * ((frame * 3) % 100)) / 100}
                cy="200"
                r="5"
                fill="#a855f7"
                filter="url(#glow)"
              />
            </>
          )}
        </svg>
      </div>

      {/* CTA Text */}
      <div
        style={{
          position: 'absolute',
          bottom: 180,
          textAlign: 'center',
          opacity: ctaOpacity,
          transform: `scale(${ctaScale})`,
        }}
      >
        <div
          style={{
            fontSize: 72,
            fontWeight: 700,
            background: 'linear-gradient(90deg, #00d4ff 0%, #a855f7 50%, #00ff88 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            fontFamily: 'system-ui, -apple-system, sans-serif',
            letterSpacing: -1,
            marginBottom: 10,
          }}
        >
          Your AI Sales Team
        </div>
        <div
          style={{
            fontSize: 48,
            fontWeight: 400,
            color: 'rgba(255, 255, 255, 0.9)',
            fontFamily: 'system-ui, -apple-system, sans-serif',
            letterSpacing: -0.5,
          }}
        >
          Deploy in 5 Minutes
        </div>
      </div>

      {/* Logo */}
      <div
        style={{
          position: 'absolute',
          bottom: 80,
          opacity: logoOpacity,
        }}
      >
        <div
          style={{
            fontSize: 56,
            fontWeight: 700,
            background: 'linear-gradient(90deg, #FFD700 0%, #FFA500 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            fontFamily: 'system-ui, -apple-system, sans-serif',
            letterSpacing: 2,
            display: 'flex',
            alignItems: 'center',
            gap: 15,
          }}
        >
          <span style={{ fontSize: 48 }}>☀️</span>
          SUNBEAM CRM
        </div>
      </div>

      {/* Sound design comment */}
      <div style={{ position: 'absolute', opacity: 0 }}>
        {/* 🎵 SOUND: Panels sliding in with futuristic whoosh, connection beeps, uplifting finale music */}
      </div>
    </AbsoluteFill>
  );
};
