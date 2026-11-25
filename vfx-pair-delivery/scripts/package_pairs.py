#!/usr/bin/env python3
"""
Build delivery packages for "source video -> edited target video" training pairs.

For each pair it writes, into <out>/<pair_id>/:
  <pair_id>_source.mp4, <pair_id>_target.mp4   (byte-identical copies, renamed)
  instruction.txt   line 1 = English instruction, line 2 = Chinese instruction
  qa.csv            video parameters + automatic checks + human self-check + verdict
  manifest.jsonl    one JSON line describing the pair
  sha256.txt        SHA-256 of the other five files ("<hash>  <name>")
plus batch files in <out>/: qa_all.csv, manifest_all.jsonl, report.md

Usage:
  python3 package_pairs.py pairs.json --out ./delivery [--config config.json]

Requires ffmpeg/ffprobe on PATH, Python 3.9+, numpy, opencv-python.
See ../SKILL.md for the pairs.json schema.
"""
import argparse, csv, hashlib, io, json, math, os, re, shutil, subprocess, sys
from pathlib import Path

import numpy as np
try:
    import cv2
except ImportError:  # face ratio + SSIM blur need cv2
    cv2 = None

DEFAULT_CONFIG = {
    "min_width": 1280, "min_height": 720,
    "min_bitrate_mbps_1080p": 20.0, "min_bitrate_mbps_720p": 10.0,
    "allowed_codecs": ["h264", "hevc"],
    "allowed_pix_fmts": ["yuv420p"],
    # tolerance agreed with the client lead: small fps / frame / duration gaps are a warning, not a rejection
    "time_tolerance_s": 1.0,
    "max_instruction_words_en": 60, "max_instruction_chars_zh": 60,
    # unedited-region consistency (brief: MAD <= 2/255, SSIM >= .98, to be calibrated on the trial batch)
    "preserved_mad_max": 2.0, "preserved_ssim_min": 0.98,
    "roi_diff_threshold": 18.0,      # per-pixel mean abs diff (0-255) that marks the edited region
    "roi_margin": 0.03,              # bbox padding as a fraction of width/height
    "analysis_width": 480, "analysis_frames": 24,
    "reject_on_bitrate": False,      # bitrate shortfall -> warn only
    "reject_on_audio": False,        # audio track -> warn only
    "res_tolerance": 0.01,
    # full-frame effects (weather, relit sky...): the unedited-region check does not apply
    "global_subtasks": ["snow", "rain", "wind", "fog", "storm", "sandstorm", "hail"],
    "global_edit_area": 0.6,         # auto-detected edited area above this -> treat as full-frame effect           # source/target size differing by <=1% (e.g. 2050 vs 2052) -> warn, re-export suggested
}


