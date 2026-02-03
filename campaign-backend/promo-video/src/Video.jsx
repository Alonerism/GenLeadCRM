import React from 'react';
import { AbsoluteFill, Sequence } from 'remotion';
import { ChaoticIntro } from './scenes/ChaoticIntro';
import { DramaticProblem } from './scenes/DramaticProblem';
import { SolutionWithPizzazz } from './scenes/SolutionWithPizzazz';
import { RidiculousCTA } from './scenes/RidiculousCTA';

export const Video = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: '#000' }}>
      {/* Scene 1: CHAOTIC INTRO (0-3s = 0-90 frames) */}
      <Sequence from={0} durationInFrames={90}>
        <ChaoticIntro />
      </Sequence>

      {/* Scene 2: DRAMATIC PROBLEM (3-8s = 90-240 frames) */}
      <Sequence from={90} durationInFrames={150}>
        <DramaticProblem />
      </Sequence>

      {/* Scene 3: SOLUTION WITH PIZZAZZ (8-20s = 240-600 frames) */}
      <Sequence from={240} durationInFrames={360}>
        <SolutionWithPizzazz />
      </Sequence>

      {/* Scene 4: RIDICULOUS CTA (20-25s = 600-750 frames) */}
      <Sequence from={600} durationInFrames={150}>
        <RidiculousCTA />
      </Sequence>
    </AbsoluteFill>
  );
};
