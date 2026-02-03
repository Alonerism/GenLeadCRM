import React from 'react';
import { AbsoluteFill, Sequence } from 'remotion';
import { LeadGeneration } from './scenes/ad/LeadGeneration';
import { AICalling } from './scenes/ad/AICalling';
import { PerformanceDashboard } from './scenes/ad/PerformanceDashboard';
import { TheSystem } from './scenes/ad/TheSystem';

export const FacebookAd = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: '#0a0e27' }}>
      {/* Scene 1: LEAD GENERATION (0-5s = 0-150 frames) */}
      <Sequence from={0} durationInFrames={150}>
        <LeadGeneration />
      </Sequence>

      {/* Scene 2: AI CALLING (5-10s = 150-300 frames) */}
      <Sequence from={150} durationInFrames={150}>
        <AICalling />
      </Sequence>

      {/* Scene 3: PERFORMANCE DASHBOARD (10-18s = 300-540 frames) */}
      <Sequence from={300} durationInFrames={240}>
        <PerformanceDashboard />
      </Sequence>

      {/* Scene 4: THE SYSTEM (18-25s = 540-750 frames) */}
      <Sequence from={540} durationInFrames={210}>
        <TheSystem />
      </Sequence>
    </AbsoluteFill>
  );
};