# ---------------------------------------------------------------- helpers
def run(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def probe(path):
    j = json.loads(run(["ffprobe", "-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", str(path)]))
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    audio = [s for s in j["streams"] if s["codec_type"] == "audio"]
    num, den = (int(x) for x in v["avg_frame_rate"].split("/"))
    rnum, rden = (int(x) for x in v["r_frame_rate"].split("/"))
    fps = num / den if den else 0.0
    rfps = rnum / rden if rden else 0.0
    dur = float(v.get("duration") or j["format"]["duration"])
    frames = int(v.get("nb_read_frames") or v.get("nb_frames") or round(dur * fps))
    br = v.get("bit_rate") or j["format"].get("bit_rate")
    w, h = int(v["width"]), int(v["height"])
    return {
        "codec": v["codec_name"], "pix_fmt": v.get("pix_fmt"), "width": w, "height": h,
        "fps": round(fps, 3), "r_fps": round(rfps, 3), "cfr": abs(fps - rfps) < 0.01,
        "frames": frames, "duration_s": round(dur, 3),
        "bitrate_mbps": round(int(br) / 1e6, 2) if br else None,
        "audio_tracks": len(audio), "container": j["format"]["format_name"],
        "orientation": "landscape" if w >= h else "portrait",
    }


def read_frames(path, times, width):
    """Decode frames at given timestamps, scaled to `width` (keeps aspect), RGB uint8."""
    out = []
    for t in times:
        raw = subprocess.run(
            ["ffmpeg", "-v", "error", "-ss", f"{t:.4f}", "-i", str(path), "-frames:v", "1",
             "-vf", f"scale={width}:-2:flags=area", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
            check=True, capture_output=True).stdout
        out.append(raw)
    return out


def frames_to_arrays(raws, w, h):
    return [np.frombuffer(r, np.uint8).reshape(h, w, 3).astype(np.float32) for r in raws if len(r) == w * h * 3]


def ssim_gray(a, b, mask):
    """Mean SSIM of grayscale a,b over pixels where mask is True."""
    a = a.mean(axis=2); b = b.mean(axis=2)
    if cv2 is None:
        return None
    C1, C2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    blur = lambda x: cv2.GaussianBlur(x, (11, 11), 1.5)
    mu_a, mu_b = blur(a), blur(b)
    s_a = blur(a * a) - mu_a ** 2; s_b = blur(b * b) - mu_b ** 2; s_ab = blur(a * b) - mu_a * mu_b
    m = ((2 * mu_a * mu_b + C1) * (2 * s_ab + C2)) / ((mu_a ** 2 + mu_b ** 2 + C1) * (s_a + s_b + C2))
    return float(m[mask].mean()) if mask.any() else None


def analyse(src, tgt, sp, tp, cfg):
    """Estimate edited ROI and unedited-region consistency, matching frames by timestamp."""
    W = cfg["analysis_width"]
    H = int(round(W * sp["height"] / sp["width"] / 2) * 2)
    dur = min(sp["duration_s"], tp["duration_s"])
    n = cfg["analysis_frames"]
    times = [dur * (i + 0.5) / n for i in range(n)]
    # target is scaled to the source geometry so a resolution mismatch does not break the comparison
    a_raw = read_frames(src, times, W)
    b_raw = []
    for t in times:
        b_raw.append(subprocess.run(
            ["ffmpeg", "-v", "error", "-ss", f"{t:.4f}", "-i", str(tgt), "-frames:v", "1",
             "-vf", f"scale={W}:{H}:flags=area", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
            check=True, capture_output=True).stdout)
    A = frames_to_arrays(a_raw, W, H); B = frames_to_arrays(b_raw, W, H)
    k = min(len(A), len(B))
    if k == 0:
        return {"roi_bbox": None, "mad_outside": None, "ssim_outside": None, "edited_area": None}
    diffs = [np.abs(A[i] - B[i]).mean(axis=2) for i in range(k)]
    mean_diff = np.mean(diffs, axis=0)
    hot = mean_diff > cfg["roi_diff_threshold"]
    if cv2 is not None:
        hot = cv2.morphologyEx(hot.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)).astype(bool)
    if hot.any():
        ys, xs = np.where(hot)
        mx, my = cfg["roi_margin"] * W, cfg["roi_margin"] * H
        x0, x1 = max(0, xs.min() - mx), min(W, xs.max() + 1 + mx)
        y0, y1 = max(0, ys.min() - my), min(H, ys.max() + 1 + my)
        bbox = [round(float(x0) / W, 3), round(float(y0) / H, 3), round(float(x1) / W, 3), round(float(y1) / H, 3)]
        outside = np.ones((H, W), bool); outside[int(y0):int(math.ceil(y1)), int(x0):int(math.ceil(x1))] = False
    else:
        bbox = None; outside = np.ones((H, W), bool)
    mads = [float(d[outside].mean()) for d in diffs if outside.any()]
    ssims = [ssim_gray(A[i], B[i], outside) for i in range(k)]
    ssims = [s for s in ssims if s is not None]
    return {
        "roi_bbox": bbox,
        "edited_area": round(float(hot.mean()), 3),
        "mad_outside": round(float(np.mean(mads)), 2) if mads else None,
        "ssim_outside": round(float(np.mean(ssims)), 4) if ssims else None,
    }


def face_ratio(src, sp):
    if cv2 is None:
        return None
    raw = read_frames(src, [sp["duration_s"] / 2], 640)[0]
    h = int(len(raw) / (640 * 3))
    img = np.frombuffer(raw, np.uint8).reshape(h, 640, 3)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    path = os.path.join(getattr(getattr(cv2, "data", None), "haarcascades", ""), "haarcascade_frontalface_default.xml")
    if not os.path.exists(path):
        return None        # no face model available -> fill face_h_ratio by hand in pairs.json
    casc = cv2.CascadeClassifier(path)
    if casc.empty():
        return None
    faces = casc.detectMultiScale(gray, 1.1, 5, minSize=(12, 12))
    if len(faces) == 0:
        return None
    return round(max(f[3] for f in faces) / h, 2)


def count_en_words(s):
    return len(re.findall(r"[A-Za-z0-9'’\-]+", s or ""))


def count_zh_chars(s):
    return len(re.findall(r"[一-鿿]", s or ""))


def tf(x):
    if x == "na":
        return "N/A"
    if x is None:
        return ""          # not checked yet -> leave blank rather than claim FALSE
    return "TRUE" if x else "FALSE"


# ---------------------------------------------------------------- core
def check_pair(p, sp, tp, ana, cfg):
    issues, warns = [], []
    # format
    fmt = "pass"
    for tag, q in (("source", sp), ("target", tp)):
        if "mp4" not in q["container"]:
            fmt = "fail"; issues.append(f"{tag} 不是 mp4")
        if q["codec"] not in cfg["allowed_codecs"]:
            fmt = "fail"; issues.append(f"{tag} 编码 {q['codec']} 不在允许范围")
        if q["pix_fmt"] not in cfg["allowed_pix_fmts"]:
            fmt = "warn" if fmt == "pass" else fmt; warns.append(f"{tag} 像素格式 {q['pix_fmt']}")
        if q["width"] < cfg["min_width"] or q["height"] < cfg["min_height"]:
            fmt = "fail"; issues.append(f"{tag} 分辨率 {q['width']}×{q['height']} 低于最低 {cfg['min_width']}×{cfg['min_height']}")
        if q["audio_tracks"]:
            if cfg["reject_on_audio"]:
                fmt = "fail"; issues.append(f"{tag} 含音轨")
            else:
                fmt = "warn" if fmt == "pass" else fmt; warns.append(f"{tag} 含音轨（建议去除）")
        if not q["cfr"]:
            fmt = "warn" if fmt == "pass" else fmt; warns.append(f"{tag} 非恒定帧率（VFR）")
    if (sp["width"], sp["height"]) != (tp["width"], tp["height"]):
        rel = max(abs(sp["width"] - tp["width"]) / sp["width"], abs(sp["height"] - tp["height"]) / sp["height"])
        if rel <= cfg["res_tolerance"]:
            fmt = "warn" if fmt == "pass" else fmt
            warns.append(f"源/目标分辨率有细微差异（{sp['width']}×{sp['height']} vs {tp['width']}×{tp['height']}），建议导出时对齐")
        else:
          fmt = "fail"; issues.append(f"源/目标分辨率不一致（{sp['width']}×{sp['height']} vs {tp['width']}×{tp['height']}）")
    if abs(sp["width"] / sp["height"] - 16 / 9) > 0.02 and sp["orientation"] == "landscape":
        warns.append(f"源画幅非 16:9（{sp['width']}×{sp['height']}）")
    # fps & time (tolerant)
    dt = abs(sp["duration_s"] - tp["duration_s"])
    exact = sp["fps"] == tp["fps"] and sp["frames"] == tp["frames"]
    if exact and dt < 1 / max(sp["fps"], 1):
        ft = "pass"
    elif dt <= cfg["time_tolerance_s"]:
        ft = "warn"; warns.append(f"帧率/帧数/时长有差异但在容差内（{sp['fps']}fps/{sp['frames']}帧/{sp['duration_s']}s vs {tp['fps']}fps/{tp['frames']}帧/{tp['duration_s']}s）")
    else:
        ft = "fail"; issues.append(f"时长差 {dt:.2f}s 超出容差 {cfg['time_tolerance_s']}s")
    aligned = exact and (sp["width"], sp["height"]) == (tp["width"], tp["height"]) and dt < 1 / max(sp["fps"], 1)
    # bitrate
    br = "pass"
    for tag, q in (("source", sp), ("target", tp)):
        need = cfg["min_bitrate_mbps_1080p"] if q["height"] >= 1080 else cfg["min_bitrate_mbps_720p"]
        if q["bitrate_mbps"] is not None and q["bitrate_mbps"] < need:
            if cfg["reject_on_bitrate"]:
                br = "fail"; issues.append(f"{tag} 码率 {q['bitrate_mbps']}Mbps < {need}")
            else:
                br = "warn"; warns.append(f"{tag} 码率 {q['bitrate_mbps']}Mbps 低于要求 {need}Mbps")
    # instruction
    ew, zc = count_en_words(p["instruction_en"]), count_zh_chars(p["instruction_zh"])
    if ew == 0 or zc == 0:
        issues.append("缺少中文或英文指令")
    if ew > cfg["max_instruction_words_en"]:
        issues.append(f"英文指令 {ew} 词 > {cfg['max_instruction_words_en']}")
    if zc > cfg["max_instruction_chars_zh"]:
        issues.append(f"中文指令 {zc} 字 > {cfg['max_instruction_chars_zh']}")
    # unedited region
    pres = None
    is_global = p.get("subtask") in cfg["global_subtasks"] or (ana["edited_area"] or 0) >= cfg["global_edit_area"]
    if is_global:
        pres = "na"
        warns.append("全画面特效（天气/整体光线变化），非特效区一致性不适用，以人工目检为准")
    elif ana["mad_outside"] is not None:
        pres = ana["mad_outside"] <= cfg["preserved_mad_max"] and (ana["ssim_outside"] is None or ana["ssim_outside"] >= cfg["preserved_ssim_min"])
        if not pres:
            warns.append(f"非特效区差异 MAD {ana['mad_outside']}/255、SSIM {ana['ssim_outside']}（要求 ≤{cfg['preserved_mad_max']}、≥{cfg['preserved_ssim_min']}，试标校准）")
    human = p.get("self_check", {})
    edit_ok, identity_ok, temporal_ok = human.get("edit_ok"), human.get("identity_ok"), human.get("temporal_ok")
    for k, v in (("特效合格 edit_ok", edit_ok), ("人物一致 identity_ok", identity_ok), ("时序连贯 temporal_ok", temporal_ok)):
        if v is False:
            issues.append(f"人工自检未通过：{k}")
        if v is None:
            warns.append(f"人工自检未填写：{k}")
    for n in p.get("review_notes", []) or []:
        warns.append(n)            # reviewer remarks: shown to the client, never change the verdict
    verdict = "reject" if (issues or "fail" in (fmt, ft, br)) else "pass"
    return {
        "format": fmt, "fps_and_time": ft, "bitrate": br, "aligned": aligned,
        "edit_ok": edit_ok, "identity_ok": identity_ok, "preserved_ok": pres, "temporal_ok": temporal_ok,
        "verdict": verdict, "issues": issues, "warnings": warns, "instruction_words": ew, "instruction_zh_chars": zc,
    }


QA_COLS = ["pair_id", "task", "subtask", "source", "target", "width", "height", "fps", "frames", "duration_s",
           "orientation", "instruction_words", "format", "fps_and_time", "bitrate", "aligned", "edit_ok",
           "identity_ok", "preserved_ok", "temporal_ok", "verdict"]


def build(p, out_root, cfg):
    pid = p["pair_id"]
    d = Path(out_root) / pid
    d.mkdir(parents=True, exist_ok=True)
    src_name, tgt_name = f"{pid}_source.mp4", f"{pid}_target.mp4"
    shutil.copyfile(p["source_path"], d / src_name)
    shutil.copyfile(p["target_path"], d / tgt_name)
    sp, tp = probe(d / src_name), probe(d / tgt_name)
    ana = analyse(d / src_name, d / tgt_name, sp, tp, cfg)
    chk = check_pair(p, sp, tp, ana, cfg)

    (d / "instruction.txt").write_text(p["instruction_en"].strip() + "\n" + p["instruction_zh"].strip() + "\n", encoding="utf-8")

    row = {"pair_id": pid, "task": p["task"], "subtask": p["subtask"], "source": src_name, "target": tgt_name,
           "width": tp["width"], "height": tp["height"], "fps": tp["fps"], "frames": tp["frames"],
           "duration_s": tp["duration_s"], "orientation": tp["orientation"], "instruction_words": chk["instruction_words"],
           "format": chk["format"], "fps_and_time": chk["fps_and_time"], "bitrate": chk["bitrate"],
           "aligned": tf(chk["aligned"]), "edit_ok": tf(chk["edit_ok"]), "identity_ok": tf(chk["identity_ok"]),
           "preserved_ok": tf(chk["preserved_ok"]), "temporal_ok": tf(chk["temporal_ok"]), "verdict": chk["verdict"]}
    with open(d / "qa.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=QA_COLS); w.writeheader(); w.writerow(row)

    sh_src, sh_tgt = sha256(d / src_name), sha256(d / tgt_name)
    manifest = {
        "pair_id": pid, "task": p["task"], "subtask": p["subtask"],
        "instruction_en": p["instruction_en"].strip(), "instruction_zh": p["instruction_zh"].strip(),
        "source": src_name, "target": tgt_name, "ref": p.get("ref"), "mask": p.get("mask"),
        "width": tp["width"], "height": tp["height"], "fps": tp["fps"], "frames": tp["frames"],
        "duration_s": tp["duration_s"], "orientation": tp["orientation"],
        "source_params": {k: sp[k] for k in ("width", "height", "fps", "frames", "duration_s", "codec", "bitrate_mbps")},
        "framing": p.get("framing"), "face_h_ratio": p.get("face_h_ratio", face_ratio(d / src_name, sp)),
        "performer_id": p.get("performer_id"), "scene_id": p.get("scene_id"),
        "camera": p.get("camera", "static"),
        "method": p.get("method", {"source": "real_footage", "target": "model_generated"}),
        "tools": p.get("tools", {"source": None, "target": None}),
        "roi": {"region": p.get("roi_region"), "bbox_xyxy_normalized": p.get("roi_bbox") or ana["roi_bbox"],
                "edited_area_ratio": ana["edited_area"]},
        "license_id": p.get("license_id"), "performer_release": p.get("performer_release"),
        "qa": {"aligned": chk["aligned"], "edit_ok": chk["edit_ok"], "identity_ok": chk["identity_ok"],
               "preserved_ok": None if chk["preserved_ok"] == "na" else chk["preserved_ok"],
               "preserved_check": "not_applicable_full_frame_effect" if chk["preserved_ok"] == "na" else "outside_roi",
               "temporal_ok": chk["temporal_ok"],
               "unedited_mad": ana["mad_outside"], "unedited_ssim": ana["ssim_outside"],
               "reviewer": p.get("reviewer"), "notes": "；".join(chk["issues"] + chk["warnings"])},
        "sha256": {"source": sh_src, "target": sh_tgt},
        "gen_prompt": {"source": p.get("gen_prompt_source")},
    }
    (d / "manifest.jsonl").write_text(json.dumps(manifest, ensure_ascii=False) + "\n", encoding="utf-8")

    names = ["manifest.jsonl", "qa.csv", src_name, tgt_name, "instruction.txt"]
    (d / "sha256.txt").write_text("".join(f"{sha256(d / n)}  {n}\n" for n in names), encoding="utf-8")
    return row, manifest, chk, sp, tp, ana


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pairs"); ap.add_argument("--out", required=True); ap.add_argument("--config")
    a = ap.parse_args()
    cfg = dict(DEFAULT_CONFIG)
    if a.config:
        cfg.update(json.loads(Path(a.config).read_text(encoding="utf-8")))
    pairs = json.loads(Path(a.pairs).read_text(encoding="utf-8"))
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    rows, mans, report = [], [], ["# 交付包检查报告\n"]
    for p in pairs:
        row, man, chk, sp, tp, ana = build(p, out, cfg)
        rows.append(row); mans.append(man)
        report.append(f"## {p['pair_id']} — {chk['verdict']}\n")
        report.append(f"- 源：{sp['width']}×{sp['height']} {sp['fps']}fps {sp['frames']}帧 {sp['duration_s']}s {sp['codec']} {sp['bitrate_mbps']}Mbps 音轨{sp['audio_tracks']}")
        report.append(f"- 目标：{tp['width']}×{tp['height']} {tp['fps']}fps {tp['frames']}帧 {tp['duration_s']}s {tp['codec']} {tp['bitrate_mbps']}Mbps 音轨{tp['audio_tracks']}")
        report.append(f"- 检查：format={chk['format']} fps_and_time={chk['fps_and_time']} bitrate={chk['bitrate']} aligned={chk['aligned']} preserved={chk['preserved_ok']}（MAD {ana['mad_outside']}，SSIM {ana['ssim_outside']}，ROI {ana['roi_bbox']}）")
        for x in chk["issues"]:
            report.append(f"- ❌ {x}")
        for x in chk["warnings"]:
            report.append(f"- ⚠️ {x}")
        report.append("")
    with open(out / "qa_all.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=QA_COLS); w.writeheader(); w.writerows(rows)
    (out / "manifest_all.jsonl").write_text("".join(json.dumps(m, ensure_ascii=False) + "\n" for m in mans), encoding="utf-8")
    (out / "report.md").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
