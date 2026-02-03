import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from 'remotion';

export const PerformanceDashboard = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Dashboard materialization
  const dashboardSpring = spring({
    frame,
    fps,
    config: {
      damping: 200,
      stiffness: 100,
    },
  });

  const dashboardOpacity = interpolate(frame, [0, 30], [0, 1]);
  const dashboardY = interpolate(dashboardSpring, [0, 1], [100, 0]);

  // Metric animations with stagger
  const metrics = [
    { label: 'Calls Made', value: 1247, delay: 20, color: '#00d4ff' },
    { label: 'Conversions', value: 89, delay: 40, color: '#a855f7' },
    { label: 'ROI', value: 340, suffix: '%', delay: 60, color: '#00ff88' },
  ];

  const animatedMetrics = metrics.map((metric) => {
    const metricSpring = spring({
      frame: frame - metric.delay,
      fps,
      config: {
        damping: 200,
        stiffness: 100,
      },
    });

    const displayValue = Math.floor(metricSpring * metric.value);
    const opacity = frame >= metric.delay ? metricSpring : 0;

    return {
      ...metric,
      displayValue,
      opacity,
    };
  });

  // Chart bars animation
  const chartBars = [65, 78, 82, 91, 95].map((percentage, i) => {
    const barSpring = spring({
      frame: frame - 80 - i * 5,
      fps,
      config: {
        damping: 200,
        stiffness: 100,
      },
    });

    const height = barSpring * (percentage / 100) * 200;
    const opacity = frame >= 80 + i * 5 ? 1 : 0;

    return { height, opacity, percentage };
  });

  // Holographic glow pulse
  const glowPulse = 0.5 + Math.sin(frame * 0.1) * 0.3;

  return (
    <AbsoluteFill
      style={{
        background: 'radial-gradient(ellipse at center, #1a1f4d 0%, #0a0e27 100%)',
        justifyContent: 'center',
        alignItems: 'center',
        opacity: dashboardOpacity,
        overflow: 'hidden',
      }}
    >
      {/* Main dashboard container */}
      <div
        style={{
          transform: `translateY(${dashboardY}px)`,
          width: 1200,
          padding: 60,
          background: 'rgba(15, 23, 42, 0.8)',
          borderRadius: 24,
          border: '1px solid rgba(0, 212, 255, 0.3)',
          boxShadow: `
            0 0 60px rgba(0, 212, 255, ${glowPulse * 0.3}),
            inset 0 0 60px rgba(0, 212, 255, 0.05)
          `,
          backdropFilter: 'blur(10px)',
        }}
      >
        {/* Header */}
        <div
          style={{
            fontSize: 48,
            fontWeight: 600,
            color: '#ffffff',
            marginBottom: 60,
            fontFamily: 'system-ui, -apple-system, sans-serif',
            letterSpacing: -1,
          }}
        >
          Performance Dashboard
        </div>

        {/* Metrics row */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            marginBottom: 60,
          }}
        >
          {animatedMetrics.map((metric, i) => (
            <div
              key={i}
              style={{
                flex: 1,
                textAlign: 'center',
                opacity: metric.opacity,
              }}
            >
              <div
                style={{
                  fontSize: 72,
                  fontWeight: 700,
                  color: metric.color,
                  fontFamily: 'system-ui, -apple-system, sans-serif',
                  textShadow: `0 0 20px ${metric.color}`,
                  marginBottom: 10,
                }}
              >
                {metric.displayValue.toLocaleString()}
                {metric.suffix || ''}
              </div>
              <div
                style={{
                  fontSize: 24,
                  color: 'rgba(255, 255, 255, 0.6)',
                  fontFamily: 'system-ui, -apple-system, sans-serif',
                  textTransform: 'uppercase',
                  letterSpacing: 2,
                }}
              >
                {metric.label}
              </div>
            </div>
          ))}
        </div>

        {/* Chart visualization */}
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-end',
            justifyContent: 'space-around',
            height: 200,
            padding: '0 40px',
            gap: 20,
          }}
        >
          {chartBars.map((bar, i) => (
            <div
              key={i}
              style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                opacity: bar.opacity,
              }}
            >
              <div
                style={{
                  width: '100%',
                  height: bar.height,
                  background: 'linear-gradient(180deg, #00d4ff 0%, #a855f7 100%)',
                  borderRadius: '8px 8px 0 0',
                  boxShadow: '0 0 20px rgba(0, 212, 255, 0.5)',
                  position: 'relative',
                }}
              >
                {/* Percentage label on top of bar */}
                <div
                  style={{
                    position: 'absolute',
                    top: -30,
                    left: '50%',
                    transform: 'translateX(-50%)',
                    fontSize: 18,
                    fontWeight: 600,
                    color: '#00d4ff',
                    fontFamily: 'system-ui, -apple-system, sans-serif',
                  }}
                >
                  {bar.percentage}%
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Week labels */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-around',
            marginTop: 20,
            padding: '0 40px',
          }}
        >
          {['Mon', 'Tue', 'Wed', 'Thu', 'Fri'].map((day, i) => (
            <div
              key={i}
              style={{
                flex: 1,
                textAlign: 'center',
                fontSize: 16,
                color: 'rgba(255, 255, 255, 0.4)',
                fontFamily: 'system-ui, -apple-system, sans-serif',
              }}
            >
              {day}
            </div>
          ))}
        </div>
      </div>

      {/* Floating particles for holographic effect */}
      {[...Array(20)].map((_, i) => {
        const x = (i * 100) % 1920;
        const y = ((frame * 2 + i * 50) % 1080);
        const size = 2 + (i % 3);

        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: x,
              top: y,
              width: size,
              height: size,
              borderRadius: '50%',
              background: i % 2 === 0 ? '#00d4ff' : '#a855f7',
              opacity: 0.2,
              boxShadow: `0 0 ${size * 2}px ${i % 2 === 0 ? '#00d4ff' : '#a855f7'}`,
            }}
          />
        );
      })}

      {/* Sound design comment */}
      <div style={{ position: 'absolute', opacity: 0 }}>
        {/* 🎵 SOUND: Holographic UI materialization, subtle data processing beeps, success chime */}
      </div>
    </AbsoluteFill>
  );
};
