README 24 April 2025

## Von Neumann Probe Installation

This repository contains a browser-based installation with two screens in one `/app/` experience:

- a live or static von Neumann probe starfield
- a browser LLM activation viewer

The main runtime lives at `app/index.html`. The root-level `README.md` is kept as a project overview and rough operator guide.

### Quick Start

```bash
python3 -m http.server 8080
# open http://localhost:8080/app/
```

### Data Pipeline

```bash
python3 pipeline/process_hyg.py
```

Downloads HYG v4.1 star catalog (~34MB CSV), processes ~119k stars, outputs binary + JSON to `data/processed/`. You only need to run this if the processed data is missing.

### Project Structure

```
/app/
  index.html             Main two-screen experience
  renderer.js            Starfield renderer, shaders, simulation
  model-viewer.js        Browser-facing LLM activation viewer
  model-worker.js        Worker that runs the small model
  model.html             Standalone model debug page
  static/                Captured starfield frame, corpus seed, assets
/pipeline/
  process_hyg.py         Star catalog download + processing
/data/processed/
  stars.bin              Float32Array: 7 floats/star (x,y,z, absMag, r,g,b)
  metadata.json          Star count, magnitude range
  landmarks.json         Named star positions for labels
```

### Using the Starfield

The starfield uses a virtual swarm of 997 probes. The current probe is selected from that swarm and re-selected randomly when the starfield screen is re-entered from the prime cadence.

All probes travel at 5% speed of light.

**Transport controls**:
- Play/Pause button starts the simulation
- Speed buttons: 1:1 (real-time), 100, 1k, 10k, 100k years per second
- Time slider: scrub through the simulation timeline
- FOV slider: field of view (20-120 degrees)

**Relativistic effects** (toggle buttons):
- Aberr: stellar aberration (stars cluster toward direction of travel)
- Dopp: Doppler colour shift (blue ahead, red behind)
- Beam: searchlight/beaming effect (stars brighter ahead, dimmer behind)

**Overlay toggles**:
- Sail: solar sail visualisation (degrades over ~1000 years)
- Clouds: Milky Way volumetric glow (on by default)
- Grid: galactic plane reference grid
- Arms: spiral arm centerlines
- Rings: distance rings from Sol
- Trail: probe trajectory trail
- Labels: named star/landmark labels
- Map: galactic position mini-map (top-down and side views)
- Tune: Milky Way shader tuning panel

### Milky Way Tuning Panel

The "Tune" button opens a live parameter panel for adjusting the volumetric Milky Way rendering. Changes are applied immediately. The panel includes presets (Default, Subtle, Dramatic, Clean) and individual sliders:

| Parameter | What it controls |
|-----------|-----------------|
| Emission | Overall glow brightness (log scale) |
| Dust Abs | Dust absorption strength (log scale) |
| Disk Height | Stellar disk vertical extent (ly) |
| Dust Height | Dust lane base thickness (ly) |
| Exposure | Post-processing exposure multiplier |
| Glow Noise | Fractal noise amplitude for emission boundary |
| Dust Noise | Fractal noise amplitude for dust boundary |
| Rift Str | Great Rift midplane dust strength |
| Bulge Str | Central bulge brightness |
| Disk Taper | How quickly the stellar disk thins at large radii |
| Dust Taper | How far dust extends radially from galactic center |
| Dust Large | Weight of large-scale (~120 degree) dust patches |
| Dust Fine | Weight of medium/fine dust filaments |
| Disk Warp | Galactic disk sinusoidal warp amplitude |

**Presets** set all parameters at once (including FOV):
- **Default**: balanced starting point (FOV 60)
- **Subtle**: understated, dimmer glow
- **Dramatic**: bright bulge, strong dust, wide field (FOV 120)
- **Clean**: no noise/warp, smooth disk for debugging

### Technical Details

- Three.js r170 via CDN import map (no bundler)
- 119k real stars (HYG catalog) + 500k procedural stars filling the galaxy
- Stars: custom `ShaderMaterial` with magnitude-based sizing and colour
- LLM token vocalization exists in the browser viewer but is disabled by default; set `VOICE_GENERATED_TOKENS` to `true` in `app/model-viewer.js` and `app/model.html` to re-enable speech for generated alphanumeric tokens.
- Milky Way: ray-marched volumetric shader on a sky sphere (24 steps, 80k ly range)
  - Exponential disk + spiral arms + central bulge density model
  - Domain-warped FBM noise for fractal cloud boundaries
  - 2D angular noise for large-scale dust structure (tendrils, dark patches)
  - Dust absorption with Great Rift
  - Galactic disk warp
  - Tone mapping with gamma correction
- Bloom post-processing (UnrealBloomPass)
- Dirty-flag rendering: GPU idles when nothing changes (no fan noise)
- Coordinates: light-years, origin at Sol, +x toward galactic center
- The main `/app/` page auto-enters once the splash, starfield, and model are ready, then hard-cuts between the two screens on prime-number millisecond intervals.
- The model viewer can speak generated alphanumeric tokens, but speech is disabled by default in `app/model-viewer.js` and `app/model.html`.

### Branches

- `main` — stable site
- `von-neumann-probe` — simulator feature branch
