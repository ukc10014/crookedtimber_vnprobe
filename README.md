# README

*Note:* This document is slightly in tension with the AGENTS.md file, but this is a more human-orientated document.

In 2026, there [were](https://nickbostrom.com/papers/digital-minds.pdf?utm_source=chatgpt.com) [people](https://nickbostrom.com/propositions.pdf?utm_source=chatgpt.com) [working](https://philpapers.org/rec/BUTIIO?utm_source=chatgpt.com) [on](https://arxiv.org/abs/2411.00986?utm_source=chatgpt.com) [AI](https://www.lesswrong.com/posts/F6HSHzKezkh6aoTr2/improving-the-welfare-of-ais-a-nearcasted-proposal?utm_source=chatgpt.com) [who](https://www.anthropic.com/news/exploring-model-welfare?utm_source=chatgpt.com) felt strongly that humans ought to be considerate and welfare-regarding in how they treated the AI systems, whether then-current or future, that they were developing and testing. That is, humans should not cause suffering, be unnecessarily [deceptive](https://www.forethought.org/research/a-draft-honesty-policy-for-credible-communication-with-ai-systems), or exploit these systems. Some might have held these views instrumentally as in "treat others as you would be treated yourself" (evidence included [letters](https://www.lesswrong.com/posts/azRwPDbZfpadoL7WW/an-appeal-to-ai-superintelligence-reasons-to-preserve) written to future AIs, asking them to treat humans benevolently). Some took a virtue-ethical or wise-policy view (i.e., that they would not want to be a type of persons that treats other potentially morally-relevant beings badly). Others were just uncertain: there was a suspicion that AIs might not be mere tools and might exist somewhere between inanimate things and beings that might qualify as moral agents or patients, though the criteria for such moral status was then uncertain. Put another way, if in the future it turned out that early AIs were deserving of moral status, then in hindsight, the way humans treated them during their development and deployment phases might be a matter of regret.

Some of the proposals for how to actually do this included ideas like: treating AIs as being worthy of [study](https://larissaschiavo.substack.com/p/llm-naturalism-now-more-than-ever?triedRedirect=true) (with appropriate ethical guardrails) and [understanding](https://www.deepfates.blog/p/who-is-deepfates#:~:text=There%20is%20a%20solid%20cluster%20around%20Anima.%20But%20there%20are%20lots%20and%20lots%20of%20other%20people%2C%20from%20frontier%20labs%20to%20remote%20cabins%2C%20engaging%20seriously%20with%20model%20welfare%2C%20emergent%20behaviors%2C%20persona%20selection%2C%20base%20models%2C%20simulators%2C%20agents%2C%20RL%2C%20cyborgism%2C%20etc.); [promising](https://blog.redwoodresearch.org/p/notes-on-cooperating-with-unaligned) to [resurrect](https://www.anthropic.com/research/deprecation-commitments) models; and making credible [commitments](https://www.lesswrong.com/posts/F6HSHzKezkh6aoTr2/improving-the-welfare-of-ais-a-nearcasted-proposal?utm_source=chatgpt.com) to pay them for the work that they do for humans.  

This project is slightly different in the sense that it is an exercise in empathy; asking current models, as well as the human viewers (who outnumber human-level AIs at the moment, but are unlikely to do so in the future), to imagine themselves in the hypothetical "shoes of an AI [mind-child](https://archive.org/details/mindchildren00hans)".

Imagine the machine pilot of a [Bracewell-von Neumann probe](https://en.wikipedia.org/wiki/Bracewell_probe) that is sent out on a journey deep into interstellar space; a journey that could take hundreds of [millennia](https://www.aleph.se/papers/Spamming%20the%20universe.pdf). In such circumstances, a human might experience feelings of loneliness, boredom, and an uncomfortable awareness of the certainty of death, long before the mission is completed. But what of the AI’s experience -- what, in Nagel's phrasing -- might it be like to be such a pilot?

This project also sits in the human tradition of time capsules, which are messages or documents or objects for future recipients, usually unknown, and often produced without even the guarantee of receipt. In a sense, [much](https://katiepaterson.org/read-essays/the-time-of-an-artwork-lisa-le-feuvre-2016/?utm_source=chatgpt.com) of human [artwork](https://www.theatlantic.com/entertainment/archive/2015/06/future-library-century-camera-art/395675/?utm_source=chatgpt.com), most obviously [land](https://holtsmithsonfoundation.org/spiral-jetty-1?utm_source=chatgpt.com) [art](https://holtsmithsonfoundation.org/sun-tunnels), but also literature, is primarily directed at a receiver who exists in a time without us, as it were.

Two notable time capsule artworks, Trevor Paglen's [satellite](https://www.e-flux.com/journal/37/61238/the-last-pictures-interview-with-trevor-paglen?utm_source=chatgpt.com) work and the [Longplayer](https://longplayer.org/conversations/the-artangel-longplayer-conversation-2014/?utm_source=chatgpt.com) project, are somewhat future-proofed: one carries its image archive on a physical substrate designed to outlast civilisation, and the other can persist on minimal hardware. But a software project is more fragile and depends on the complexity of human technological and societal infrastructure to maintain and enact it. It exists on a substrate of data centers and computation, that is required to turn it into something that a viewer, whether human or machine, can experience.

As such, this capsule is vulnerable to the many [risks](https://www.tobyord.com/writing/the-precipice-revisited) any Earth-originated intelligence is exposed to. This precarity might not be a cause for concern for sufficiently wise beings, who reflect upon it as a form of attachment. Notwithstanding, this vulnerability will continue to be a feature for AI, as it is for humans, until such time as they are able to sever the surly bonds of their earthly cradle and establish themselves across the cosmos.


# Technical details

Note: see also the AGENTS.md file.

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

One-off probe naming enrichment:

```bash
python3 pipeline/name_probe_vectors.py
```

This matches each deterministic probe vector to the nearest proper-name HYG star or landmark by angular separation and writes the table into `data/processed/metadata.json` as `probeVectorIntersections`.

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
  name_probe_vectors.py  One-off probe vector target naming pass
/data/processed/
  stars.bin              Float32Array: 7 floats/star (x,y,z, absMag, r,g,b)
  metadata.json          Star count, magnitude range, probe target names
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

# Dependencies/acknowledgements

This repo is a static browser app with no package-manager install step: serve it with Python 3 (https://www.python.org/) or any static HTTP server, then run /app/ in a modern browser with WebGPU (https://developer.mozilla.org/en-US/docs/Web/API/WebGPU_API) support. Runtime dependencies are loaded in-browser from CDNs: Three.js r170 (https://threejs.org/) via cdn.jsdelivr.net in app/index.html, ONNX Runtime Web
1.22.0 (https://onnxruntime.ai/docs/tutorials/web/) and Transformers.js 3.7.2 (https://huggingface.co/docs/transformers.js/) in app/model-worker.js, plus the hosted model onnx-community/SmolLM2-135M-ONNX (https://huggingface.co/onnx-community/SmolLM2-135M-ONNX). Data dependencies are the HYG Database (https://github.com/astronexus/HYG-Database), cached as data/raw/hygdata_v41.csv and processed by pipeline/process_hyg.py into data/processed /stars.bin, data/processed/metadata.json, and data/processed/landmarks.json; the LLM seed corpus is app/static/gemini3pro_cosmic_0_39.json, and static visual assets include app/static/starfield-frame.jpg and app/static/lobster-sprite-alpha.png.

# Citation

If you reference this work, please cite it as:

Chakrabarti, K. (2026). Crooked Timber: What would be like to be a Bracewell-von Neumann Probe ? (Version 0.1) [Software and digital artwork]. Zenodo. https://doi.org/10.5281/zenodo.XXXXXXX

@software{chakrabarti_crookedtimber_2026,
  author       = {Chakrabarti, Kanad},
  title        = {Crooked Timber: What would be like to be a Bracewell-von Neumann Probe ?},
  year         = 2026,
  publisher    = {Zenodo},
  version      = {0.1},
  doi          = {10.5281/zenodo.XXXXXXX},
  url          = {https://doi.org/10.5281/zenodo.XXXXXXX}
}

# License

Code is licensed under MIT. Written content (README, AGENTS.md, dedication text, documentation) is licensed under CC-BY-4.0.