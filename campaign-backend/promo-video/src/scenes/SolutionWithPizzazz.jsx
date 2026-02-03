import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from 'remotion';

export const SolutionWithPizzazz = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Google Maps pins DROP like Ace Ventura packages (0-3s)
  const pinDrops = [...Array(8)].map((_, i) => {
    const startFrame = i * 15;
    const dropSpring = spring({
      frame: frame - startFrame,
      fps,
      config: {
        damping: 6,
        stiffness: 200,
      },
    });

    const y = interpolate(dropSpring, [0, 1], [-500, 200 + i * 80]);
    const rotate = interpolate(dropSpring, [0, 1], [720, 0]);
    const scale = interpolate(dropSpring, [0, 1], [0.3, 1.1]);

    return { y, rotate, scale, x: -600 + i * 180, visible: frame > startFrame };
  });

  // "We got you covered" text (3-5s, frame 90-150)
  const taglineFrame = frame - 90;
  const taglineSpring = spring({
    frame: taglineFrame,
    fps,
    config: {
      damping: 8,
      stiffness: 300,
    },
  });

  const taglineScale = interpolate(taglineSpring, [0, 1], [0, 1.2]);

  // Dashboard elements ZOOM in (5-8s, frame 150-240)
  const dashZoom = spring({
    frame: frame - 150,
    fps,
    config: {
      damping: 10,
      stiffness: 300,
    },
  });

  const dashScale = interpolate(dashZoom, [0, 0.3, 1], [1, 3, 1]); // Zooms WAY too close then snaps back

  // Voice Agent waveform (8-11s, frame 240-330)
  const waveAmplitude = frame > 240 ? Math.abs(Math.sin(frame * 0.5)) * 100 + 50 : 0;

  // "AI so smart" text (10-12s, frame 300-360)
  const aiTextSpring = spring({
    frame: frame - 300,
    fps,
    config: {
      damping: 5,
      stiffness: 400,
    },
  });

  const aiTextScale = interpolate(aiTextSpring, [0, 1], [0, 1.3]);

  // Everything wiggles
  const wiggleRotate = Math.sin(frame * 0.3) * 3;

  return (
    <AbsoluteFill
      style={{
        background: 'linear-gradient(135deg, #FF6B35, #F7931E, #FFD700)',
        overflow: 'hidden',
      }}
    >
      {/* Google Maps Pins DROPPING */}
      {frame < 120 && (
        <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}>
          {pinDrops.map((pin, i) => (
            pin.visible && (
              <div
                key={i}
                style={{
                  position: 'absolute',
                  left: '50%',
                  top: '50%',
                  transform: `translate(${pin.x}px, ${pin.y}px) rotate(${pin.rotate}deg) scale(${pin.scale})`,
                  fontSize: 60,
                }}
              >
                📍
              </div>
            )
          ))}

          {frame > 60 && (
            <div
              style={{
                position: 'absolute',
                top: '40%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                fontSize: 72,
                fontWeight: 900,
                color: '#FFF',
                textShadow: '4px 4px 12px rgba(0,0,0,0.6)',
                fontFamily: 'Impact, sans-serif',
                textAlign: 'center',
              }}
            >
              LEADS FROM<br />GOOGLE MAPS! 🗺️
            </div>
          )}
        </div>
      )}

      {/* "WE GOT YOU COVERED LIKE A GLOVE!" */}
      {taglineFrame > 0 && taglineFrame < 120 && (
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: `translate(-50%, -50%) scale(${taglineScale}) rotate(${wiggleRotate}deg)`,
            fontSize: 86,
            fontWeight: 900,
            color: '#FFFFFF',
            textShadow: '0 0 30px rgba(0,0,0,0.8), 6px 6px 0 #FF1493',
            fontFamily: 'Impact, sans-serif',
            textAlign: 'center',
            lineHeight: 1.1,
          }}
        >
          WE GOT YOU COVERED<br />
          LIKE A GLOVE! 🧤
        </div>
      )}

      {/* Dashboard Elements ZOOMING */}
      {frame > 150 && frame < 240 && (
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: `translate(-50%, -50%) scale(${dashZoom})`,
          }}
        >
          <div
            style={{
              background: 'rgba(255,255,255,0.95)',
              borderRadius: 20,
              padding: 40,
              boxShadow: '0 20px 60px rgba(0,0,0,0.4)',
              border: '4px solid #FF1493',
            }}
          >
            <div style={{ fontSize: 48, fontWeight: 700, marginBottom: 20, color: '#333' }}>
              📊 CAMPAIGN DASHBOARD
            </div>
            <div style={{ fontSize: 32, color: '#666' }}>
              ✅ Leads: <span style={{ color: '#00FF00', fontWeight: 900 }}>1,247</span>
              <br />
              📞 Calls: <span style={{ color: '#FF6B35', fontWeight: 900 }}>856</span>
              <br />
              💰 Deals: <span style={{ color: '#FFD700', fontWeight: 900 }}>$127K</span>
            </div>
          </div>
        </div>
      )}

      {/* Voice Agent CRAZY Waveform */}
      {frame > 240 && frame < 330 && (
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: 1200,
          }}
        >
          <div
            style={{
              fontSize: 64,
              fontWeight: 900,
              color: '#FFF',
              textShadow: '4px 4px 12px rgba(0,0,0,0.8)',
              fontFamily: 'Impact, sans-serif',
              textAlign: 'center',
              marginBottom: 40,
            }}
          >
            🤖 AI VOICE AGENT
          </div>

          {/* Crazy waveform */}
          <div style={{ display: 'flex', justifyContent: 'center', gap: 10, alignItems: 'center' }}>
            {[...Array(20)].map((_, i) => {
              const height = Math.abs(Math.sin((frame + i * 10) * 0.2)) * waveAmplitude + 20;
              return (
                <div
                  key={i}
                  style={{
                    width: 24,
                    height,
                    background: `hsl(${i * 18 + frame * 2}, 100%, 60%)`,
                    borderRadius: 12,
                  }}
                />
              );
            })}
          </div>
        </div>
      )}

      {/* "AI SO SMART IT'S SMOKIN!" */}
      {aiTextSpring > 0 && (
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: `translate(-50%, -50%) scale(${aiTextScale}) rotate(${wiggleRotate * 2}deg)`,
            fontSize: 96,
            fontWeight: 900,
            color: '#00FF00',
            textShadow: `
              0 0 40px rgba(0,255,0,0.8),
              6px 6px 0 #000,
              -2px -2px 0 #FFF
            `,
            fontFamily: 'Impact, sans-serif',
            textAlign: 'center',
            lineHeight: 1.2,
          }}
        >
          AI SO SMART<br />
          IT'S SMOKIN'! 🔥
        </div>
      )}

      {/* Spring physics annotation */}
      <div style={{ position: 'absolute', top: 0, left: 0, opacity: 0 }}>
        {/* 🎵 SOUND: "BOING BOING" pin drops */}
        {/* 🎵 SOUND: Ace Ventura "Alrighty then!" sample */}
        {/* 🎵 SOUND: Digital whoosh zoom */}
        {/* 🎵 SOUND: Sci-fi AI beeps and boops */}
      </div>
    </AbsoluteFill>
  );
};
