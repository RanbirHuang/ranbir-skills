---
name: vfx-pair-delivery
description: Review "source video → VFX target video" training pairs and build their delivery package (instruction.txt, qa.csv, manifest.jsonl, sha256.txt) with automatic spec checks. Use for video-effect / video-editing dataset delivery, 视频特效交付, 试标审核, or when someone asks to generate the non-video delivery files for a pair.
---

# VFX pair delivery (视频特效训练数据交付)

Turns finished pairs (a real-shot **source** video + an effect-added **target** video) into a
client-ready delivery package, and produces the review numbers needed to accept or send back a pair.

Built for the Baidu 众测「实拍视频采集 + 特效制作」project, but every threshold lives in a config,
so it works for any "instruction-guided video editing" dataset with the same layout.

## What one pair delivers

```
<pair_id>/
  <pair_id>_source.mp4     original clip (renamed copy, bytes untouched)
  <pair_id>_target.mp4     clip with the effect (renamed copy)
  instruction.txt          line 1 English (≤60 words), line 2 Chinese (≤60 chars)
  qa.csv                   one row: params + automatic checks + human checks + verdict
  manifest.jsonl           one JSON line: task, instructions, params, ROI, method, QA, hashes
  sha256.txt               "<sha256>  <file>" for manifest.jsonl, qa.csv, both videos, instruction.txt
```
Batch files at the package root: `qa_all.csv`, `manifest_all.jsonl`, `report.md` (检查报告).

## Workflow

1. **Collect the pairs** from the tracking table (e.g. a Feishu base). For each pair you need:
   Pair_ID, task (P1 background_physical_interaction / P2 local_effect), subtask, the two video
   files, a short EN + ZH delivery instruction, framing, ROI region name, and the human self-check
   (edit_ok / identity_ok / temporal_ok). The table is the single source of truth.
2. **Decide which file is which by content, not by file name.** Look at a frame of each: the one
   without the effect is the source. File names in trackers are often swapped.
3. **Write the delivery instruction** — not the long generation prompt. Pattern:
   *what changes* + *how it behaves over time* + "Keep <face, clothing, motion, background,
   lighting, framing> unchanged." Count: EN ≤ 60 words, ZH ≤ 60 Chinese characters.
4. **Write `pairs.json`** (schema below) and run
   `python3 scripts/package_pairs.py pairs.json --out ./交付包 [--config config.json]`.
   Needs ffmpeg/ffprobe, numpy, opencv-python.
5. **Read `report.md`.** ❌ items make the verdict `reject`; ⚠️ items are warnings for the reviewer.
6. **Write results back to the table**: format fields (分辨率/帧率/帧数/时长/编码/码率),
   自检结论, 我方审核结果, 审核意见 (number the problems ①②③ and end with what is good),
   the short instructions, the package path, and upload the four files into their attachment fields.
7. **Verify**: run `sha256sum -c sha256.txt` inside each pair folder after copying to the final
   location. If you re-type any file content elsewhere (e.g. a browser upload), hash it and compare —
   note `qa.csv` is written with CRLF line endings by Python's csv module.

## pairs.json schema

```json
[{
  "pair_id": "P2-fire-000001",
  "task": "local_effect",
  "subtask": "hair_on_fire",
  "source_path": "/path/to/source.mp4",
  "target_path": "/path/to/target.mp4",
  "instruction_en": "Set her hair on fire: ... Keep her face, ... unchanged.",
  "instruction_zh": "让她头顶的头发燃起逼真的火焰……不变。",
  "framing": "medium",                     // close_up | medium | full_body
  "roi_region": "hair_head",               // free text, the edited area
  "face_h_ratio": 0.15,                    // optional; auto-detected if OpenCV face model exists
  "camera": "static",
  "method": {"source": "real_footage", "target": "model_generated"},
  "tools":  {"source": "phone", "target": "tool name"},
  "performer_id": null, "scene_id": null, "license_id": null, "performer_release": false,
  "reviewer": "who checked it",
  "self_check": {"edit_ok": true, "identity_ok": true, "temporal_ok": true},
  "gen_prompt_source": "optional prompt used to generate/shoot the source"
}]
```

## Automatic checks (defaults in `DEFAULT_CONFIG`)

| Check | Rule | Result |
|---|---|---|
| Container / codec | mp4, h264 or hevc | fail otherwise |
| Resolution | ≥ 1280×720 | fail |
| Source vs target size | identical; ≤1% difference (e.g. 2050 vs 2052) | fail / warn |
| fps, frame count, duration | identical = pass; duration gap ≤ `time_tolerance_s` (1 s) = **warn, not reject** | fail only beyond tolerance |
| Bitrate | ≥ 20 Mbps at 1080p, ≥ 10 Mbps at 720p | warn (set `reject_on_bitrate` to fail) |
| Audio track | should be absent | warn (set `reject_on_audio` to fail) |
| VFR, non-16:9 | — | warn |
| Instruction length | EN ≤ 60 words, ZH ≤ 60 chars, both present | fail |
| Unedited region | target scaled to source size, frames matched by timestamp; edited ROI = pixels whose mean diff > 18/255; outside ROI MAD ≤ 2/255 and SSIM ≥ 0.98 | warn (thresholds to be calibrated on the trial batch) |
| Human self-check | edit_ok / identity_ok / temporal_ok | False = fail, missing = warn |

The tolerance on fps/frames/duration is deliberate: the project lead accepts small timing
differences from generation tools. Resolution below the minimum or a large size mismatch is
still a rejection — ask for a re-export at the source resolution.

## Review-comment template (审核意见)

```
需返工 / 通过（附提示）：①<最重要的问题，附数值>；②…；③…。<特效效果评价>，人物一致。
```

## Feishu base tips (if the tracker is a Feishu/Lark base)

- One row per pair. Keep attachment fields for 源视频, 目标视频, instruction.txt, qa.csv,
  manifest.jsonl, 哈希密钥（sha256.txt）, plus text fields 交付指令（英/中） and 交付包路径.
- Add a grid view 「交付文件」 that shows only Pair_ID, 大类, 特效类型, the six files,
  the two instructions, 自检结论, 制作状态, 我方审核结果, 交付包路径.
- Bulk-fill with a TSV paste starting from a select-type cell; text cells take a single-cell paste.
