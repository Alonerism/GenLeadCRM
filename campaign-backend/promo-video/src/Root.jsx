import React from 'react';
import { Composition } from 'remotion';
import { Video } from './Video';
import { FacebookAd } from './FacebookAd';

export const RemotionRoot = () => {
  return (
    <>
      {/* Jim Carrey style promo */}
      <Composition
        id="SunbeamPromo"
        component={Video}
        durationInFrames={750} // 25 seconds at 30fps
        fps={30}
        width={1920}
        height={1080}
      />

      {/* Professional Facebook Ad - 16:9 */}
      <Composition
        id="FacebookAd-16x9"
        component={FacebookAd}
        durationInFrames={750} // 25 seconds at 30fps
        fps={30}
        width={1920}
        height={1080}
      />

      {/* Professional Facebook Ad - 1:1 Square */}
      <Composition
        id="FacebookAd-Square"
        component={FacebookAd}
        durationInFrames={750} // 25 seconds at 30fps
        fps={30}
        width={1080}
        height={1080}
      />
    </>
  );
};
