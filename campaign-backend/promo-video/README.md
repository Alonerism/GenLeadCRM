# 🎬 Sunbeam CRM - Promotional Videos

Two distinct promotional videos for Sunbeam CRM, created with Remotion:

1. **🎭 Jim Carrey Style** - Hilariously over-the-top, energetic, and chaotic
2. **🌟 Professional Facebook Ad** - Dark sci-fi aesthetic, sleek and modern

## Video Options

### Option 1: Jim Carrey Style (Fun & Viral)
A hilariously over-the-top promotional video packed with exaggerated Jim Carrey-style energy!

## 🎬 Video Structure (25 seconds, 30fps, 1920x1080)

### Scene 1: CHAOTIC INTRO (0-3s)
- Logo EXPLODES onto screen with exaggerated spring animation
- Tagline bounces in: "Like The Mask, but for Solar Sales!"
- Rubber-band elastic effects everywhere
- Particle explosion effects

### Scene 2: DRAMATIC PROBLEM (3-8s)
- Text SCREAMS: "SPREADSHEETS?! REALLY?!"
- Papers flying with cartoon physics
- Exaggerated shaking and glitching
- Sad trombone vibes

### Scene 3: SOLUTION WITH PIZZAZZ (8-20s)
- Google Maps pins DROP like Ace Ventura packages
- "We got you covered like a glove!" tagline
- Dashboard elements ZOOM in way too close then snap back
- Voice Agent with CRAZY waveform animation
- "AI so smart it's SMOKIN!" (The Mask reference)
- Everything wiggles with spring physics cranked to 11

### Scene 4: RIDICULOUS CTA (20-25s)
- "ALLLLLRIGHTY THEN! Start Closing Deals!" in massive wobbling text
- Everything spinning and zooming out
- Final freeze frame with exaggerated lens flare
- Icons orbiting at high speed

## 🎨 Style Features

- **ALL CAPS** text for emphasis
- Overshoot animations (damping: 5-10, stiffness: 200-400)
- Rotation effects on EVERYTHING
- Scale animations from 0.5x → 1.2x → 1x
- Bright, saturated 90s comedy colors
- Sound effect suggestions in code comments
- Professionally ridiculous!

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start Remotion Studio (preview in browser)
npm start

# Render the video
npm run build
```

## 🎵 Sound Effects (Add These!)

The code includes comments suggesting these sound effects:

- **Intro**: Massive "BOOM" explosion + "WHOOOOSH"
- **Problem**: Record scratch + sad trombone "wah wah waaah"
- **Solution**: "BOING BOING" pin drops, Ace Ventura samples, digital whooshes
- **CTA**: Jim Carrey "Alrighty then!" sample, cash register "CHA-CHING!", triumphant fanfare

## 📁 Project Structure

```
promo-video/
├── src/
│   ├── Root.jsx              # Composition registration
│   ├── Video.jsx             # Main video timeline
│   ├── index.jsx             # Entry point
│   └── scenes/
│       ├── ChaoticIntro.jsx
│       ├── DramaticProblem.jsx
│       ├── SolutionWithPizzazz.jsx
│       └── RidiculousCTA.jsx
├── package.json
└── remotion.config.mjs
```

## 🎯 Features Showcased

Based on the actual Sunbeam CRM system:

1. **Google Maps Lead Generation** - Scrapes leads from Google Maps
2. **AI Voice Agent** - Automated calling with Twilio + OpenAI
3. **Campaign Dashboard** - React frontend for managing solar sales campaigns
4. **Campaign Orchestration** - Backend API coordinating everything

## 🎨 Animation Techniques Used

- Spring physics with extreme parameters
- Interpolation with overshoot
- Particle systems
- Rotation transformations
- Scale animations
- CSS gradient animations
- Dynamic waveform visualization
- Lens flare effects

## 📝 Notes

- Make it so energetic people HAVE to watch it twice to catch everything ✓
- Professional quality with ridiculous execution ✓
- Every frame is packed with movement ✓
- Color palette: 90s comedy movie poster vibes ✓

---

Made with 🎭 energy and ☀️ Sunbeam CRM

---

### Option 2: Professional Facebook Ad (Sleek & Modern)

See **[FACEBOOK_AD_README.md](./FACEBOOK_AD_README.md)** for the professional version!

**Key Features:**
- Dark sci-fi aesthetic (Matrix meets modern SaaS)
- Smooth spring animations (damping: 200, stiffness: 100)
- Three distinct scenes showcasing the platform
- Available in 16:9 (1920x1080) and 1:1 (1080x1080) for social media
- Professional color palette: Electric blue, neon purple, dark backgrounds

**Quick Render:**
```bash
# 16:9 Version (YouTube, LinkedIn, Twitter)
npm run build:fb-16x9

# 1:1 Square Version (Instagram, Facebook)
npm run build:fb-square

# Render both styles
npm run build:all
```

---

## 🎬 Which Video Should You Use?

| Use Case | Recommended Version |
|----------|-------------------|
| Viral social media campaign | 🎭 Jim Carrey Style |
| Facebook/Instagram ads | 🌟 Professional Ad |
| Product demo for clients | 🌟 Professional Ad |
| Internal team hype video | 🎭 Jim Carrey Style |
| LinkedIn/B2B marketing | 🌟 Professional Ad |
| Twitter engagement | 🎭 Jim Carrey Style |

