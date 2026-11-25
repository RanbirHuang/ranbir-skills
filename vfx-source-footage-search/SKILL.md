---
name: vfx-source-footage-search
description: Find real-shot source clips on free stock sites (Pexels, Pixabay, Mixkit, Coverr) for video-effect training pairs, check them frame by frame against the shot requirements, and return download links; 找原片、找素材视频、试标素材.
---

# Source footage search for VFX pairs (找特效原片)

Finds stock clips that an AI tool can add an effect to with little trouble, and hands back
**download links** (no downloading unless asked). Built for the Baidu 众测「实拍视频采集 + 特效制作」
project: P1 = background/physical interaction (rain, snow, wind, ground change), P2 = local effect
(hair on fire, halo…).

## 1. Shot requirements (check every candidate against all of them)

| # | Requirement | Why / typical rejection |
|---|---|---|
| 1 | **Fixed camera** for the whole usable segment | Background landmarks (poles, trees, windows) must stay at the same spot in every frame. Slow dolly/handheld = reject |
| 2 | **中近景 medium-close shot**: chest-to-waist up, one person | Full body = face too small; close-up = no body motion |
| 3 | **Face clear and visible**, mostly frontal | No sunglasses, masks, hands covering the face for long |
| 4 | **Body and hand movement**, not only facial expression | Gesturing, stretching, waving, turning. A static pose or head-only motion = reject |
| 5 | **Empty hands, no physics-sensitive props** | Sand, water, drinks, food, paper, phone, books react to rain/wind and make generation hard. Gloves/clothes are fine |
| 6 | **Background readable, not heavily blurred**, few elements | Over-blurred bokeh hides the effect (snow cover, wet ground). Busy crowds/cars = reject |
| 7 | **No second person**, no other hands entering the frame | |
| 8 | P1: **outdoor**; P2: indoor or outdoor | Rain/snow/wind only make sense outside |
| 9 | ≥ 1920×1080, landscape, a continuous 5–8 s segment with **no cut** | Note where cuts or framing changes happen |
| 10 | Adults only | Skip anything that looks like a minor |

Nice to have: some visible hair (for wind), visible ground or sky (for snow/rain), even daylight.

## 2. Where to search

| Site | Notes |
|---|---|
| **Pexels** (pexels.com/videos) | Largest library, free license, no attribution. Direct original-file link: `https://www.pexels.com/download/video/<id>/`. Search filters: orientation, duration, resolution |
| **Pixabay** (pixabay.com/videos) | Large, free license, good 4K |
| **Mixkit** (mixkit.co) | Curated, high quality, smaller library; many talking-to-camera clips are indoor |
| **Coverr** (coverr.co) | Free, simple license, more lifestyle/b-roll |
| Videvo / Vecteezy / Videezy | Mixed free + paid; some clips need attribution — check each clip page |
| Paid (Shutterstock, Adobe Stock, Pond5, Storyblocks, Artgrid) | Use when formal delivery needs **model releases**. Free sites generally don't provide signed model releases |

Licensing: free-site clips are for **internal reference / trial production** unless the client
accepts them. Before any formal delivery, check the site's current license for AI/ML-training use
and model releases.

Search-term bank (landscape filter on): `man explaining with hands outdoors`,
`woman talking to camera outdoors`, `stretching arms outdoors front view`, `man warming up in park`,
`woman waving at camera outdoors`, `person gesturing outdoors medium shot`, `portrait in park looking at camera`.
Add `static`/`tripod` if the site supports it; prefer clips 8–20 s long (more room to pick a fixed segment).

## 3. Workflow

1. **Restate the brief** in one line (effect type, indoor/outdoor, how many clips).
2. **Search** 2–4 queries per site. Build a thumbnail grid with IDs (browser helper `__grid()`), pick
   5–10 candidates that pass requirements 2, 5, 7, 8 at a glance.
3. **Frame-check each candidate**: load the original file in a `<video>` element and draw 6 frames
   (3 %, 20 %, 40 %, 60 %, 80 %, 97 %) into one sheet (`__ovs(id)`). Read off duration and resolution.
   - Fixed camera? Compare one background landmark across all 6 frames.
   - Movement? Hands/arms must change position between frames.
   - Props, second person, face blocked, cuts?
4. **Pick 2 (or as asked)** and find a usable fixed segment (e.g. "4–12 s").
5. **Reply** with a table per clip: ID, what's in frame, resolution + length, motion, background,
   suggested trim, caveats; then the download links and page links; then one line per rejected clip
   with the reason (camera moves / second person / props / head-only motion…).

## 4. Browser notes

- Helpers are in `scripts/pexels_helpers.js` — paste into the page with the browser JS tool after
  each navigation (page reloads wipe them).
- If screenshots stop refreshing (browser pane hidden/covered), use `__sheetDownload(id)`: it saves
  the frame sheet as `~/Downloads/__cs_<id>.jpg`; stage it and view it. Tell the user why images are
  appearing, and move them to `Downloads/_to_delete/` when done.
- Pexels shows a Cloudflare check on bare-ID pages (`/video/<id>/`). Never try to solve or bypass it;
  use the slug URL from the search page, wait, or ask the user to pass it.
- Decline non-essential cookies on consent banners.
- Don't download the clips themselves unless the user asks; give links.
